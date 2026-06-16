"""Cross-repository knowledge models for similarity search."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, String, Float, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.repository import Repository


class CrossRepoKnowledge(Base, UUIDMixin, TimestampMixin):
    """Cross-repository pattern recommendations."""

    __tablename__ = "cross_repo_knowledge"

    __table_args__ = (
        Index("ix_cross_repo_similarity", "repo_id", "similarity_score.desc()"),
    )

    # Foreign keys
    repo_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
    )
    reference_repo_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Knowledge item
    pattern_type: Mapped[str] = mapped_column(String(100), nullable=False)
    pattern_key: Mapped[str] = mapped_column(String(255), nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Metadata
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    line_number: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", foreign_keys=[repo_id])
    reference_repository: Mapped["Repository"] = relationship("Repository", foreign_keys=[reference_repo_id])

    def __repr__(self) -> str:
        return f"<CrossRepoKnowledge(repo={self.repo_id}, ref={self.reference_repo_id}, type={self.pattern_type})>"