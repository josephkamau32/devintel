"""Initialize database script."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.base import Base
from app.db.session import engine


async def init_db() -> None:
    """Initialize database tables."""
    print("Creating database tables...")

    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    print("Database initialized successfully!")


if __name__ == "__main__":
    from sqlalchemy import text

    asyncio.run(init_db())
