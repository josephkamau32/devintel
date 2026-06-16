"""Alembic migration: add collaboration tables."""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260617_0040_add_collaboration"
down_revision: Union[str, None] = "20260617_0030_add_cross_repo_knowledge"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "collaboration_sessions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("repo_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("session_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("participants_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["repo_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.Index("ix_collab_session_repo_active", "repo_id", "is_active"),
    )

    op.create_table(
        "collaboration_messages",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("message_type", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("cursor_line", sa.Integer(), nullable=True),
        sa.Column("cursor_column", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["collaboration_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("collaboration_messages")
    op.drop_table("collaboration_sessions")