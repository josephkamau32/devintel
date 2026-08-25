"""Drop broken and redundant idx_embeddings_repo_vector index.

Revision ID: 20260825_drop_broken_repo_vector_index
Revises: 20260824_add_indexing_status
Create Date: 2026-08-25 14:10:00.000000

Rationale:
  The `idx_embeddings_repo_vector` index was originally created in migration 002 as:
    CREATE INDEX idx_embeddings_repo_vector ON embeddings (repo_id) INCLUDE (embedding);
  
  Because no index method was specified, PostgreSQL created a standard B-Tree index.
  PostgreSQL B-Tree indexes have a maximum tuple size of ~2.7 KB (1/3 of a standard 8 KB page).
  A 1536-dimensional vector (OpenAI text-embedding-3-small) requires 1536 * 4 = 6,144 bytes,
  which far exceeds this limit and causes any insert into `embeddings` to fail immediately with:
    ProgramLimitExceededError: index row size 6176 exceeds btree version 4 maximum 2704 for index "idx_embeddings_repo_vector"

  Furthermore:
  - Vector similarity search is already properly indexed via HNSW (`ix_embeddings_hnsw`)
    and IVFFlat (`embeddings_vector_idx`).
  - Repository filtering is already indexed via B-Tree index on `(repo_id)` (`idx_embeddings_repo_id` / `ix_embeddings_repo_id`).
  - Therefore, `idx_embeddings_repo_vector` is fundamentally broken, unusable, and redundant.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260825_drop_broken_repo_vector_index"
down_revision: Union[str, None] = "20260824_add_indexing_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop idx_embeddings_repo_vector if it exists."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Check existing indexes on embeddings table defensively
    if "embeddings" in inspector.get_table_names():
        indexes = [idx["name"] for idx in inspector.get_indexes("embeddings")]
        if "idx_embeddings_repo_vector" in indexes:
            op.drop_index("idx_embeddings_repo_vector", table_name="embeddings")
        else:
            op.execute("DROP INDEX IF EXISTS idx_embeddings_repo_vector;")
    else:
        op.execute("DROP INDEX IF EXISTS idx_embeddings_repo_vector;")


def downgrade() -> None:
    """Do not recreate broken btree index on rollback."""
    # We deliberately do not re-add the broken B-Tree index on downgrade
    # because it prevents any 1536-dim vector insert from succeeding.
    pass
