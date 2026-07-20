"""Policy model for custom code quality rules."""

import enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.repository import Repository


class PolicySeverity(str, enum.Enum):
    """Policy violation severity levels."""

    ERROR = "error"
    WARNING = "warning"


class PolicyRuleType(str, enum.Enum):
    """Policy rule types."""

    MAX_COMPLEXITY = "max_complexity"
    NO_PATTERN = "no_pattern"
    REQUIRE_PATTERN = "require_pattern"
    MAX_FILE_LINES = "max_file_lines"
    REQUIRE_DOCSTRINGS = "require_docstrings"
    CUSTOM_PROMPT = "custom_prompt"


class Policy(Base, UUIDMixin, TimestampMixin):
    """Custom policy rules for code quality enforcement."""

    __tablename__ = "policies"

    # Foreign keys
    repo_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Policy configuration
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="warning",
        server_default="warning",
    )

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="policies")

    def __repr__(self) -> str:
        return f"<Policy(id={self.id}, name={self.name}, type={self.rule_type})>"
