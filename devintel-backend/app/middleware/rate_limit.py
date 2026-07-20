"""Rate limiting middleware using Redis sliding window counter.

Provides per-user rate limiting with configurable limits per endpoint group.
Falls back to allowing all requests when Redis is unavailable, so the
application degrades gracefully in environments without Redis (e.g., local dev).
"""

import time
from collections.abc import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger

logger = get_logger(__name__)


# Per-endpoint rate limits (requests per minute)
# More expensive endpoints get stricter limits
ENDPOINT_RATE_LIMITS: dict[str, int] = {
    "/api/v1/auth": 5,
    "/api/v1/chat": 20,
    "/api/v1/repos": 30,
    "/api/v1/health-score": 10,
    "/api/v1/pr-review": 10,
    "/api/v1/agent": 10,
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-user sliding window rate limiter backed by Redis.

    Uses a Redis sorted set per user+endpoint to implement a sliding
    window counter. Each request adds a timestamped entry; entries older
    than 60 seconds are pruned on each check.

    When Redis is unavailable, all requests are allowed (fail-open)
    to avoid breaking the application in environments without Redis.
    """

    def __init__(self, app: ASGIApp, default_limit: int = 100):
        super().__init__(app)
        self.default_limit = default_limit

    def _get_client_key(self, request: Request) -> str:
        """Build a rate-limit key from user identity or IP."""
        # Prefer authenticated user ID from JWT (set by auth middleware)
        user_id = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id

        # Fall back to client IP
        if not user_id:
            user_id = request.client.host if request.client else "anonymous"

        return str(user_id)

    def _get_rate_limit(self, path: str) -> int:
        """Get the rate limit for a given request path."""
        for prefix, limit in ENDPOINT_RATE_LIMITS.items():
            if path.startswith(prefix):
                return limit
        return self.default_limit

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit before processing request."""
        # Skip rate limiting for health checks and static assets
        if request.url.path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        # Skip non-API paths
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        client_key = self._get_client_key(request)
        rate_limit = self._get_rate_limit(request.url.path)
        window_key = f"ratelimit:{client_key}:{request.url.path.split('/')[3] if len(request.url.path.split('/')) > 3 else 'global'}"

        try:
            from app.core.redis_pool import RedisPool

            redis_client = await RedisPool.get_client()

            if redis_client is None:
                # No Redis available — fail open
                return await call_next(request)

            now = time.time()
            window_start = now - 60  # 60-second sliding window

            # Use a pipeline for atomic operations
            pipe = redis_client.pipeline()

            # Remove entries older than the window
            pipe.zremrangebyscore(window_key, 0, window_start)

            # Count current entries in the window
            pipe.zcard(window_key)

            # Add current request timestamp
            pipe.zadd(window_key, {str(now): now})

            # Set TTL on the key (auto-cleanup)
            pipe.expire(window_key, 120)

            results = await pipe.execute()
            current_count = results[1]  # zcard result

            if current_count >= rate_limit:
                # Calculate retry-after based on oldest entry in window
                logger.warning(
                    "Rate limit exceeded",
                    extra={
                        "client": client_key,
                        "path": request.url.path,
                        "limit": rate_limit,
                        "count": current_count,
                    },
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded. Please try again later.",
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "request_id": getattr(
                            request.state, "request_id", "unknown"
                        ),
                    },
                    headers={"Retry-After": "60"},
                )

        except Exception as e:
            # Redis errors should never break the application — fail open
            logger.error(f"Rate limiting error (failing open): {e}")

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        return response
