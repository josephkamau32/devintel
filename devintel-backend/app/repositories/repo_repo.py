from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import Repository
from app.repositories.base_repo import BaseRepository


class RepositoryRepository(BaseRepository[Repository]):
    def __init__(self, db: AsyncSession):
        super().__init__(Repository, db)

    async def list_by_user(self, user_id: int) -> list[Repository]:
        result = await self.db.execute(
            select(Repository).where(Repository.user_id == user_id).order_by(Repository.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_github_repo_id(self, github_repo_id: str) -> Optional[Repository]:
        result = await self.db.execute(
            select(Repository).where(Repository.github_repo_id == github_repo_id)
        )
        return result.scalar_one_or_none()

    async def create_repository(
        self,
        user_id: int,
        github_repo_id: str,
        full_name: str,
        name: str,
        description: Optional[str] = None,
        default_branch: str = "main",
        is_private: bool = False,
    ) -> Repository:
        repository = Repository(
            user_id=user_id,
            github_repo_id=github_repo_id,
            full_name=full_name,
            name=name,
            description=description,
            default_branch=default_branch,
            is_private=is_private,
        )
        return await self.save(repository)
