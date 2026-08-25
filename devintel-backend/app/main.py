import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException, app_exception_handler, unhandled_exception_handler, validation_exception_handler
from app.middleware.metrics import PrometheusMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import (
    AuditLoggingMiddleware,
    RequestIDMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
)

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Verify database connectivity on startup.

    Schema management is handled entirely by Alembic (run in start.sh
    before uvicorn).  We only verify connectivity here — never call
    create_all, because the asyncpg dialect does not reliably support
    ``CREATE TABLE IF NOT EXISTS`` via checkfirst introspection and
    will crash with DuplicateTableError.
    """
    from app.core.logging import setup_logging
    from app.core.telemetry import init_telemetry
    from app.db.session import engine

    # Initialize structured logging
    setup_logging()

    # Initialize OpenTelemetry (no-op if OTEL_ENABLED != true)
    init_telemetry(app)

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connectivity verified.")
    except Exception as exc:
        logger.error("Database startup check failed: %s", exc)
        raise

    # Start the durable job poller
    from app.services.job_poller import start_poller, stop_poller
    poller_tasks, poller_stop_event = await start_poller()

    yield

    # --- Shutdown ---
    # Stop job poller (give in-flight jobs up to 10s to finish)
    await stop_poller(poller_tasks, poller_stop_event)

    from app.core.http_pool import close_http_client
    from app.services.cache import cache
    logger.info("Shutting down: closing connections...")
    await close_http_client()
    await cache.close()
    await engine.dispose()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )


    # ── Security middleware ────────────────────────────────────────────────
    # NOTE: add_middleware uses a stack — the LAST middleware added wraps
    # everything and runs FIRST.  We add CORS *after* all other middleware
    # so it is the outermost layer and always injects CORS headers, even
    # when an inner middleware returns an error response.
    # Request ID tracing — adds X-Request-ID to every request/response
    app.add_middleware(RequestIDMiddleware)
    # OWASP security headers (X-Content-Type-Options, X-Frame-Options, CSP, etc.)
    app.add_middleware(SecurityHeadersMiddleware)
    # Reject oversized request bodies (10 MB default) to prevent DoS
    app.add_middleware(RequestSizeLimitMiddleware)
    # Per-user rate limiting (Redis sliding window, fails open without Redis)
    app.add_middleware(RateLimitMiddleware, default_limit=settings.RATE_LIMIT_PER_MINUTE)
    # Audit logging for sensitive paths (/auth, /repos, /admin)
    app.add_middleware(AuditLoggingMiddleware)
    # Prometheus HTTP metrics (request count, duration, in-progress)
    app.add_middleware(PrometheusMiddleware)

    # ── CORS (must be outermost = added LAST) ─────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # ── Routes ────────────────────────────────────────────────────────────
    app.include_router(api_router)

    @app.get("/health")
    async def health():
        import time
        return {
            "status": "ok",
            "app": settings.APP_NAME,
            "version": "1.0.0",
            "environment": "production" if not settings.DEBUG else "development",
            "timestamp": time.time(),
        }

    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from fastapi.responses import Response
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    logger.info("%s started. Debug=%s", settings.APP_NAME, settings.DEBUG)
    return app


app = create_app()

