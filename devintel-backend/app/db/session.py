"""Database session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Create engine arguments
engine_args = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,
}

if settings.DATABASE_URL.startswith("sqlite"):
    from sqlalchemy.pool import StaticPool
    engine_args["poolclass"] = StaticPool
    engine_args["connect_args"] = {"check_same_thread": False}
else:
    engine_args["pool_size"] = settings.DATABASE_POOL_SIZE
    engine_args["max_overflow"] = settings.DATABASE_MAX_OVERFLOW

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, **engine_args)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions.

    Commits on success so that flush()-based repositories persist their changes.
    Rolls back on any unhandled exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
