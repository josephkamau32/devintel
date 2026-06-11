"""Code Health API endpoint — GET /repos/{id}/health."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_repo_access, get_current_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.repositories.code_health import CodeHealthRepository
from app.repositories.embedding import EmbeddingRepository
from app.repositories.repository import RepositoryRepository

logger = get_logger(__name__)
router = APIRouter(prefix="/repos", tags=["Code Health"])


@router.get("/{repository_id}/health")
async def get_code_health(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return the latest code health analysis for a repository.

    If no analysis exists yet (e.g. repo was just indexed), returns 404.
    The analysis is automatically triggered after indexing completes.

    Clients can call POST /{id}/health/refresh to manually trigger re-analysis.
    """
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    await check_repo_access(repository, current_user, db)

    if not repository.indexed_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository is not indexed yet. Index it first to generate a health report.",
        )

    health_repo = CodeHealthRepository(db)
    record = await health_repo.get_by_repo(repository_id)

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health report not yet available. It will be computed automatically after indexing.",
        )

    import json
    return {
        "id": str(record.id),
        "repo_id": str(record.repo_id),
        "repo_name": repository.full_name,
        "overall_score": round(record.overall_score, 1),
        "dimensions": {
            "complexity": round(record.complexity_score, 1),
            "documentation": round(record.documentation_score, 1),
            "maintainability": round(record.maintainability_score, 1),
            "test_coverage": round(record.test_coverage_score, 1),
            "security": round(record.security_score, 1),
        },
        "summary": record.summary,
        "top_issues": json.loads(record.top_issues or "[]"),
        "recommendations": json.loads(record.recommendations or "[]"),
        "language_detected": record.language_detected,
        "files_analyzed": record.files_analyzed,
        "computed_at": record.computed_at.isoformat() if record.computed_at else None,
    }


@router.post("/{repository_id}/health/refresh", status_code=status.HTTP_202_ACCEPTED)
async def refresh_code_health(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a code health re-analysis for a repository."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    await check_repo_access(repository, current_user, db)

    if not repository.indexed_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository must be indexed before running health analysis.",
        )

    import asyncio
    import uuid

    from app.tasks.code_health import compute_code_health_task
    task_id = str(uuid.uuid4())
    asyncio.create_task(compute_code_health_task(str(repository_id)))

    return {
        "status": "queued",
        "task_id": task_id,
        "message": "Code health analysis has been queued. Results will be available shortly.",
    }


from app.schemas.health_score import AutoFixRequest, AutoFixResponse
from app.services.auto_fix_service import AutoFixService


@router.post("/{repository_id}/auto-fix", response_model=AutoFixResponse, status_code=status.HTTP_200_OK)
async def auto_fix_code_health_issue(
    repository_id: UUID,
    request: AutoFixRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Automatically generate and propose a fix for a specific code health issue."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    await check_repo_access(repository, current_user, db)

    if not repository.indexed_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository must be indexed before running auto-fix.",
        )

    embedding_repo = EmbeddingRepository(db)
    auto_fix_svc = AutoFixService()

    try:
        result = await auto_fix_svc.generate_and_apply_fix(
            repository=repository,
            issue_description=request.issue_description,
            user=current_user,
            embedding_repo=embedding_repo
        )
        return AutoFixResponse(**result)
    except Exception as e:
        logger.error(f"Auto-fix failed: {str(e)}")
        # In production this would distinguish between 4xx and 5xx via a custom APIError
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
