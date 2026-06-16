"""Alembic migration: add agent_type to chat model."""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260616_0200_add_agent_type"
down_revision: Union[str, None] = "20260616_0100_add_code_graph"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chats",
        sa.Column("agent_type", sa.String(length=50), nullable=True, server_default="general")
    )


def downgrade() -> None:
    op.drop_column("chats", "agent_type")