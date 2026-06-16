"""Database session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# Create engine arguments
engine_args = {
    "echo": settings.debug,
    "pool_pre_ping": True,
}

if not settings.database_url:
    # Default to SQLite in-memory for development when no DB URL provided
    database_url = "sqlite+aiosqlite:///:memory:"
    logger = __import__("app.core.logging").core.logging.get_logger(__name__)
    logger.warning("DATABASE_URL not set, using SQLite in-memory database")
else:
    database_url = settings.database_url

if "sqlite" in database_url:
    engine_args["poolclass"] = StaticPool
    engine_args["connect_args"] = {"check_same_thread": False}
else:
    engine_args["pool_size"] = settings.database_pool_size
    engine_args["max_overflow"] = settings.database_max_overflow

# Create async engine
engine = create_async_engine(database_url, **engine_args)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
