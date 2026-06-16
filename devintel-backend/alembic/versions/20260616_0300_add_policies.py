"""Alembic migration: add policies table."""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260616_0300_add_policies"
down_revision: Union[str, None] = "20260616_0200_add_agent_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "policies",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("repo_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("rule_type", sa.String(length=50), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False, default=dict),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="warning"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["repo_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.Index("ix_policies_repo_id", "repo_id"),
    )


def downgrade() -> None:
    op.drop_table("policies")