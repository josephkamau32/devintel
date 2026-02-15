"""CSRF protection middleware."""

import secrets
from typing import Callable

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware for state-changing operations.
    
    Protects POST, PUT, PATCH, DELETE requests by validating CSRF tokens.
    GET, HEAD, OPTIONS requests are exempt.
    """
    
    # HTTP methods that require CSRF protection
    PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    
    # Paths exempt from CSRF protection
    EXEMPT_PATHS = {
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/github",
        "/api/v1/auth/github/callback",  # OAuth callbacks need to be exempt
    }
    
    def __init__(self, app, secret_key: str):
        """
        Initialize CSRF middleware.
        
        Args:
            app: FastAPI application
            secret_key: Secret key for token generation
        """
        super().__init__(app)
        self.secret_key = secret_key
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with CSRF protection."""
        
        # Skip CSRF for safe methods
        if request.method not in self.PROTECTED_METHODS:
            response = await call_next(request)
            # Add CSRF token to response for client
            if not hasattr(request.state, "csrf_token"):
                csrf_token = self._generate_csrf_token()
                response.set_cookie(
                    key="csrf_token",
                    value=csrf_token,
                    httponly=False,  # Needs to be accessible by JavaScript
                    secure=True,  # HTTPS only in production
                    samesite="strict",
                )
            return response
        
        # Skip CSRF for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)
        
        # Validate CSRF token for protected methods
        csrf_cookie = request.cookies.get("csrf_token")
        csrf_header = request.headers.get("X-CSRF-Token")
        
        if not csrf_cookie or not csrf_header:
            logger.warning(
                f"Missing CSRF token",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "ip": request.client.host if request.client else "unknown",
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing",
            )
        
        if not secrets.compare_digest(csrf_cookie, csrf_header):
            logger.warning(
                f"Invalid CSRF token",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "ip": request.client.host if request.client else "unknown",
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token invalid",
            )
        
        # Token valid, proceed with request
        return await call_next(request)
    
    def _generate_csrf_token(self) -> str:
        """Generate a random CSRF token."""
        return secrets.token_urlsafe(32)
