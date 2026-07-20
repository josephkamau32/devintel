"""Code graph model for storing call relationships."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.embedding import Embedding
    from app.models.repository import Repository


class CodeGraph(Base, UUIDMixin):
    """Stores function call relationships between code chunks."""

    __tablename__ = "code_graph"

    # Repository reference
    repo_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Caller and callee chunk references
    caller_chunk_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("embeddings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    callee_chunk_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("embeddings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Edge type: 'direct_call', 'method_call', 'import', 'inheritance'
    edge_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="direct_call"
    )

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="code_graphs")
    caller: Mapped["Embedding"] = relationship("Embedding", foreign_keys=[caller_chunk_id])
    callee: Mapped["Embedding"] = relationship("Embedding", foreign_keys=[callee_chunk_id])

    def __repr__(self) -> str:
        return f"<CodeGraph(caller={self.caller_chunk_id} -> callee={self.callee_chunk_id}, type={self.edge_type})>"
