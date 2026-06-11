"""add_pgvector_ann_indexes

Revision ID: 002_pgvector_indexes
Revises: 001_user_tokens
Create Date: 2026-02-15

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '002_pgvector_indexes'
down_revision = '001_user_tokens'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add ANN indexes for pgvector similarity search."""
    # Create IVFFlat index for faster similarity search
    # lists parameter: number of clusters (recommended: rows/1000, min 10)
    # For 100k embeddings, use lists=100
    op.execute("""
        CREATE INDEX IF NOT EXISTS embeddings_vector_idx
        ON embeddings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)

    # Add index on repo_id for faster filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_embeddings_repo_id
        ON embeddings (repo_id);
    """)

    # Composite index for repo_id + vector search
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_embeddings_repo_vector
        ON embeddings (repo_id)
        INCLUDE (embedding);
    """)


def downgrade() -> None:
    """Remove ANN indexes."""
    op.execute("DROP INDEX IF EXISTS idx_embeddings_repo_vector;")
    op.execute("DROP INDEX IF EXISTS idx_embeddings_repo_id;")
    op.execute("DROP INDEX IF EXISTS embeddings_vector_idx;")
