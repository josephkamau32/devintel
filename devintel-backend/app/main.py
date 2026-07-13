import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.core.exceptions import AppException, app_exception_handler, validation_exception_handler
from app.api.v1.router import api_router
from app.middleware.security import (
    SecurityHeadersMiddleware,
    RequestIDMiddleware,
    RequestSizeLimitMiddleware,
    AuditLoggingMiddleware,
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

    # ── CORS ──────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Security middleware (order matters: outermost runs first) ──────────
    # Request ID tracing — adds X-Request-ID to every request/response
    app.add_middleware(RequestIDMiddleware)
    # OWASP security headers (X-Content-Type-Options, X-Frame-Options, CSP, etc.)
    app.add_middleware(SecurityHeadersMiddleware)
    # Reject oversized request bodies (10 MB default) to prevent DoS
    app.add_middleware(RequestSizeLimitMiddleware)
    # Audit logging for sensitive paths (/auth, /repos, /admin)
    app.add_middleware(AuditLoggingMiddleware)

    # ── Exception handlers ────────────────────────────────────────────────
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # ── Routes ────────────────────────────────────────────────────────────
    app.include_router(api_router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "app": settings.APP_NAME}

    logger.info("%s started. Debug=%s", settings.APP_NAME, settings.DEBUG)
    return app


app = create_app()
