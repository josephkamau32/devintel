#!/bin/sh
set -e

echo "=== DevIntel startup ==="

# Widen alembic_version.version_num if the table exists
# AND drop all existing tables if db is in a corrupted state from partial migrations
python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def prepare_db():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        # Check if alembic_version exists
        result = await conn.execute(text(
            \"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')\"
        ))
        has_alembic = result.scalar()

        if has_alembic:
            # Check current version
            result = await conn.execute(text('SELECT version_num FROM alembic_version'))
            row = result.first()
            if row:
                current = row[0]
                print(f'Current alembic version: {current}')
                # Widen the column for future migrations
                await conn.execute(text(
                    'ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)'
                ))
                print('alembic_version column widened to VARCHAR(128)')
            else:
                print('alembic_version exists but is empty - dropping all tables for clean start')
                # Get all table names
                result = await conn.execute(text(
                    \"SELECT tablename FROM pg_tables WHERE schemaname = 'public'\"
                ))
                tables = [r[0] for r in result.fetchall()]
                for table in tables:
                    await conn.execute(text(f'DROP TABLE IF EXISTS \"{table}\" CASCADE'))
                    print(f'  Dropped table: {table}')
                print('All tables dropped - clean migration will follow')
        else:
            print('No alembic_version table - fresh database, proceeding normally')

    await engine.dispose()

asyncio.run(prepare_db())
"

# Run migrations
echo "Running alembic upgrade head..."
alembic upgrade head
echo "Migrations complete!"

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
