#!/bin/sh
set -e

# Widen alembic_version.version_num column if it exists (default is varchar(32),
# but our revision IDs are longer than 32 chars)
python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def widen_version_col():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text(
            \"ALTER TABLE IF EXISTS alembic_version \"
            \"ALTER COLUMN version_num TYPE VARCHAR(128)\"
        ))
    await engine.dispose()
    print('alembic_version column widened to VARCHAR(128)')

asyncio.run(widen_version_col())
"

# Run migrations
alembic upgrade head

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
