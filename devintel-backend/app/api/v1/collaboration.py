"""Collaboration API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_repo_access, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.collaboration import (
    CollaborationMessageRepository,
    CollaborationSessionRepository,
)
from app.repositories.repository import RepositoryRepository
from app.schemas.collaboration import (
    CollaborationHistoryResponse,
    CollaborationMessageResponse,
    CollaborationSessionCreate,
    CollaborationSessionResponse,
)
from app.services.collaboration_service import CollaborationService

router = APIRouter(prefix="/collab", tags=["Collaboration"])


@router.post("/sessions", response_model=CollaborationSessionResponse)
async def create_collaboration_session(
    request: CollaborationSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new collaboration session."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(request.repository_id)

    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db)

    service = CollaborationService(db)
    session = await service.create_session(
        repository=repository,
        owner=current_user,
        session_name=request.session_name,
    )

    return CollaborationSessionResponse.model_validate(session)


@router.get("/sessions/{repository_id}", response_model=CollaborationSessionResponse)
async def get_active_session(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get active collaboration session for a repository."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db)

    session_repo = CollaborationSessionRepository(db)
    session = await session_repo.get_active_by_repo(repository_id)

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active session found")

    return CollaborationSessionResponse.model_validate(session)


@router.get("/sessions/{session_id}/history", response_model=CollaborationHistoryResponse)
async def get_session_history(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get message history for a collaboration session."""
    session_repo = CollaborationSessionRepository(db)
    session = await session_repo.get_by_id(session_id)

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Check repo access
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(session.repo_id)
    await check_repo_access(repository, current_user, db)

    msg_repo = CollaborationMessageRepository(db)
    messages = await msg_repo.get_by_session(session_id)

    return CollaborationHistoryResponse(
        messages=[CollaborationMessageResponse.model_validate(m) for m in messages]
    )
