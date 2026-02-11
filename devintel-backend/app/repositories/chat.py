"""Chat repository."""

from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.repositories.base import BaseRepository


class ChatRepository(BaseRepository[Chat]):
    """Chat repository."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        super().__init__(Chat, db)

    async def get_by_user_and_repo(
        self,
        user_id: UUID,
        repo_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Chat]:
        """Get chat history for a user and repository."""
        result = await self.db.execute(
            select(Chat)
            .where(Chat.user_id == user_id, Chat.repo_id == repo_id)
            .offset(skip)
            .limit(limit)
            .order_by(Chat.created_at.desc())
        )
        return list(result.scalars().all())
