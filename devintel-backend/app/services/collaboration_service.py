"""Collaboration service for real-time sessions."""

from typing import Optional
from uuid import UUID

from app.core.logging import get_logger
from app.models.collaboration import CollaborationSession, CollaborationMessage
from app.models.repository import Repository
from app.models.user import User
from app.repositories.collaboration import CollaborationSessionRepository, CollaborationMessageRepository

logger = get_logger(__name__)


class CollaborationService:
    """Service for managing real-time collaboration sessions."""

    def __init__(self, db_session):
        self.db = db_session

    async def create_session(
        self,
        repository: Repository,
        owner: User,
        session_name: str,
    ) -> CollaborationSession:
        """Create a new collaboration session."""
        session_repo = CollaborationSessionRepository(self.db)
        session = await session_repo.create(
            repo_id=repository.id,
            owner_id=owner.id,
            session_name=session_name,
            is_active=True,
            participants_count=1,
        )
        await self.db.commit()
        return session

    async def join_session(
        self,
        session_id: UUID,
    ) -> CollaborationSession:
        """Join an existing session (increment participant count)."""
        session_repo = CollaborationSessionRepository(self.db)
        session = await session_repo.get_by_id(session_id)

        if not session:
            raise ValueError("Session not found")

        session.participants_count += 1
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def leave_session(
        self,
        session_id: UUID,
    ) -> None:
        """Leave a session (decrement participant count)."""
        session_repo = CollaborationSessionRepository(self.db)
        session = await session_repo.get_by_id(session_id)

        if session:
            session.participants_count = max(0, session.participants_count - 1)
            if session.participants_count == 0:
                session.is_active = False
            await self.db.commit()

    async def add_message(
        self,
        session: CollaborationSession,
        user: User,
        message_type: str,
        content: str,
        file_path: Optional[str] = None,
        cursor_line: Optional[int] = None,
        cursor_column: Optional[int] = None,
    ) -> CollaborationMessage:
        """Add a message to a session."""
        msg_repo = CollaborationMessageRepository(self.db)
        message = await msg_repo.create(
            session_id=session.id,
            user_id=user.id,
            message_type=message_type,
            content=content,
            file_path=file_path,
            cursor_line=cursor_line,
            cursor_column=cursor_column,
        )
        await self.db.commit()
        return message

    async def get_session_history(
        self,
        session: CollaborationSession,
        limit: int = 100,
    ) -> list[CollaborationMessage]:
        """Get message history for a session."""
        msg_repo = CollaborationMessageRepository(self.db)
        return await msg_repo.get_by_session(session.id, limit=limit)