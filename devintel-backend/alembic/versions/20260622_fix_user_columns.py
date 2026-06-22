"""Add username, is_active, is_verified columns to users table

Revision ID: 20260622_fix_user_cols
Revises: 20260617_0060_add_migrations
Create Date: 2026-06-22 12:00:00.000000

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260622_fix_user_cols"
down_revision: Union[str, None] = "20260617_0060_add_migrations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = [c["name"] for c in inspector.get_columns("users")]

    # Add username column (mapped as github_username in the model)
    if "username" not in existing_cols:
        op.add_column(
            "users",
            sa.Column("username", sa.String(length=100), nullable=True),
        )
    # Add is_active with a default so existing rows get a value
    if "is_active" not in existing_cols:
        op.add_column(
            "users",
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
        )
    # Add is_verified with a default
    if "is_verified" not in existing_cols:
        op.add_column(
            "users",
            sa.Column(
                "is_verified",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )


def downgrade() -> None:
    op.drop_column("users", "is_verified")
    op.drop_column("users", "is_active")
    op.drop_column("users", "username")
