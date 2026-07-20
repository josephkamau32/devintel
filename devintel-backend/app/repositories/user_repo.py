from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_github_id(self, github_id: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.github_id == github_id)
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        user = await self.get_by_email(email)
        return user is not None

    async def create_email_user(
        self,
        email: str,
        hashed_password: str,
        full_name: Optional[str] = None,
    ) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            is_verified=False,
        )
        return await self.save(user)

    async def create_github_user(
        self,
        github_id: str,
        github_username: str,
        github_token_encrypted: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> User:
        user = User(
            github_id=github_id,
            github_username=github_username,
            github_token_encrypted=github_token_encrypted,
            email=email.lower() if email else None,
            full_name=full_name,
            avatar_url=avatar_url,
            is_active=True,
            is_verified=True,
        )
        return await self.save(user)

    async def update_github_token(self, user: User, encrypted_token: str) -> User:
        user.github_token_encrypted = encrypted_token
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def link_github_account(
        self,
        user: User,
        github_id: str,
        github_username: str | None,
        encrypted_token: str,
        avatar_url: str | None,
    ) -> User:
        user.github_id = github_id
        user.github_username = github_username
        user.github_token_encrypted = encrypted_token
        user.avatar_url = avatar_url
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_or_create_demo_user(
        self,
        email: str,
        hashed_password: str,
        full_name: str,
    ) -> User:
        """Find the demo user by email, or create one if it doesn't exist."""
        user = await self.get_by_email(email)
        if user is not None:
            return user
        return await self.create_email_user(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
        )

