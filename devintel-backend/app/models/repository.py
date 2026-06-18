from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
import enum
from app.models.base import Base, TimestampMixin


class IndexingStatus(str, enum.Enum):
    PENDING = "pending"
    INDEXING = "indexing"
    COMPLETE = "complete"
    FAILED = "failed"


class Repository(Base, TimestampMixin):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    github_repo_id = Column(String(100), nullable=False)
    full_name = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    default_branch = Column(String(100), default="main")
    is_private = Column(Boolean, default=False)
    indexing_status = Column(Enum(IndexingStatus), default=IndexingStatus.PENDING)
    last_indexed_commit = Column(String(40), nullable=True)

    user = relationship("User", back_populates="repositories")
    chunks = relationship("CodeChunk", back_populates="repository", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Repository id={self.id} full_name={self.full_name}>"
