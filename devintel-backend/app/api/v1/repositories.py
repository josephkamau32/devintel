"""Repository management routes."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.integrations.github_client import GitHubClient
from app.models.user import User
from app.repositories.repository import RepositoryRepository
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryIndexResponse,
    RepositoryListResponse,
    RepositoryResponse,
)
from app.tasks.indexing import index_repository_task

logger = get_logger(__name__)
router = APIRouter(prefix="/repos", tags=["Repositories"])


@router.get("/github")
async def list_github_repositories(
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """Fetch repositories from GitHub API."""
    # Note: In production, store GitHub access token securely
    # For now, this requires the user to have connected their GitHub account
    # You would need to store the GitHub access token in the database
    
    # Placeholder - implement token storage
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="GitHub token storage not yet implemented. Use /repos to list indexed repos.",
    )


@router.get("", response_model=RepositoryListResponse)
async def list_repositories(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's repositories."""
    repo_repo = RepositoryRepository(db)
    
    repositories = await repo_repo.get_by_user(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    
    total = await repo_repo.count_by_user(current_user.id)
    
    return RepositoryListResponse(
        repositories=[RepositoryResponse.model_validate(repo) for repo in repositories],
        total=total,
    )


@router.post("", response_model=RepositoryResponse)
async def create_repository(
    repo_data: RepositoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a repository."""
    repo_repo = RepositoryRepository(db)
    
    # Check if repository already exists
    existing = await repo_repo.get_by_full_name(current_user.id, repo_data.full_name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository already added",
        )
    
    # Create repository
    repository = await repo_repo.create(
        user_id=current_user.id,
        **repo_data.model_dump(),
    )
    
    return RepositoryResponse.model_validate(repository)


@router.post("/index", response_model=RepositoryIndexResponse)
async def index_repository(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger repository indexing."""
    repo_repo = RepositoryRepository(db)
    
    # Get repository
    repository = await repo_repo.get_by_id(repository_id)
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )
    
    if repository.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to index this repository",
        )
    
    # Trigger background task
    task = index_repository_task.delay(
        repo_id=str(repository_id),
        clone_url=repository.url,  # Assuming url contains clone URL
        access_token="",  # Implement token storage
    )
    
    return RepositoryIndexResponse(
        task_id=task.id,
        message="Indexing started",
        repository_id=repository_id,
    )


@router.delete("/{repository_id}")
async def delete_repository(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a repository."""
    repo_repo = RepositoryRepository(db)
    
    # Get repository
    repository = await repo_repo.get_by_id(repository_id)
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )
    
    if repository.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this repository",
        )
    
    # Delete repository (embeddings will cascade)
    await repo_repo.delete(repository_id)
    
    return {"message": "Repository deleted successfully"}
