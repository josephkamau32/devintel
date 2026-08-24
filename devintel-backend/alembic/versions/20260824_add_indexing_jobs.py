"""Alembic migration: add indexing_jobs table.

Revision ID: 20260824_add_indexing_jobs
Revises: 20260622_fix_user_cols
Create Date: 2026-08-24 12:00:00.000000

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260824_add_indexing_jobs"
down_revision: Union[str, None] = "20260622_fix_user_cols"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "indexing_jobs" not in existing_tables:
        op.create_table(
            "indexing_jobs",
            sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("repository_id", sa.UUID(as_uuid=True), nullable=False),
            sa.Column("job_type", sa.String(length=20), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("locked_by", sa.String(length=100), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        )
        op.create_index(
            "ix_indexing_jobs_repository_id",
            "indexing_jobs",
            ["repository_id"],
        )
        op.create_index(
            "ix_indexing_jobs_status_created_at",
            "indexing_jobs",
            ["status", "created_at"],
            postgresql_where=sa.text("status IN ('pending', 'running')"),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "indexing_jobs" in existing_tables:
        op.drop_table("indexing_jobs")
