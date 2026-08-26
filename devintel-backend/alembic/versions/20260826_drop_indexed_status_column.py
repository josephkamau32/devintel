"""Drop legacy indexed_status boolean column from repositories.

Phase 2 of the two-phase migration:
  Phase 1 (20260824_add_indexing_status): Added indexing_status VARCHAR(20) and backfilled data.
  Phase 2 (this migration): Drops the legacy indexed_status boolean column now that all application
  code, frontend, vscode extension, and tasks use indexing_status exclusively.

Revision ID: 20260826_drop_indexed_status_column
Revises: 20260825_drop_broken_repo_vector_index
Create Date: 2026-08-26 12:00:00.000000

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260826_drop_indexed_status_column"
down_revision: Union[str, None] = "20260825_drop_broken_repo_vector_index"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the legacy indexed_status boolean column if present."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if "repositories" in inspector.get_table_names():
        existing_cols = [c["name"] for c in inspector.get_columns("repositories")]
        if "indexed_status" in existing_cols:
            op.drop_column("repositories", "indexed_status")


def downgrade() -> None:
    """Recreate the legacy indexed_status boolean column.

    NOTE ON LOSSY DOWNGRADE:
      Historical true/false semantics cannot be fully reconstructed from indexing_status alone.
      This is a one-way data loss on downgrade, which is expected and acceptable at this stage.
      We map 'complete' -> true, and all other states ('pending', 'indexing', 'failed') -> false.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "repositories" in inspector.get_table_names():
        existing_cols = [c["name"] for c in inspector.get_columns("repositories")]
        if "indexed_status" not in existing_cols:
            op.add_column(
                "repositories",
                sa.Column(
                    "indexed_status",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.text("false"),
                ),
            )
            # Best-effort backfill:
            op.execute(
                sa.text(
                    "UPDATE repositories "
                    "SET indexed_status = true "
                    "WHERE indexing_status = 'complete'"
                )
            )
            op.execute(
                sa.text(
                    "UPDATE repositories "
                    "SET indexed_status = false "
                    "WHERE indexing_status != 'complete'"
                )
            )
