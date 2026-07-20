"""Policy repository for database operations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy import Policy
from app.repositories.base import BaseRepository


class PolicyRepository(BaseRepository[Policy]):
    """Repository for policy CRUD operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(Policy, db)

    async def get_by_repo(self, repo_id: UUID, skip: int = 0, limit: int = 100) -> list[Policy]:
        """Get all policies for a repository."""
        result = await self.db.execute(
            select(Policy)
            .where(Policy.repo_id == repo_id)
            .offset(skip)
            .limit(limit)
            .order_by(Policy.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_by_repo(self, repo_id: UUID) -> int:
        """Delete all policies for a repository."""
        from sqlalchemy import delete
        result = await self.db.execute(delete(Policy).where(Policy.repo_id == repo_id))
        await self.db.flush()
        return result.rowcount
