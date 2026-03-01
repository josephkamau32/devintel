"""Add default_branch to repositories and unique constraints

Revision ID: b3e9a1d7f45c
Revises: ac4f26b751bf
Create Date: 2026-03-01 12:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3e9a1d7f45c'
down_revision: Union[str, None] = 'ac4f26b751bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Add default_branch column with a server default so existing rows get "main"
    op.add_column(
        'repositories',
        sa.Column(
            'default_branch',
            sa.String(length=255),
            server_default='main',
            nullable=False,
        ),
    )

    # Add unique constraints to prevent duplicate repository connections.
    # Personal repos: unique per (user_id, full_name) where org_id IS NULL
    # Org repos: unique per (org_id, full_name)
    # We use partial unique indexes (PostgreSQL-specific) so NULL columns don't conflict.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_repositories_user_full_name
        ON repositories (user_id, full_name)
        WHERE org_id IS NULL AND user_id IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_repositories_org_full_name
        ON repositories (org_id, full_name)
        WHERE org_id IS NOT NULL
        """
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.execute("DROP INDEX IF EXISTS uq_repositories_org_full_name")
    op.execute("DROP INDEX IF EXISTS uq_repositories_user_full_name")
    op.drop_column('repositories', 'default_branch')
