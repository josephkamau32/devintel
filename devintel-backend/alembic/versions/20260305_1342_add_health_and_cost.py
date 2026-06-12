"""Alembic migration: add code_health table and chat cost columns."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260305_1342_add_health_and_cost"
down_revision = "b3e9a1d7f45c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. code_health table
    # ------------------------------------------------------------------
    op.create_table(
        "code_health",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "repo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("overall_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("complexity_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("documentation_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("maintainability_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("test_coverage_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("security_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("top_issues", sa.Text(), nullable=True),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column("language_detected", sa.String(100), nullable=True),
        sa.Column("files_analyzed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_code_health_repo_id", "code_health", ["repo_id"])

    # ------------------------------------------------------------------
    # 2. Chat cost columns
    # ------------------------------------------------------------------
    op.add_column(
        "chats",
        sa.Column("cost_usd", sa.Numeric(precision=10, scale=8), nullable=True),
    )
    op.add_column(
        "chats",
        sa.Column("input_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "chats",
        sa.Column("output_tokens", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("chats", "output_tokens")
    op.drop_column("chats", "input_tokens")
    op.drop_column("chats", "cost_usd")
    op.drop_index("ix_code_health_repo_id", table_name="code_health")
    op.drop_table("code_health")
