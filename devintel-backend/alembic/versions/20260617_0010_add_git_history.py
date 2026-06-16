"""Alembic migration: add git_history and file_blame tables."""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260617_0010_add_git_history"
down_revision: Union[str, None] = "20260617_0000_add_generated_tests"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "git_history",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("repo_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("sha", sa.String(length=40), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("author_name", sa.String(length=255), nullable=False),
        sa.Column("author_email", sa.String(length=255), nullable=False),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("files_changed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("additions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deletions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("changed_files", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["repo_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.Index("ix_git_history_repo_committed_at", "repo_id", sa.text("committed_at desc")),
        sa.Index("ix_git_history_sha", "sha"),
    )

    op.create_table(
        "file_blame",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("repo_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("git_history_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("line_content", sa.Text(), nullable=False),
        sa.Column("commit_sha", sa.String(length=40), nullable=False),
        sa.Column("commit_message", sa.Text(), nullable=True),
        sa.Column("author_name", sa.String(length=255), nullable=True),
        sa.Column("commit_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["repo_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["git_history_id"], ["git_history.id"], ondelete="SET NULL"),
    )


def downgrade() -> None:
    op.drop_table("file_blame")
    op.drop_table("git_history")