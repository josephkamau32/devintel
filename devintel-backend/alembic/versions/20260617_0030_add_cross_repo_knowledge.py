"""Alembic migration: add cross_repo_knowledge table."""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260617_0030_add_cross_repo_knowledge"
down_revision: Union[str, None] = "20260617_0020_add_architecture_diagrams"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cross_repo_knowledge",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("repo_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("reference_repo_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("pattern_type", sa.String(length=100), nullable=False),
        sa.Column("pattern_key", sa.String(length=255), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["repo_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reference_repo_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.Index("ix_cross_repo_similarity", "repo_id", sa.text("similarity_score desc")),
    )


def downgrade() -> None:
    op.drop_table("cross_repo_knowledge")