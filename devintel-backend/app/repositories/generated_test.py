"""Generated test repository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generated_test import GeneratedTest
from app.repositories.base import BaseRepository


class GeneratedTestRepository(BaseRepository[GeneratedTest]):
    """Repository for generated test CRUD operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(GeneratedTest, db)

    async def get_by_repo(self, repo_id: UUID, skip: int = 0, limit: int = 100) -> list[GeneratedTest]:
        """Get all tests for a repository."""
        result = await self.db.execute(
            select(GeneratedTest)
            .where(GeneratedTest.repo_id == repo_id)
            .offset(skip)
            .limit(limit)
            .order_by(GeneratedTest.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_by_repo(self, repo_id: UUID) -> int:
        """Delete all generated tests for a repository."""
        result = await self.db.execute(delete(GeneratedTest).where(GeneratedTest.repo_id == repo_id))
        await self.db.flush()
        return result.rowcount