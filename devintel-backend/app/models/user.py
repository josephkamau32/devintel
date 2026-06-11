"""User model."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.analytics import Analytics
    from app.models.chat import Chat
    from app.models.organization import OrganizationMember
    from app.models.repository import Repository


class User(Base, UUIDMixin, TimestampMixin):
    """User model for authentication via GitHub OAuth."""

    __tablename__ = "users"

    # Authentication fields
    github_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    github_access_token_encrypted: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Profile fields
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # JWT Refresh Token
    refresh_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    repositories: Mapped[list["Repository"]] = relationship(
        "Repository",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="raise",
    )
    chats: Mapped[list["Chat"]] = relationship(
        "Chat",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="raise",
    )
    analytics: Mapped[Optional["Analytics"]] = relationship(
        "Analytics",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="raise",
    )
    organizations: Mapped[list["OrganizationMember"]] = relationship(
        "OrganizationMember",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="raise",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, github_id={self.github_id}, email={self.email})>"
