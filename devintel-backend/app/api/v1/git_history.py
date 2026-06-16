"""Git history API routes."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_repo_access, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.git_history import GitHistoryRepository, FileBlameRepository
from app.repositories.repository import RepositoryRepository
from app.schemas.git_history import (
    BlameContextResponse,
    BlameRequest,
    FileBlameResponse,
    GitHistoryResponse,
)
from app.services.git_history_service import GitHistoryService
from app.services.encryption import encryption_service

router = APIRouter(prefix="/git", tags=["Git History"])


@router.post("/blame", response_model=list[FileBlameResponse])
async def get_file_blame(
    request: BlameRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get blame information for a file."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(request.repository_id)

    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db)

    if not current_user.github_access_token_encrypted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub token not configured")

    token = encryption_service.decrypt(current_user.github_access_token_encrypted)
    git_service = GitHistoryService(db, github_token=token)

    try:
        blame_records = await git_service.get_blame_for_file(
            repository=repository,
            file_path=request.file_path,
            ref=request.ref,
        )
        return [FileBlameResponse.model_validate(r) for r in blame_records]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/history/{repository_id}", response_model=list[GitHistoryResponse])
async def get_git_history(
    repository_id: UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get git commit history for a repository."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db)

    git_repo = GitHistoryRepository(db)
    commits = await git_repo.get_by_repo(repository_id, limit=limit)
    return [GitHistoryResponse.model_validate(c) for c in commits]


@router.post("/blame/context", response_model=BlameContextResponse)
async def get_blame_context(
    request: BlameRequest,
    line_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get git history context for a specific line."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(request.repository_id)

    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db)

    git_service = GitHistoryService(db)
    context = await git_service.get_changes_for_line(
        repository=repository,
        file_path=request.file_path,
        line_number=line_number,
    )

    if not context:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blame context not found")

    return BlameContextResponse(**context)