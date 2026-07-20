from uuid import uuid4

from sqlalchemy import Boolean, Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, index=True, nullable=True)
    # DB column is "name"; exposed as 'full_name' in Python for clarity
    full_name = Column("name", String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    hashed_password = Column(String(255), nullable=True)

    # GitHub OAuth fields
    github_id = Column(String(255), unique=True, index=True, nullable=True)
    github_username = Column("username", String(100), nullable=True)
    github_token_encrypted = Column("github_access_token_encrypted", Text, nullable=True)

    # Account status
    is_active = Column(Boolean, default=True, nullable=False, server_default="true")
    is_verified = Column(Boolean, default=False, nullable=False, server_default="false")

    repositories = relationship("Repository", back_populates="user", cascade="all, delete-orphan")
    organizations = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="user", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    def __repr__(self):
        return f"<User id={self.id} email={self.email} github={self.github_username}>"
