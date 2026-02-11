"""Analytics model for tracking user metrics."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class Analytics(Base, UUIDMixin, TimestampMixin):
    """Analytics model for tracking user activity and usage metrics."""

    __tablename__ = "analytics"

    # Foreign key to user
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Metrics
    query_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_usage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    repositories_indexed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="analytics")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Analytics(id={self.id}, user_id={self.user_id}, query_count={self.query_count})>"
