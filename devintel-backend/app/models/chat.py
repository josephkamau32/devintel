"""Chat model for storing conversation history."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.repository import Repository
    from app.models.user import User


class Chat(Base, UUIDMixin, TimestampMixin):
    """Chat model for storing user questions and AI responses."""

    __tablename__ = "chats"

    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    repo_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    org_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Chat content
    question: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)

    # Analytics
    token_usage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Cost tracking (GPT-4o pricing: $2.50/1M input, $10.00/1M output)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[Optional[float]] = mapped_column(
        Numeric(precision=10, scale=8), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chats")
    repository: Mapped["Repository"] = relationship("Repository", back_populates="chats")
    organization: Mapped[Optional["Organization"]] = relationship("Organization")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Chat(id={self.id}, user_id={self.user_id}, repo_id={self.repo_id})>"
