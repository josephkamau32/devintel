"""Alembic migration: add code_graph table for call graph relationships.

Revision ID: 20260616_0100_add_code_graph
Revises: 20260616_0000_add_incremental_indexing_fields
Create Date: 2026-06-16 01:00:00.000000

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260616_0100_add_code_graph"
down_revision: Union[str, None] = "20260616_0000_add_incremental_indexing_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "code_graph",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("repo_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("caller_chunk_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("callee_chunk_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("edge_type", sa.String(length=50), nullable=False, server_default="direct_call"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["repo_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["caller_chunk_id"], ["embeddings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["callee_chunk_id"], ["embeddings.id"], ondelete="CASCADE"),
        sa.Index("ix_code_graph_repo_id", "repo_id"),
        sa.Index("ix_code_graph_caller", "caller_chunk_id"),
        sa.Index("ix_code_graph_callee", "callee_chunk_id"),
    )


def downgrade() -> None:
    op.drop_table("code_graph")