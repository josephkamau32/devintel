from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator

from app.models.base import Base, TimestampMixin


class VectorType(TypeDecorator):
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String())
        else:
            return dialect.type_descriptor(Vector(1536))


class CodeChunk(Base, TimestampMixin):
    __tablename__ = "code_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    chunk_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)
    embedding = Column(VectorType(), nullable=True)

    repository = relationship("Repository", back_populates="chunks")

    __table_args__ = (
        Index("ix_code_chunks_repo_file", "repository_id", "file_path"),
    )

