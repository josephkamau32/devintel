"""Architecture diagram models for storing Mermaid/C4 diagrams."""

import enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.repository import Repository


class DiagramType(str, enum):
    """Types of architecture diagrams."""

    MERMAID = "mermaid"
    C4_CONTEXT = "c4_context"
    C4_CONTAINER = "c4_container"
    C4_COMPONENT = "c4_component"


class ArchitectureDiagram(Base, UUIDMixin, TimestampMixin):
    """Stored architecture diagrams."""

    __tablename__ = "architecture_diagrams"

    # Foreign keys
    repo_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Diagram info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    diagram_type: Mapped[str] = mapped_column(String(50), nullable=False)
    mermaid_code: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", backref="architecture_diagrams")

    def __repr__(self) -> str:
        return f"<ArchitectureDiagram(id={self.id}, name={self.name}, type={self.diagram_type})>"