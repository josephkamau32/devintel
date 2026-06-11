"""create_user_token_fields

Revision ID: 001_user_tokens
Revises:
Create Date: 2026-02-15

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '001_user_tokens'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add token fields to users table."""
    # Add github_access_token_encrypted column
    op.add_column('users', sa.Column('github_access_token_encrypted', sa.String(length=1000), nullable=True))

    # Add refresh_token column
    op.add_column('users', sa.Column('refresh_token', sa.String(length=500), nullable=True))


def downgrade() -> None:
    """Remove token fields from users table."""
    op.drop_column('users', 'refresh_token')
    op.drop_column('users', 'github_access_token_encrypted')
