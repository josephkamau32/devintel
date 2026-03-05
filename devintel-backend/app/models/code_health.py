"""Code Health model for storing per-repository quality analysis results."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.repository import Repository


class CodeHealth(Base, UUIDMixin, TimestampMixin):
    """Stores the latest AI-computed code health scores for a repository."""

    __tablename__ = "code_health"

    repo_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One record per repo (upserted on each analysis)
        index=True,
    )

    # Scores — 0.0 to 100.0
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    complexity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    documentation_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    maintainability_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    test_coverage_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    security_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Qualitative insights
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    top_issues: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    language_detected: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Analytics
    files_analyzed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository")

    def __repr__(self) -> str:
        return f"<CodeHealth(repo_id={self.repo_id}, overall={self.overall_score:.1f})>"
