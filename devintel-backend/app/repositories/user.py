"""User repository."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User repository."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        super().__init__(User, db)

    async def get_by_github_id(self, github_id: str) -> Optional[User]:
        """Get user by GitHub ID."""
        result = await self.db.execute(
            select(User).where(User.github_id == github_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update_from_github(
        self,
        github_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> User:
        """Create or update user from GitHub OAuth data."""
        user = await self.get_by_github_id(github_id)

        if user:
            # Update existing user
            user.email = email or user.email
            user.name = name or user.name
            user.avatar_url = avatar_url or user.avatar_url
            await self.db.flush()
            await self.db.refresh(user)
        else:
            # Create new user
            user = await self.create(
                github_id=github_id,
                email=email,
                name=name,
                avatar_url=avatar_url,
            )

        return user
