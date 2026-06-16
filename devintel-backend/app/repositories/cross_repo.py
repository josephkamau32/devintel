"""Cross-repository knowledge repository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cross_repo import CrossRepoKnowledge
from app.repositories.base import BaseRepository


class CrossRepoKnowledgeRepository(BaseRepository[CrossRepoKnowledge]):
    """Repository for CrossRepoKnowledge model."""

    def __init__(self, db: AsyncSession):
        super().__init__(CrossRepoKnowledge, db)

    async def get_similar_patterns(
        self,
        repo_id: UUID,
        pattern_type: Optional[str] = None,
        min_score: float = 0.7,
        limit: int = 20,
    ) -> list[CrossRepoKnowledge]:
        """Get similar patterns from other repositories."""
        query = (
            select(CrossRepoKnowledge)
            .where(
                CrossRepoKnowledge.repo_id == repo_id,
                CrossRepoKnowledge.similarity_score >= min_score,
            )
        )
        if pattern_type:
            query = query.where(CrossRepoKnowledge.pattern_type == pattern_type)

        query = query.order_by(CrossRepoKnowledge.similarity_score.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_pattern_key(
        self,
        repo_id: UUID,
        pattern_type: str,
        pattern_key: str,
    ) -> Optional[CrossRepoKnowledge]:
        """Get a specific knowledge entry."""
        result = await self.db.execute(
            select(CrossRepoKnowledge).where(
                CrossRepoKnowledge.repo_id == repo_id,
                CrossRepoKnowledge.pattern_type == pattern_type,
                CrossRepoKnowledge.pattern_key == pattern_key,
            )
        )
        return result.scalar_one_or_none()

    async def delete_by_repo(self, repo_id: UUID) -> int:
        """Delete all cross-repo knowledge for a repository."""
        result = await self.db.execute(
            delete(CrossRepoKnowledge).where(
                (CrossRepoKnowledge.repo_id == repo_id) | (CrossRepoKnowledge.reference_repo_id == repo_id)
            )
        )
        await self.db.flush()
        return result.rowcount