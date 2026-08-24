"""Indexing job model for durable asynchronous repository indexing tasks."""

from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class IndexingJob(Base, TimestampMixin):
    """Durable job record for background repository indexing."""

    __tablename__ = "indexing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    repository_id = Column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="pending", server_default="pending")
    payload = Column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
        server_default="{}",
    )
    attempt_count = Column(Integer, nullable=False, default=0, server_default="0")
    max_attempts = Column(Integer, nullable=False, default=3, server_default="3")
    error_message = Column(Text, nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    locked_by = Column(String(100), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    repository = relationship("Repository", back_populates="indexing_jobs")

    __table_args__ = (
        Index(
            "ix_indexing_jobs_status_created_at",
            "status",
            "created_at",
            postgresql_where=text("status IN ('pending', 'running')"),
        ),
    )

    def __repr__(self) -> str:
        return f"<IndexingJob id={self.id} repo_id={self.repository_id} type={self.job_type} status={self.status}>"
