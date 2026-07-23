import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException, app_exception_handler, unhandled_exception_handler, validation_exception_handler
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


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
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
        return {"status": "ok", "app": settings.APP_NAME}

    logger.info("%s started. Debug=%s", settings.APP_NAME, settings.DEBUG)
    return app


app = create_app()
