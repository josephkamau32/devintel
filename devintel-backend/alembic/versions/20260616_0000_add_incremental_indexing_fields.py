"""Alembic migration: add incremental indexing fields.

Revision ID: 20260616_0000_add_incremental_indexing_fields
Revises: 20260611_1745_add_password_auth
Create Date: 2026-06-16 00:00:00.000000

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260616_0000_add_incremental_indexing_fields"
down_revision: Union[str, None] = "20260611_1745_add_password_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add last_indexed_commit_sha column
    op.add_column(
        "repositories",
        sa.Column("last_indexed_commit_sha", sa.String(length=40), nullable=True)
    )

    # Add indexing_mode column with default 'full'
    op.add_column(
        "repositories",
        sa.Column(
            "indexing_mode",
            sa.String(length=20),
            nullable=False,
            server_default="full"
        )
    )

    # Create index on last_indexed_commit_sha for faster lookups
    op.create_index(
        op.f("ix_repositories_last_indexed_commit_sha"),
        "repositories",
        ["last_indexed_commit_sha"]
    )


def downgrade() -> None:
    # Drop the index
    op.drop_index(
        op.f("ix_repositories_last_indexed_commit_sha"),
        table_name="repositories"
    )

    # Drop the columns
    op.drop_column("repositories", "indexing_mode")
    op.drop_column("repositories", "last_indexed_commit_sha")