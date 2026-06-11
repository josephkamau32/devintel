"""Code Health repository — CRUD operations for CodeHealth records."""

from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_health import CodeHealth
from app.repositories.base import BaseRepository


class CodeHealthRepository(BaseRepository[CodeHealth]):
    """Repository for CodeHealth records."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(CodeHealth, db)

    async def get_by_repo(self, repo_id: UUID) -> Optional[CodeHealth]:
        """Get the latest health record for a repository."""
        result = await self.db.execute(
            select(CodeHealth).where(CodeHealth.repo_id == repo_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, repo_id: UUID, data: dict) -> CodeHealth:
        """
        Insert or update the code health record for a repository.
        Uses PostgreSQL's ON CONFLICT DO UPDATE for atomic upsert.
        """
        data["repo_id"] = repo_id
        data["computed_at"] = datetime.now(UTC)

        stmt = (
            pg_insert(CodeHealth)
            .values(**data)
            .on_conflict_do_update(
                index_elements=["repo_id"],
                set_={k: v for k, v in data.items() if k != "repo_id"},
            )
            .returning(CodeHealth)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        record = result.scalar_one()
        await self.db.refresh(record)
        return record
