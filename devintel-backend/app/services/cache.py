"""Caching utilities using Redis with connection pooling."""

import json
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """Async Redis cache with connection pooling."""

    def __init__(self):
        """Initialize cache."""
        self.redis: Optional[aioredis.Redis] = None
        # The instruction snippet provided a malformed line: `self._use_pool = Truem_url(...)`
        # Assuming the intent was to initialize self.redis using aioredis.from_url,
        # which inherently uses connection pooling, and to add a flag `_use_pool`.
        # The `aioredis.from_url` method already returns a Redis client that manages a connection pool.
        self._use_pool = True # This flag was explicitly added in the instruction snippet
        self.redis = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = await self.redis.get(key)
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
        ttl: int = settings.redis_cache_ttl,
    ) -> bool:
        """Set value in cache with TTL."""
        try:
            json_value = json.dumps(value)
            await self.redis.setex(key, ttl, json_value)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        await self.redis.close()


# Global cache instance
cache = CacheService()
