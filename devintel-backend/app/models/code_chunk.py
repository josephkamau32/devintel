from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.models.base import Base, TimestampMixin


class CodeChunk(Base, TimestampMixin):
    __tablename__ = "code_chunks"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    chunk_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)
    embedding = Column(Vector(1536), nullable=True)

    repository = relationship("Repository", back_populates="chunks")

    __table_args__ = (
        Index("ix_code_chunks_repo_file", "repository_id", "file_path"),
    )
