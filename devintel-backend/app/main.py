"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1 import (
    analytics,
    auth,
    chat,
    health_score,
    organizations,
    pr_review,
    repositories,
    webhooks,
    ws,
)
from app.core.config import settings
from app.core.exceptions import DevIntelException
from app.core.logging import get_logger, setup_logging
from app.middleware.csrf import CSRFMiddleware
from app.middleware.security import (
    AuditLoggingMiddleware,
    RequestIDMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
    SQLInjectionDetectionMiddleware,
)

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting DevIntel AI backend")
    yield
    logger.info("Shutting down DevIntel AI backend")

    # Graceful shutdown: Close cache (Redis or in-memory)
    from app.services.cache import cache
    try:
        await cache.close()
    except Exception as e:
        logger.error(f"Error closing cache: {e}")

    # Graceful shutdown: Dispose SQLAlchemy engine
    from app.db.session import engine
    try:
        await engine.dispose()
    except Exception as e:
        logger.error(f"Error disposing database engine: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered developer productivity platform with RAG",
    version="1.0.0",
    lifespan=lifespan,
    # Hide API docs in production for security
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware (must be first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security middleware (in order of execution)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware, secret_key=settings.secret_key)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestSizeLimitMiddleware, max_size=10 * 1024 * 1024)
app.add_middleware(AuditLoggingMiddleware)
app.add_middleware(SQLInjectionDetectionMiddleware, block_on_detection=True)


# Exception handlers
@app.exception_handler(DevIntelException)
async def devintel_exception_handler(request: Request, exc: DevIntelException):
    """Handle custom DevIntel exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with CORS headers so the browser can read the error."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    origin = request.headers.get("origin", "")
    headers = {}
    if origin and origin in settings.cors_origins:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Internal server error", "detail": str(exc)},
        headers=headers,
    )


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "devintel-ai"}


# Include routers
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(repositories.router, prefix=settings.api_v1_prefix)
app.include_router(chat.router, prefix=settings.api_v1_prefix)
app.include_router(pr_review.router, prefix=settings.api_v1_prefix)
app.include_router(analytics.router, prefix=settings.api_v1_prefix)
app.include_router(
    organizations.router,
    prefix=f"{settings.api_v1_prefix}/organizations",
    tags=["organizations"],
)
app.include_router(webhooks.router, prefix=settings.api_v1_prefix)
app.include_router(health_score.router, prefix=settings.api_v1_prefix)
app.include_router(ws.router)  # WebSocket routes don't use the /api/v1 prefix


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to DevIntel AI",
        "docs": "/docs",
        "health": "/health",
    }
