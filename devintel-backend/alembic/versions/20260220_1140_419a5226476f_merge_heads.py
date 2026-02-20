"""merge_heads

Revision ID: 419a5226476f
Revises: 002_pgvector_indexes, ceef8efa415f
Create Date: 2026-02-20 11:40:43.451351

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '419a5226476f'
down_revision: Union[str, None] = ('002_pgvector_indexes', 'ceef8efa415f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    pass


def downgrade() -> None:
    """Downgrade database schema."""
    pass
