"""Alembic migration: add migration tables."""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260617_0060_add_migrations"
down_revision: Union[str, None] = "20260617_0050_add_security_remediation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "migration_projects",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("repo_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("source_tech", sa.String(length=100), nullable=False),
        sa.Column("target_tech", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("migration_plan", sa.Text(), nullable=True),
        sa.Column("migrated_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["repo_id"], ["repositories.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "migrated_files",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("original_path", sa.String(length=500), nullable=False),
        sa.Column("migrated_path", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["migration_projects.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("migrated_files")
    op.drop_table("migration_projects")