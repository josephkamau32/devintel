#!/bin/sh
set -e

echo "=== DevIntel startup ==="

# Detect database state and prepare for Alembic migrations.
# Handles three scenarios:
#   1. Fresh DB (no tables)            → alembic upgrade head runs cleanly
#   2. Managed DB (alembic_version ok) → alembic upgrade head applies deltas
#   3. Tables exist but tracking lost  → stamp head, then upgrade (no-op)
python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def prepare_db():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        # Check if alembic_version table exists
        result = await conn.execute(text(
            \"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')\"
        ))
        has_alembic = result.scalar()

        # Check if the 'users' table exists (proxy for 'do app tables exist?')
        result = await conn.execute(text(
            \"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')\"
        ))
        has_tables = result.scalar()

        if has_alembic:
            # Widen the column in case older varchar(32) is still present
            await conn.execute(text(
                'ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)'
            ))
            result = await conn.execute(text('SELECT version_num FROM alembic_version'))
            row = result.first()
            if row:
                print(f'Alembic tracking OK — current version: {row[0]}')
            elif has_tables:
                # alembic_version exists but is empty, yet app tables are present.
                # This happens when the DB was partially reset. Stamp at head.
                print('alembic_version empty but tables exist — stamping at head')
            else:
                # alembic_version exists but is empty and no tables — truly fresh.
                # Drop the empty tracking table so Alembic starts clean.
                await conn.execute(text('DROP TABLE alembic_version'))
                print('Empty alembic_version with no tables — dropped for clean start')
        elif has_tables:
            # Tables exist (from create_all) but no alembic_version tracking.
            # Create alembic_version so 'stamp' works, then stamp at head.
            print('Tables exist but no alembic tracking — will stamp at head')
        else:
            print('Fresh database — migrations will create everything')

    await engine.dispose()

asyncio.run(prepare_db())
"

# If tables exist but Alembic has no tracked version, stamp at head
# so that 'upgrade head' becomes a no-op instead of re-running CREATE TABLEs.
python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def maybe_stamp():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        result = await conn.execute(text(
            \"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')\"
        ))
        has_tables = result.scalar()

        result = await conn.execute(text(
            \"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')\"
        ))
        has_alembic = result.scalar()

        needs_stamp = False
        if has_tables and not has_alembic:
            needs_stamp = True
        elif has_tables and has_alembic:
            result = await conn.execute(text('SELECT version_num FROM alembic_version'))
            row = result.first()
            if not row:
                needs_stamp = True

    await engine.dispose()
    return needs_stamp

needs_stamp = asyncio.run(maybe_stamp())
if needs_stamp:
    import subprocess, sys
    print('Stamping database at head...')
    subprocess.run([sys.executable, '-m', 'alembic', 'stamp', 'head'], check=True)
    print('Stamp complete — database is now tracked by Alembic')
" || echo "Stamp check completed (non-critical)"

# Run migrations
echo "Running alembic upgrade head..."
alembic upgrade head
echo "Migrations complete!"

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1

