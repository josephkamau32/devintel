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
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Repository]:
        """Get repositories by user ID."""
        stmt = select(Repository)
        stmt = stmt.where(Repository.user_id == user_id)

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
    ) -> Repository | None:
        """Get repository by full name scoped to user (for duplicate detection)."""
        stmt = select(Repository).where(Repository.full_name == full_name)
        stmt = stmt.where(Repository.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_user(self, user_id: UUID) -> int:
        """Count repositories for a user."""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(Repository)
        stmt = stmt.where(Repository.user_id == user_id)

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

