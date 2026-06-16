"""Code migration models for tracking migration projects."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.repository import Repository


class MigrationProject(Base, UUIDMixin, TimestampMixin):
    """Code migration project tracking."""

    __tablename__ = "migration_projects"

    # Foreign keys
    repo_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Migration info
    source_tech: Mapped[str] = mapped_column(String(100), nullable=False)
    target_tech: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Migration plan
    migration_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    migrated_files: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_files: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", backref="migration_projects")

    def __repr__(self) -> str:
        return f"<MigrationProject(id={self.id}, {self.source_tech} -> {self.target_tech})>"


class MigratedFile(Base, UUIDMixin, TimestampMixin):
    """Single migrated file."""

    __tablename__ = "migrated_files"

    # Foreign keys
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("migration_projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    # File info
    original_path: Mapped[str] = mapped_column(String(500), nullable=False)
    migrated_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    # Relationships
    project: Mapped["MigrationProject"] = relationship("MigrationProject", backref="migrated_files")

    def __repr__(self) -> str:
        return f"<MigratedFile(project={self.project_id}, original={self.original_path})>"