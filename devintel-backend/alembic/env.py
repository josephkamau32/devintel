"""Alembic environment configuration — async PostgreSQL (asyncpg).

Handles the Render free-tier database lifecycle:
  - Fresh DB → run all migrations normally.
  - Managed DB (alembic_version has a version) → apply pending deltas.
  - Tables exist but tracking lost → stamp at HEAD so upgrade is a no-op.

The auto-stamp logic lives HERE (not in an external script) because this
is the only code path guaranteed to run before Alembic touches the DB.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.models import Base

# ── Alembic configuration ─────────────────────────────────────────────────
config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# The latest migration revision — update this whenever you add a new migration.
HEAD_REVISION = "20260824_add_indexing_status"


# ── Offline mode (generates SQL scripts, rarely used) ──────────────────────
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (connects to the live database) ───────────────────────────
def do_run_migrations(connection) -> None:
    """Run migrations with auto-detection of orphaned databases.

    If the database has app tables (e.g. ``users``) but Alembic's
    ``alembic_version`` table is missing or empty, we stamp the
    current HEAD revision directly.  This prevents the initial
    migration from crashing with ``DuplicateTableError`` when
    Render's free-tier DB loses its tracking table.
    """
    from sqlalchemy import inspect as sa_inspect

    inspector = sa_inspect(connection)
    existing_tables = inspector.get_table_names()
    has_app_tables = "users" in existing_tables
    has_alembic = "alembic_version" in existing_tables

    # ── Widen version_num column if it exists ──────────────────────────
    if has_alembic:
        connection.execute(
            text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)")
        )

    # ── Auto-stamp: tables exist but Alembic tracking is lost ─────────
    if has_app_tables:
        needs_stamp = False

        if not has_alembic:
            # No alembic_version table at all — create it and stamp
            connection.execute(text(
                "CREATE TABLE IF NOT EXISTS alembic_version ("
                "  version_num VARCHAR(128) NOT NULL, "
                "  CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)"
                ")"
            ))
            needs_stamp = True
        else:
            # alembic_version exists — check if it's empty
            result = connection.execute(text("SELECT version_num FROM alembic_version"))
            row = result.first()
            if not row:
                needs_stamp = True
            else:
                print(f"Alembic tracking OK — current revision: {row[0]}")

        if needs_stamp:
            connection.execute(
                text("INSERT INTO alembic_version (version_num) VALUES (:rev)"),
                {"rev": HEAD_REVISION},
            )
            print(f"Auto-stamped alembic_version at HEAD ({HEAD_REVISION})")

    # ── Run Alembic migrations ────────────────────────────────────────
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
        await connection.commit()
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
