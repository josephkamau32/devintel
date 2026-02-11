"""Repository model."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.chat import Chat
    from app.models.embedding import Embedding
    from app.models.user import User


class Repository(Base, UUIDMixin, TimestampMixin):
    """Repository model for GitHub repositories."""

    __tablename__ = "repositories"

    # Foreign key to user
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Repository metadata
    repo_name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    stars: Mapped[int] = mapped_column(default=0, nullable=False)
    language: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Indexing status
    indexed_status: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    indexing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    indexing_progress: Mapped[int] = mapped_column(default=0, nullable=False)  # 0-100

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="repositories")
    embeddings: Mapped[List["Embedding"]] = relationship(
        "Embedding",
        back_populates="repository",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    chats: Mapped[List["Chat"]] = relationship(
        "Chat",
        back_populates="repository",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Repository(id={self.id}, full_name={self.full_name}, indexed={self.indexed_status})>"
