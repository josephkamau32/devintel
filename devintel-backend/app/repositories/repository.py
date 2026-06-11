"""Repository repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import Repository
from app.repositories.base import BaseRepository


class RepositoryRepository(BaseRepository[Repository]):
    """Repository repository."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        super().__init__(Repository, db)

    async def get_by_user(
        self, user_id: UUID, org_id: UUID | None = None, skip: int = 0, limit: int = 100
    ) -> list[Repository]:
        """Get repositories by user ID or organization ID."""
        stmt = select(Repository)
        if org_id:
            stmt = stmt.where(Repository.org_id == org_id)
        else:
            stmt = stmt.where(Repository.user_id == user_id, Repository.org_id.is_(None))

        result = await self.db.execute(
            stmt.offset(skip)
            .limit(limit)
            .order_by(Repository.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_full_name(
        self,
        full_name: str,
        user_id: UUID | None = None,
        org_id: UUID | None = None,
    ) -> Repository | None:
        """Get repository by full name scoped to user or org (for duplicate detection)."""
        stmt = select(Repository).where(Repository.full_name == full_name)
        if org_id:
            stmt = stmt.where(Repository.org_id == org_id)
        else:
            stmt = stmt.where(Repository.user_id == user_id, Repository.org_id.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_user(self, user_id: UUID, org_id: UUID | None = None) -> int:
        """Count repositories for a user or organization."""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(Repository)
        if org_id:
            stmt = stmt.where(Repository.org_id == org_id)
        else:
            stmt = stmt.where(Repository.user_id == user_id, Repository.org_id.is_(None))

        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_full_name_any(self, full_name: str) -> Repository | None:
        """Get a repository by full_name without user scope.

        Used by the webhook handler which has no authenticated user context —
        returns the first connected repo matching the GitHub full name.
        """
        stmt = select(Repository).where(Repository.full_name == full_name).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

