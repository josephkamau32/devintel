"""Repository model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.chat import Chat
    from app.models.code_graph import CodeGraph
    from app.models.embedding import Embedding
    from app.models.generated_test import GeneratedTest
    from app.models.organization import Organization
    from app.models.policy import Policy
    from app.models.user import User


class Repository(Base, UUIDMixin, TimestampMixin):
    """Repository model for GitHub repositories."""

    __tablename__ = "repositories"

    # Foreign keys
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    org_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Repository metadata
    repo_name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    stars: Mapped[int] = mapped_column(default=0, nullable=False)
    language: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    default_branch: Mapped[str] = mapped_column(String(255), default="main", server_default="main", nullable=False)

    # Indexing status
    indexed_status: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    indexing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    indexing_progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0-100

    # Incremental indexing
    last_indexed_commit_sha: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)  # Git SHA for incremental updates
    indexing_mode: Mapped[str] = mapped_column(
        String(20),
        default="full",
        server_default="full",
        nullable=False,
    )  # 'full' or 'incremental'

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="repositories")
    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="repositories")
    embeddings: Mapped[list["Embedding"]] = relationship(
        "Embedding",
        back_populates="repository",
        cascade="all, delete-orphan",
        lazy="raise",
    )
    chats: Mapped[list["Chat"]] = relationship(
        "Chat",
        back_populates="repository",
        cascade="all, delete-orphan",
        lazy="raise",
    )
    code_graphs: Mapped[list["CodeGraph"]] = relationship(
        "CodeGraph",
        back_populates="repository",
        cascade="all, delete-orphan",
        lazy="raise",
    )
    policies: Mapped[list["Policy"]] = relationship(
        "Policy",
        back_populates="repository",
        cascade="all, delete-orphan",
        lazy="raise",
    )
    generated_tests: Mapped[list["GeneratedTest"]] = relationship(
        "GeneratedTest",
        back_populates="repository",
        cascade="all, delete-orphan",
        lazy="raise",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Repository(id={self.id}, full_name={self.full_name}, indexed={self.indexed_status})>"