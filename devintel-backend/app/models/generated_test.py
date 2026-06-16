"""Generated tests model for storing test artifacts."""

import enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, Enum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.repository import Repository


class TestStatus(str, enum):
    """Test generation status."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"


class GeneratedTest(Base, UUIDMixin, TimestampMixin):
    """Generated test cases for PR diffs."""

    __tablename__ = "generated_tests"

    # Foreign keys
    repo_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    draft_pr_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # Test info
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    test_content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="generated_tests")

    def __repr__(self) -> str:
        return f"<GeneratedTest(id={self.id}, file={self.file_path}, status={self.status})>"