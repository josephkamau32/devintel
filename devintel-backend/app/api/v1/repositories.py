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
    RepositoryIndexRequest,
    RepositoryIndexResponse,
    RepositoryListResponse,
    RepositoryResponse,
    RepositoryStatusResponse,
)
from app.services.encryption import encryption_service
from app.tasks.indexing import index_repository_task

logger = get_logger(__name__)
router = APIRouter(prefix="/repos", tags=["Repositories"])


def _get_github_token(user: User) -> str:
    """Decrypt and return the user's GitHub access token."""
    if not user.github_access_token_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub account not connected. Please log in with GitHub first.",
        )
    token = encryption_service.decrypt(user.github_access_token_encrypted)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to decrypt GitHub token. Please re-authenticate with GitHub.",
        )
    return token


@router.get("/github")
async def list_github_repositories(
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """Fetch repositories from the user's GitHub account."""
    token = _get_github_token(current_user)

    try:
        github_client = GitHubClient(token)
        repos = await github_client.get_user_repositories(page=page, per_page=per_page)
        return {"repositories": repos, "page": page, "per_page": per_page}
    except Exception as e:
        logger.error(f"Failed to fetch GitHub repositories: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch repositories from GitHub. Please try again.",
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
    request: RepositoryIndexRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger repository indexing."""
    repo_repo = RepositoryRepository(db)
    
    # Get repository
    repository = await repo_repo.get_by_id(request.repository_id)
    
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
    
    # Indexing mutex: prevent concurrent indexing of the same repo
    if 0 < repository.indexing_progress < 100:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Repository is already being indexed. Please wait for the current indexing to complete.",
        )
    
    # Decrypt GitHub token for cloning private repos
    access_token = ""
    if current_user.github_access_token_encrypted:
        decrypted = encryption_service.decrypt(current_user.github_access_token_encrypted)
        if decrypted:
            access_token = decrypted
    
    # Trigger background task
    task = index_repository_task.delay(
        repo_id=str(request.repository_id),
        clone_url=repository.url,
        access_token=access_token,
    )
    
    return RepositoryIndexResponse(
        task_id=task.id,
        message="Indexing started",
        repository_id=request.repository_id,
    )


@router.get("/{repository_id}/status", response_model=RepositoryStatusResponse)
async def get_repository_status(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get repository indexing status (lightweight polling endpoint)."""
    repo_repo = RepositoryRepository(db)
    
    repository = await repo_repo.get_by_id(repository_id)
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )
        
    if repository.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this repository",
        )
    
    return RepositoryStatusResponse(
        id=repository.id,
        indexed_status=repository.indexed_status,
        indexing_progress=repository.indexing_progress,
        indexing_error=repository.indexing_error,
    )


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a repository by ID."""
    repo_repo = RepositoryRepository(db)
    
    repository = await repo_repo.get_by_id(repository_id)
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )
        
    if repository.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this repository",
        )
        
    return RepositoryResponse.model_validate(repository)


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
