"""Redis connection pool management."""

from typing import Optional

import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisPool:
    """Redis connection pool manager."""
    
    _pool: Optional[ConnectionPool] = None
    _client: Optional[aioredis.Redis] = None
    
    @classmethod
    async def get_pool(cls) -> ConnectionPool:
        """Get or create Redis connection pool."""
        if cls._pool is None:
            cls._pool = ConnectionPool.from_url(
                settings.redis_url,
                max_connections=settings.redis_pool_size,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            logger.info(
                f"Created Redis connection pool",
                extra={
                    "url": settings.redis_url,
                    "max_connections": settings.redis_pool_size,
                },
            )
        return cls._pool
    
    @classmethod
    async def get_client(cls) -> aioredis.Redis:
        """Get Redis client from pool."""
        if cls._client is None:
            pool = await cls.get_pool()
            cls._client = aioredis.Redis(connection_pool=pool)
        return cls._client
    
    @classmethod
    async def close(cls):
        """Close Redis connection pool."""
        if cls._client:
            await cls._client.close()
            cls._client = None
        
        if cls._pool:
            await cls._pool.disconnect()
            cls._pool = None
            logger.info("Closed Redis connection pool")
    
    @classmethod
    async def health_check(cls) -> bool:
        """Check Redis connection health."""
        try:
            client = await cls.get_client()
            await client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global instance
redis_pool = RedisPool()
