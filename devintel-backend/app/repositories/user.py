"""User repository for database operations."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Repository for User model operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_by_github_id(self, github_id: str) -> Optional[User]:
        """Get user by GitHub ID."""
        result = await self.db.execute(select(User).where(User.github_id == github_id))
        return result.scalars().first()

    async def create_or_update_from_github(
        self,
        github_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        github_token_encrypted: Optional[str] = None,
    ) -> User:
        """Create or update user from GitHub OAuth data."""
        user = await self.get_by_github_id(github_id)

        if user:
            # Update existing user
            user.email = email
            user.name = name
            user.avatar_url = avatar_url
            if github_token_encrypted:
                user.github_access_token_encrypted = github_token_encrypted
        else:
            # Create new user
            user = User(
                github_id=github_id,
                email=email,
                name=name,
                avatar_url=avatar_url,
                github_access_token_encrypted=github_token_encrypted,
            )
            self.db.add(user)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: UUID, **kwargs) -> Optional[User]:
        """Update user fields."""
        user = await self.get_by_id(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            await self.db.commit()
            await self.db.refresh(user)
        return user
