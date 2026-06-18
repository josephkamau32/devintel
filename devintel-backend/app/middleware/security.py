"""Security middleware for the application."""

import time
from collections.abc import Callable
from uuid import uuid4

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.

    Implements OWASP security best practices for HTTP headers.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        from app.core.config import settings

        self.security_headers = {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            # Enable XSS protection (legacy, but doesn't hurt)
            "X-XSS-Protection": "1; mode=block",
            # Content Security Policy (restrictive default)
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';",
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # Permissions policy
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

        # Only add HSTS in production (breaks HTTP localhost in dev)
        if settings.ENVIRONMENT == "production":
            self.security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Add all security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value

        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to each request for tracing.

    The request ID is:
    - Added to response headers
    - Added to log context
    - Used for distributed tracing
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID to request and response."""
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid4()))

        # Add to request state for access in routes
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Limit request body size to prevent DoS attacks.

    Default limit: 10MB
    """

    def __init__(self, app: ASGIApp, max_size: int = 10 * 1024 * 1024):
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check request size and reject if too large."""
        content_length = request.headers.get("content-length")

        if content_length and int(content_length) > self.max_size:
            logger.warning(
                f"Request size too large: {content_length} bytes",
                extra={"path": request.url.path},
            )
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "message": "Request body too large",
                    "max_size": self.max_size,
                },
            )

        return await call_next(request)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log sensitive operations for security auditing.

    Logs:
    - All authentication attempts
    - Repository modifications
    - User data access
    """

    SENSITIVE_PATHS = [
        "/api/v1/auth",
        "/api/v1/repos",
        "/api/v1/admin",
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log sensitive operations."""
        start_time = time.time()

        # Check if this is a sensitive path
        is_sensitive = any(
            request.url.path.startswith(path) for path in self.SENSITIVE_PATHS
        )

        if is_sensitive:
            # Log request
            logger.info(
                "Sensitive operation started",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                    "request_id": getattr(request.state, "request_id", "unknown"),
                },
            )

        # Process request
        response = await call_next(request)

        if is_sensitive:
            # Log response
            duration = time.time() - start_time
            logger.info(
                "Sensitive operation completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "request_id": getattr(request.state, "request_id", "unknown"),
                },
            )

        return response


class SQLInjectionDetectionMiddleware(BaseHTTPMiddleware):
    """Middleware to detect and block potential SQL injection attempts."""

    def __init__(self, app, block_on_detection: bool = True):
        """Initialize SQL injection detection middleware.

        Args:
            app: FastAPI application
            block_on_detection: If True, block requests with SQL injection patterns
        """
        super().__init__(app)
        self.block_on_detection = block_on_detection

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check request for SQL injection patterns and block if detected."""
        from app.core.validators import detect_sql_injection

        # Exempt chat and PR review paths — users naturally discuss SQL code
        # These endpoints have their own input validation (prompt injection defense, etc.)
        exempt_prefixes = ("/api/v1/chat", "/api/v1/pr-review")
        if any(request.url.path.startswith(p) for p in exempt_prefixes):
            return await call_next(request)

        # Check query parameters
        for key, value in request.query_params.items():
            try:
                detect_sql_injection(value, block=self.block_on_detection)
            except HTTPException as e:
                logger.warning(
                    f"Blocked SQL injection in query param: {key}",
                    extra={
                        "path": request.url.path,
                        "param": key,
                        "ip": request.client.host if request.client else "unknown",
                    },
                )
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail},
                )
            except Exception as e:
                logger.error(f"Unexpected error in SQL injection check: {e}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid input detected"},
                )

        # Check path parameters (from URL)
        try:
            detect_sql_injection(str(request.url.path), block=self.block_on_detection)
        except HTTPException as e:
            logger.warning(
                "Blocked SQL injection in path",
                extra={
                    "path": request.url.path,
                    "ip": request.client.host if request.client else "unknown",
                },
            )
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail},
            )
        except Exception as e:
            logger.error(f"Unexpected error in SQL injection path check: {e}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid input detected"},
            )

        return await call_next(request)
