"""Architecture diagram repository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.architecture import ArchitectureDiagram
from app.repositories.base import BaseRepository


class ArchitectureDiagramRepository(BaseRepository[ArchitectureDiagram]):
    """Repository for ArchitectureDiagram model."""

    def __init__(self, db: AsyncSession):
        super().__init__(ArchitectureDiagram, db)

    async def get_by_repo(self, repo_id: UUID, limit: int = 20) -> list[ArchitectureDiagram]:
        """Get all diagrams for a repository."""
        result = await self.db.execute(
            select(ArchitectureDiagram)
            .where(ArchitectureDiagram.repo_id == repo_id)
            .limit(limit)
            .order_by(ArchitectureDiagram.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_latest_by_repo(
        self, repo_id: UUID, diagram_type: str
    ) -> Optional[ArchitectureDiagram]:
        """Get latest diagram of given type for a repository."""
        result = await self.db.execute(
            select(ArchitectureDiagram)
            .where(
                ArchitectureDiagram.repo_id == repo_id,
                ArchitectureDiagram.diagram_type == diagram_type,
            )
            .order_by(ArchitectureDiagram.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def delete_by_repo(self, repo_id: UUID) -> int:
        """Delete all diagrams for a repository."""
        from sqlalchemy import delete
        result = await self.db.execute(
            delete(ArchitectureDiagram).where(ArchitectureDiagram.repo_id == repo_id)
        )
        await self.db.flush()
        return result.rowcount