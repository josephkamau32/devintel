"""Alembic migration: add password auth
Revision ID: 20260611_1745_add_password_auth
Revises: 20260305_1342_add_health_and_cost
Create Date: 2026-06-11 17:45:00.000000

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260305_add_health_cost"
down_revision: Union[str, None] = "b3e9a1d7f45c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make github_id nullable
    op.alter_column("users", "github_id", existing_type=sa.VARCHAR(length=255), nullable=True)

    # Add hashed_password
    op.add_column("users", sa.Column("hashed_password", sa.String(length=255), nullable=True))

    # Make email unique and indexed
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)


def downgrade() -> None:
    # Drop email index
    op.drop_index(op.f("ix_users_email"), table_name="users")

    # Drop hashed_password
    op.drop_column("users", "hashed_password")

    # Make github_id not nullable
    op.alter_column("users", "github_id", existing_type=sa.VARCHAR(length=255), nullable=False)
