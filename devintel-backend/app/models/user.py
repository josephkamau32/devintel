from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analytics import Analytics
    from app.models.chat import Chat
    from app.models.organization import OrganizationMember
    from app.models.repository import Repository


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    # DB column is "name"; exposed as 'full_name' in Python for clarity
    full_name: Mapped[Optional[str]] = mapped_column("name", String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # GitHub OAuth fields
    github_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    github_username: Mapped[Optional[str]] = mapped_column("username", String(100), nullable=True)
    github_token_encrypted: Mapped[Optional[str]] = mapped_column("github_access_token_encrypted", Text, nullable=True)

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default="true")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")

    repositories: Mapped[list["Repository"]] = relationship("Repository", back_populates="user", cascade="all, delete-orphan")
    organizations: Mapped[list["OrganizationMember"]] = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")
    analytics: Mapped[list["Analytics"]] = relationship("Analytics", back_populates="user", cascade="all, delete-orphan")
    chats: Mapped[list["Chat"]] = relationship("Chat", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} github={self.github_username}>"

