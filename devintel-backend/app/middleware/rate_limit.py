"""Rate limiting middleware using Redis sliding window counter with in-memory fallback.

Provides per-user rate limiting with configurable limits per endpoint group.
When Redis is available, it uses Redis sorted sets for distributed sliding-window
rate limiting. When Redis is unavailable (e.g. offline, connection failure, or
free-tier environments without Redis), it gracefully falls back to a process-local
in-memory sliding window rate limiter rather than failing open.
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
    "/api/v1/auth": 30,
    "/api/v1/chat": 20,
    "/api/v1/repos": 30,
    "/api/v1/health-score": 10,
    "/api/v1/pr-review": 10,
    "/api/v1/agent": 10,
}

# ---------------------------------------------------------------------------
# In-memory sliding-window fallback store (F-11)
#
# Process-local fallback for when Redis is unconfigured or unreachable.
# LIMITATION NOTE:
# This in-memory dictionary is strictly process-local and does NOT coordinate
# rate limits across multiple server instances, worker processes, or containers.
# In a multi-worker setup without Redis, each worker tracks its own window
# independently. When Redis is healthy, the distributed Redis-backed limiter is
# used exclusively.
# ---------------------------------------------------------------------------
_in_memory_store: dict[str, list[float]] = {}


def reset_in_memory_rate_limit_store() -> None:
    """Clear in-memory rate limiting store (useful for tests)."""
    _in_memory_store.clear()


def _check_in_memory_rate_limit(
    window_key: str,
    rate_limit: int,
    client_key: str,
    path: str,
    request_id: str = "unknown",
) -> Response | None:
    """Check and update sliding-window rate limit in memory.

    Returns a 429 JSONResponse if limit is exceeded, or None if allowed.
    """
    now = time.time()
    window_start = now - 60.0  # 60-second sliding window

    # Fetch existing timestamps and prune entries older than window
    timestamps = _in_memory_store.get(window_key, [])
    timestamps = [ts for ts in timestamps if ts > window_start]

    if len(timestamps) >= rate_limit:
        _in_memory_store[window_key] = timestamps
        logger.warning(
            "Rate limit exceeded (in-memory fallback)",
            extra={
                "client": client_key,
                "path": path,
                "limit": rate_limit,
                "count": len(timestamps),
            },
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Rate limit exceeded. Please try again later.",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "request_id": request_id,
            },
            headers={"Retry-After": "60"},
        )

    timestamps.append(now)
    _in_memory_store[window_key] = timestamps
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-user sliding window rate limiter backed by Redis with in-memory fallback.

    Uses a Redis sorted set per user+endpoint to implement a sliding
    window counter. Each request adds a timestamped entry; entries older
    than 60 seconds are pruned on each check.

    When Redis is unavailable or errors out, requests fall back to an
    in-memory sliding window counter (F-11) instead of bypassing rate limits.
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
        group = request.url.path.split('/')[3] if len(request.url.path.split('/')) > 3 else 'global'
        window_key = f"ratelimit:{client_key}:{group}"
        request_id = getattr(request.state, "request_id", "unknown")

        try:
            from app.core.redis_pool import RedisPool

            redis_client = await RedisPool.get_client()

            if redis_client is None:
                # No Redis available — activate in-memory fallback (F-11)
                fallback_response = _check_in_memory_rate_limit(
                    window_key=window_key,
                    rate_limit=rate_limit,
                    client_key=client_key,
                    path=request.url.path,
                    request_id=request_id,
                )
                if fallback_response is not None:
                    return fallback_response

                response = await call_next(request)
                response.headers["X-RateLimit-Limit"] = str(rate_limit)
                return response

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
                        "request_id": request_id,
                    },
                    headers={"Retry-After": "60"},
                )

        except Exception as e:
            # Redis errors — fall back to in-memory sliding window limiter (F-11)
            logger.error(f"Rate limiting Redis error (falling back to in-memory): {e}")
            fallback_response = _check_in_memory_rate_limit(
                window_key=window_key,
                rate_limit=rate_limit,
                client_key=client_key,
                path=request.url.path,
                request_id=request_id,
            )
            if fallback_response is not None:
                return fallback_response

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        return response
