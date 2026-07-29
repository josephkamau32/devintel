"""Repository management routes."""

import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_repo_access, get_current_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.integrations.github_client import GitHubClient
from app.models.user import User
from app.repositories.embedding import EmbeddingRepository
from app.repositories.repository import RepositoryRepository
from app.schemas.pr_review import PullRequestListResponse, PullRequestResponse
from app.schemas.repository import (
    IndexingStatusResponse,
    RepositoryCreate,
    RepositoryIndexRequest,
    RepositoryIndexResponse,
    RepositoryListResponse,
    RepositoryResponse,
    SearchResponse,
    SearchResult,
)
from app.services.embedding import EmbeddingService
from app.services.encryption import encryption_service
from app.tasks.indexing import index_repository_task

logger = get_logger(__name__)
router = APIRouter(prefix="/repos", tags=["Repositories"])


@router.get("/{repository_id}/search", response_model=SearchResponse)
async def search_repository(
    repository_id: uuid.UUID,
    q: str = Query(..., min_length=1, max_length=500),
    top_k: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Semantic search across indexed code in a repository."""
    # Check access
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    await check_repo_access(repository, current_user, db)

    if not repository.indexing_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository not indexed yet",
        )

    # Generate query embedding
    embedding_service = EmbeddingService()
    query_embedding = await embedding_service.generate_embedding(q)

    # Search
    embedding_repo = EmbeddingRepository(db)
    results = await embedding_repo.vector_search(
        repo_id=repository_id,
        query_embedding=query_embedding,
        top_k=top_k,
    )

    # Convert results
    search_results = [
        SearchResult(
            file_path=emb.file_path,
            chunk_text=emb.chunk_text,
            similarity=sim,
            chunk_index=emb.chunk_index,
        )
        for emb, sim in results
    ]

    return SearchResponse(
        results=search_results,
        repository_id=repository_id,
        query=q,
    )


def _get_github_token(user: User) -> str:
    """Decrypt and return the user's GitHub access token."""
    if not user.github_token_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub account not connected. Please log in with GitHub first.",
        )
    token = encryption_service.decrypt(user.github_token_encrypted)
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
    """List repositories (personal)."""
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

    # Prevent duplicate repositories for the same user
    existing = await repo_repo.get_by_full_name(
        full_name=repo_data.full_name,
        user_id=current_user.id,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Repository '{repo_data.full_name}' is already connected to this account.",
        )

    # Create repository
    repository = await repo_repo.create(
        user_id=current_user.id,
        repo_name=repo_data.repo_name,
        full_name=repo_data.full_name,
        description=repo_data.description,
        url=repo_data.url,
        stars=repo_data.stars,
        language=repo_data.language,
        default_branch=repo_data.default_branch,
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

    await check_repo_access(repository, current_user, db)

    # Indexing mutex: prevent concurrent indexing of the same repo
    if 0 < repository.indexing_progress < 100:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Repository is already being indexed. Please wait for the current indexing to complete.",
        )

    # Decrypt GitHub token for cloning private repos
    access_token = ""
    if current_user.github_token_encrypted:
        decrypted = encryption_service.decrypt(current_user.github_token_encrypted)
        if decrypted:
            access_token = decrypted

    # Trigger background task
    task_id = str(uuid.uuid4())
    asyncio.create_task(
        index_repository_task(
            repo_id=str(request.repository_id),
            clone_url=repository.url,
            access_token=access_token,
        )
    )

    return RepositoryIndexResponse(
        task_id=task_id,
        message="Indexing started",
        repository_id=request.repository_id,
    )


@router.get("/{repository_id}/pulls", response_model=PullRequestListResponse)
async def list_repository_pulls(
    repository_id: uuid.UUID,
    state: str = Query("open", pattern="^(open|closed|all)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List pull requests for a repository."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    await check_repo_access(repository, current_user, db)

    token = _get_github_token(current_user)
    github_client = GitHubClient(token)

    try:
        pulls = await github_client.get_repository_pull_requests(
            full_name=repository.full_name,
            state=state,
            page=page,
            per_page=per_page,
        )
        return PullRequestListResponse(
            pulls=[PullRequestResponse(**p) for p in pulls],
            repository_id=repository_id,
        )
    except Exception as e:
        logger.error(f"Failed to fetch PRs for {repository.full_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch pull requests from GitHub",
        )


@router.get("/{repository_id}/pulls/{pr_number}/diff")
async def get_pull_request_diff(
    repository_id: uuid.UUID,
    pr_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the unified diff for a pull request.

    Returns raw patch text so the frontend can render a syntax-highlighted diff.
    """
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    await check_repo_access(repository, current_user, db)

    token = _get_github_token(current_user)
    github_client = GitHubClient(token)

    try:
        diff_text = await github_client.get_pull_request_diff(
            full_name=repository.full_name,
            pr_number=pr_number,
        )
        return {"diff": diff_text, "pr_number": pr_number, "repository": repository.full_name}
    except Exception as e:
        logger.error(f"Failed to fetch diff for PR #{pr_number} in {repository.full_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch pull request diff from GitHub",
        )


@router.get("/{repository_id}/status", response_model=IndexingStatusResponse)
async def get_repository_status(
    repository_id: uuid.UUID,
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

    await check_repo_access(repository, current_user, db)

    return IndexingStatusResponse(
        id=repository.id,
        indexed_status=repository.indexing_status,
        indexing_progress=repository.indexing_progress,
        indexing_error=repository.indexing_error,
        last_indexed_at=repository.last_indexed_at,
        last_indexed_commit_sha=repository.last_indexed_commit_sha,
        indexing_mode=repository.indexing_mode,
    )


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(
    repository_id: uuid.UUID,
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
    repository_id: uuid.UUID,
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

    # Only owners/admins can delete org repos; personal repos require ownership
    await check_repo_access(repository, current_user, db, write_access=True)

    # Delete repository (embeddings will cascade)
    await repo_repo.delete(repository_id)

    return {"message": "Repository deleted successfully"}
