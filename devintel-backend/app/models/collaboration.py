"""Collaboration models for real-time multi-user sessions."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.repository import Repository
    from app.models.user import User


class CollaborationSession(Base, UUIDMixin, TimestampMixin):
    """Real-time collaboration session for repositories."""

    __tablename__ = "collaboration_sessions"

    __table_args__ = (
        Index("ix_collab_session_repo_active", "repo_id", "is_active"),
    )

    # Foreign keys
    repo_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Session info
    session_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    participants_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", backref="collab_sessions")
    owner: Mapped["User"] = relationship("User", backref="collab_sessions")

    def __repr__(self) -> str:
        return f"<CollaborationSession(id={self.id}, repo={self.repo_id}, active={self.is_active})>"


class CollaborationMessage(Base, UUIDMixin, TimestampMixin):
    """Messages within a collaboration session."""

    __tablename__ = "collaboration_messages"

    # Foreign keys
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("collaboration_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Message content
    message_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'text', 'cursor', 'code_change', 'ai_suggestion'
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Cursor position for real-time editing
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cursor_line: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cursor_column: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    session: Mapped["CollaborationSession"] = relationship("CollaborationSession", backref="messages")
    user: Mapped["User"] = relationship("User", backref="collab_messages")

    def __repr__(self) -> str:
        return f"<CollaborationMessage(id={self.id}, type={self.message_type})>"