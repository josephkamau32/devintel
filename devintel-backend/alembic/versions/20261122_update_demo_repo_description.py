"""Update demo repository description to reflect indexed scope.

Revision ID: 20261122_update_demo_desc
Revises: 20260826_drop_indexed_status_column
Create Date: 2026-11-22 22:00:00.000000
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261122_update_demo_desc"
down_revision: Union[str, None] = "20260826_drop_indexed_status_column"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update description of pre-indexed sample repositories."""
    conn = op.get_bind()
    new_desc = "Pre-indexed sample repository: snapshot of backend modules app/ai, app/services and app/models."
    conn.execute(
        sa.text(
            "UPDATE repositories SET description = :desc "
            "WHERE full_name IN ('josephkamau32/devintel', 'devintel/devintel-core')"
        ),
        {"desc": new_desc},
    )


def downgrade() -> None:
    """Revert description update."""
    conn = op.get_bind()
    old_desc = "DevIntel AI Core - Intelligent Repository Intelligence & AI Assistant Platform"
    conn.execute(
        sa.text(
            "UPDATE repositories SET description = :desc "
            "WHERE full_name IN ('josephkamau32/devintel', 'devintel/devintel-core')"
        ),
        {"desc": old_desc},
    )
