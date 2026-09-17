import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.chat import Chat
    from app.models.code_chunk import CodeChunk
    from app.models.code_graph import CodeGraph
    from app.models.embedding import Embedding
    from app.models.generated_test import GeneratedTest
    from app.models.indexing_job import IndexingJob
    from app.models.organization import Organization
    from app.models.policy import Policy
    from app.models.user import User


class IndexingStatus(str, enum.Enum):
    PENDING = "pending"
    INDEXING = "indexing"
    COMPLETE = "complete"
    FAILED = "failed"


class Repository(Base, TimestampMixin):
    __tablename__ = "repositories"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # DB column is "org_id"; exposed as 'organization_id' in Python for clarity
    organization_id: Mapped[Optional[UUID]] = mapped_column("org_id", PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    repo_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    stars: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    language: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    default_branch: Mapped[Optional[str]] = mapped_column(String(100), default="main")

    indexing_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    indexing_progress: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    indexing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_indexed_commit_sha: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    indexing_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="full", server_default="full")

    user: Mapped["User"] = relationship("User", back_populates="repositories")
    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="repositories")
    chunks: Mapped[list["CodeChunk"]] = relationship("CodeChunk", back_populates="repository", cascade="all, delete-orphan")
    embeddings: Mapped[list["Embedding"]] = relationship("Embedding", back_populates="repository", cascade="all, delete-orphan")
    policies: Mapped[list["Policy"]] = relationship("Policy", back_populates="repository", cascade="all, delete-orphan")
    generated_tests: Mapped[list["GeneratedTest"]] = relationship("GeneratedTest", back_populates="repository", cascade="all, delete-orphan")
    code_graphs: Mapped[list["CodeGraph"]] = relationship("CodeGraph", back_populates="repository", cascade="all, delete-orphan")
    chats: Mapped[list["Chat"]] = relationship("Chat", back_populates="repository", cascade="all, delete-orphan")
    indexing_jobs: Mapped[list["IndexingJob"]] = relationship("IndexingJob", back_populates="repository", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Repository id={self.id} full_name={self.full_name}>"

