"""Code migration repository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.migration import MigratedFile, MigrationProject
from app.repositories.base import BaseRepository


class MigrationProjectRepository(BaseRepository[MigrationProject]):
    """Repository for MigrationProject model."""

    def __init__(self, db: AsyncSession):
        super().__init__(MigrationProject, db)

    async def get_by_repo(self, repo_id: UUID) -> list[MigrationProject]:
        """Get all migration projects for a repository."""
        result = await self.db.execute(
            select(MigrationProject)
            .where(MigrationProject.repo_id == repo_id)
            .order_by(MigrationProject.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_active(self, repo_id: UUID) -> Optional[MigrationProject]:
        """Get active migration project for a repository."""
        result = await self.db.execute(
            select(MigrationProject)
            .where(
                MigrationProject.repo_id == repo_id,
                MigrationProject.status != "completed",
            )
            .order_by(MigrationProject.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_progress(self, project_id: UUID, progress: int, status: Optional[str] = None) -> None:
        """Update migration progress."""
        values = {"progress_percent": progress}
        if status:
            values["status"] = status
        await self.db.execute(
            update(MigrationProject)
            .where(MigrationProject.id == project_id)
            .values(**values)
        )
        await self.db.flush()


class MigratedFileRepository(BaseRepository[MigratedFile]):
    """Repository for MigratedFile model."""

    def __init__(self, db: AsyncSession):
        super().__init__(MigratedFile, db)

    async def get_by_project(self, project_id: UUID) -> list[MigratedFile]:
        """Get all migrated files for a project."""
        result = await self.db.execute(
            select(MigratedFile)
            .where(MigratedFile.project_id == project_id)
            .order_by(MigratedFile.created_at)
        )
        return list(result.scalars().all())

    async def get_by_project_and_path(self, project_id: UUID, original_path: str) -> Optional[MigratedFile]:
        """Get a specific migrated file."""
        result = await self.db.execute(
            select(MigratedFile)
            .where(
                MigratedFile.project_id == project_id,
                MigratedFile.original_path == original_path,
            )
        )
        return result.scalar_one_or_none()
