"""Caching utilities with Redis or in-memory fallback.

When REDIS_URL is configured, the cache uses Redis with connection pooling.
When REDIS_URL is empty (free-tier deployment), the cache seamlessly falls
back to an in-memory dict with TTL-based expiry.
"""

import json
import time
from typing import Any, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class _InMemoryCache:
    """Simple in-memory cache with TTL support.

    Thread/async-safe for single-process deployments (Render free tier).
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}  # key -> (value, expires_at)

    async def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        self._store[key] = (value, time.time() + ttl)
        return True

    async def delete(self, key: str) -> bool:
        self._store.pop(key, None)
        return True

    async def close(self) -> None:
        self._store.clear()


class CacheService:
    """Dual-mode cache — Redis when configured, in-memory otherwise.

    The public API is identical regardless of backend, so callers never
    need to know which mode is active.
    """

    def __init__(self) -> None:
        self._redis: Any = None
        self._mem: Optional[_InMemoryCache] = None

        if settings.REDIS_URL:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                )
                logger.info("Cache backend: Redis")
            except Exception as e:
                logger.warning(f"Redis init failed, falling back to memory: {e}")
                self._mem = _InMemoryCache()
        else:
            self._mem = _InMemoryCache()
            logger.info("Cache backend: in-memory (REDIS_URL not configured)")

    # ── Public API ────────────────────────────────────────────────────

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if self._mem is not None:
            return await self._mem.get(key)
        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = settings.REDIS_CACHE_TTL,
    ) -> bool:
        """Set value in cache with TTL."""
        if self._mem is not None:
            return await self._mem.set(key, value, ttl)
        try:
            json_value = json.dumps(value)
            await self._redis.setex(key, ttl, json_value)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if self._mem is not None:
            return await self._mem.delete(key)
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> bool:
        """Delete all keys matching a glob pattern."""
        if self._mem is not None:
            # Simple glob match for in-memory store
            import fnmatch
            keys_to_delete = [
                k for k in list(self._mem._store.keys())
                if fnmatch.fnmatch(k, pattern)
            ]
            for k in keys_to_delete:
                del self._mem._store[k]
            return True
        try:
            cursor = 0
            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self._redis.delete(*keys)
                if cursor == 0:
                    break
            return True
        except Exception as e:
            logger.error(f"Cache delete_pattern error: {e}")
            return False

    async def close(self) -> None:
        """Close cache connection."""
        if self._mem is not None:
            await self._mem.close()
        elif self._redis is not None:
            try:
                await self._redis.close()
            except Exception as e:
                logger.error(f"Error closing Redis: {e}")


# Global cache instance
cache = CacheService()
