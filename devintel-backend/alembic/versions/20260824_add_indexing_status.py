"""Add indexing_status VARCHAR column alongside legacy indexed_status boolean.

Phase 1 of a two-phase migration (add new column + backfill; drop old column later).

The original schema created `indexed_status` as a BOOLEAN (true/false). The application
now uses a 4-value string enum: pending, indexing, complete, failed. This migration adds
the new `indexing_status` column and backfills existing rows based on the boolean value.

NOTE ON LOSSY BACKFILL:
  indexed_status = true  => indexing_status = 'complete'
  indexed_status = false => indexing_status = 'pending'

  This is a known, accepted limitation of the historical data. A repo that previously
  failed indexing has no way to be distinguished from one that simply hasn't started,
  since the boolean never captured a failure state. All false values are conservatively
  mapped to 'pending'.

Revision ID: 20260824_add_indexing_status
Revises: 20260824_add_indexing_jobs
Create Date: 2026-08-24 23:20:00.000000

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260824_add_indexing_status"
down_revision: Union[str, None] = "20260824_add_indexing_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = [c["name"] for c in inspector.get_columns("repositories")]

    # 1. Add the new indexing_status VARCHAR(20) column if it doesn't already exist.
    if "indexing_status" not in existing_cols:
        op.add_column(
            "repositories",
            sa.Column(
                "indexing_status",
                sa.String(length=20),
                nullable=False,
                server_default="pending",
            ),
        )

    # 2. Backfill from the legacy indexed_status boolean:
    #    true  -> 'complete'
    #    false -> 'pending'  (lossy: failed states indistinguishable from pending)
    if "indexed_status" in existing_cols:
        op.execute(
            sa.text(
                "UPDATE repositories "
                "SET indexing_status = 'complete' "
                "WHERE indexed_status = true"
            )
        )
        op.execute(
            sa.text(
                "UPDATE repositories "
                "SET indexing_status = 'pending' "
                "WHERE indexed_status = false"
            )
        )

    # NOTE: We intentionally do NOT drop indexed_status in this migration.
    # That will happen in a follow-up migration after production verification.


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = [c["name"] for c in inspector.get_columns("repositories")]

    if "indexing_status" in existing_cols:
        op.drop_column("repositories", "indexing_status")
