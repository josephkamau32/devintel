"""Embedding model with pgvector support."""

from typing import TYPE_CHECKING
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.repository import Repository


class Embedding(Base, UUIDMixin, TimestampMixin):
    """Embedding model for storing code chunks with vector embeddings."""

    __tablename__ = "embeddings"

    # Foreign key to repository
    repo_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # File metadata
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Vector embedding (1536 dimensions for OpenAI text-embedding-3-small)
    embedding: Mapped[Vector] = mapped_column(Vector(1536), nullable=False)

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="embeddings")

    __table_args__ = (
        # Create HNSW index for fast similarity search
        Index(
            "ix_embeddings_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Embedding(id={self.id}, repo_id={self.repo_id}, file_path={self.file_path}, chunk_index={self.chunk_index})>"
