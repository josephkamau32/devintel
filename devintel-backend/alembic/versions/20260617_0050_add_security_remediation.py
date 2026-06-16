"""Alembic migration: add security_remediation_agent config."""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260617_0050_add_security_remediation"
down_revision: Union[str, None] = "20260617_0040_add_collaboration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No schema changes - security_remediation agent is code-only."""
    pass


def downgrade() -> None:
    """No schema changes - security_remediation agent is code-only."""
    pass