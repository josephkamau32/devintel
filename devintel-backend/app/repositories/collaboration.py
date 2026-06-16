"""Collaboration repositories."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collaboration import CollaborationSession, CollaborationMessage
from app.repositories.base import BaseRepository


class CollaborationSessionRepository(BaseRepository[CollaborationSession]):
    """Repository for CollaborationSession model."""

    def __init__(self, db: AsyncSession):
        super().__init__(CollaborationSession, db)

    async def get_active_by_repo(self, repo_id: UUID) -> Optional[CollaborationSession]:
        """Get active session for a repository."""
        result = await self.db.execute(
            select(CollaborationSession)
            .where(
                CollaborationSession.repo_id == repo_id,
                CollaborationSession.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_owner(self, owner_id: UUID, limit: int = 20) -> list[CollaborationSession]:
        """Get sessions owned by a user."""
        result = await self.db.execute(
            select(CollaborationSession)
            .where(CollaborationSession.owner_id == owner_id)
            .order_by(CollaborationSession.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class CollaborationMessageRepository(BaseRepository[CollaborationMessage]):
    """Repository for CollaborationMessage model."""

    def __init__(self, db: AsyncSession):
        super().__init__(CollaborationMessage, db)

    async def get_by_session(self, session_id: UUID, limit: int = 100) -> list[CollaborationMessage]:
        """Get messages for a session."""
        result = await self.db.execute(
            select(CollaborationMessage)
            .where(CollaborationMessage.session_id == session_id)
            .order_by(CollaborationMessage.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(
        self,
        session_id: UUID,
        since_id: Optional[UUID] = None,
        limit: int = 50,
    ) -> list[CollaborationMessage]:
        """Get recent messages since an ID."""
        query = select(CollaborationMessage).where(
            CollaborationMessage.session_id == session_id
        )
        if since_id:
            query = query.where(CollaborationMessage.id > since_id)
        query = query.order_by(CollaborationMessage.created_at).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())