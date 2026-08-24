import enum
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class IndexingStatus(str, enum.Enum):
    PENDING = "pending"
    INDEXING = "indexing"
    COMPLETE = "complete"
    FAILED = "failed"


class Repository(Base, TimestampMixin):
    __tablename__ = "repositories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # DB column is "org_id"; exposed as 'organization_id' in Python for clarity
    organization_id = Column("org_id", UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)

    full_name = Column(String(255), nullable=False)
    repo_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(512), nullable=True)
    stars = Column(Integer, default=0)
    language = Column(String(100), nullable=True)
    default_branch = Column(String(100), default="main")

    indexing_status = Column(String(20), nullable=False, default="pending")

    indexing_progress = Column(Integer, default=0)
    indexing_error = Column(Text, nullable=True)
    last_indexed_at = Column(DateTime(timezone=True), nullable=True)
    last_indexed_commit_sha = Column(String(40), nullable=True)
    indexing_mode = Column(String(50), nullable=True)

    user = relationship("User", back_populates="repositories")
    organization = relationship("Organization", back_populates="repositories")
    chunks = relationship("CodeChunk", back_populates="repository", cascade="all, delete-orphan")
    embeddings = relationship("Embedding", back_populates="repository", cascade="all, delete-orphan")
    policies = relationship("Policy", back_populates="repository", cascade="all, delete-orphan")
    generated_tests = relationship("GeneratedTest", back_populates="repository", cascade="all, delete-orphan")
    code_graphs = relationship("CodeGraph", back_populates="repository", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="repository", cascade="all, delete-orphan")
    indexing_jobs = relationship("IndexingJob", back_populates="repository", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Repository id={self.id} full_name={self.full_name}>"
