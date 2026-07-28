"""Pre-migration database check.

Detects the state of the database and ensures Alembic can run
`upgrade head` without crashing on DuplicateTableError.

Scenarios handled:
  1. Fresh DB (no tables, no alembic_version) → do nothing, Alembic runs from scratch.
  2. Managed DB (alembic_version has a version) → widen version_num column, done.
  3. Tables exist but Alembic tracking is missing/empty → run `alembic stamp head`
     so that `upgrade head` becomes a no-op and doesn't re-CREATE existing tables.
"""

import asyncio
import subprocess
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings


async def check_db_state() -> str:
    """Return one of: 'FRESH', 'MANAGED', 'NEEDS_STAMP'."""
    engine = create_async_engine(settings.DATABASE_URL)
    try:
        async with engine.begin() as conn:
            # Do app tables exist?
            result = await conn.execute(text(
                "SELECT EXISTS ("
                "  SELECT FROM information_schema.tables "
                "  WHERE table_schema = 'public' AND table_name = 'users'"
                ")"
            ))
            has_tables = result.scalar()

            # Does alembic_version exist?
            result = await conn.execute(text(
                "SELECT EXISTS ("
                "  SELECT FROM information_schema.tables "
                "  WHERE table_schema = 'public' AND table_name = 'alembic_version'"
                ")"
            ))
            has_alembic = result.scalar()

            if not has_tables and not has_alembic:
                return "FRESH"

            if has_alembic:
                # Widen the column — our revision IDs exceed the default varchar(32)
                await conn.execute(text(
                    "ALTER TABLE alembic_version "
                    "ALTER COLUMN version_num TYPE VARCHAR(128)"
                ))
                result = await conn.execute(text(
                    "SELECT version_num FROM alembic_version"
                ))
                row = result.first()
                if row and row[0]:
                    return "MANAGED"
                # alembic_version exists but is empty → needs stamp
                return "NEEDS_STAMP"

            # Tables exist but no alembic_version at all → needs stamp
            return "NEEDS_STAMP"
    finally:
        await engine.dispose()


def main() -> None:
    state = asyncio.run(check_db_state())
    print(f"Database state: {state}")

    if state == "FRESH":
        print("Fresh database — Alembic will create everything from scratch.")
    elif state == "MANAGED":
        print("Alembic tracking is intact — upgrade head will apply any pending migrations.")
    elif state == "NEEDS_STAMP":
        print("Tables exist but Alembic has no tracked version.")
        print("Stamping database at head to prevent DuplicateTableError...")
        result = subprocess.run(
            ["alembic", "stamp", "head"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("Stamp successful — Alembic now tracks this database.")
        else:
            print(f"Stamp stdout: {result.stdout}")
            print(f"Stamp stderr: {result.stderr}")
            # Don't crash — alembic upgrade head might still work
            print("WARNING: stamp failed, but continuing anyway.")


if __name__ == "__main__":
    main()
