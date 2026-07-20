"""Git history repositories."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.git_history import FileBlame, GitHistory
from app.repositories.base import BaseRepository


class GitHistoryRepository(BaseRepository[GitHistory]):
    """Repository for GitHistory model."""

    def __init__(self, db: AsyncSession):
        super().__init__(GitHistory, db)

    async def get_by_repo_and_sha(self, repo_id: UUID, sha: str) -> Optional[GitHistory]:
        """Get commit by repo and SHA."""
        result = await self.db.execute(
            select(GitHistory).where(
                GitHistory.repo_id == repo_id,
                GitHistory.sha == sha,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_repo(self, repo_id: UUID, skip: int = 0, limit: int = 50) -> list[GitHistory]:
        """Get commits for a repository, most recent first."""
        result = await self.db.execute(
            select(GitHistory)
            .where(GitHistory.repo_id == repo_id)
            .offset(skip)
            .limit(limit)
            .order_by(GitHistory.committed_at.desc().nullslast())
        )
        return list(result.scalars().all())


class FileBlameRepository(BaseRepository[FileBlame]):
    """Repository for FileBlame model."""

    def __init__(self, db: AsyncSession):
        super().__init__(FileBlame, db)

    async def get_by_repo_and_file(
        self, repo_id: UUID, file_path: str, limit: int = 1000
    ) -> list[FileBlame]:
        """Get blame entries for a file."""
        result = await self.db.execute(
            select(FileBlame)
            .where(FileBlame.repo_id == repo_id, FileBlame.file_path == file_path)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_repo_file_line(
        self, repo_id: UUID, file_path: str, line_number: int
    ) -> Optional[FileBlame]:
        """Get blame entry for a specific line."""
        result = await self.db.execute(
            select(FileBlame).where(
                FileBlame.repo_id == repo_id,
                FileBlame.file_path == file_path,
                FileBlame.line_number == line_number,
            )
        )
        return result.scalar_one_or_none()

    async def delete_by_repo(self, repo_id: UUID) -> int:
        """Delete all blame entries for a repository."""
        from sqlalchemy import delete
        result = await self.db.execute(delete(FileBlame).where(FileBlame.repo_id == repo_id))
        await self.db.flush()
        return result.rowcount
