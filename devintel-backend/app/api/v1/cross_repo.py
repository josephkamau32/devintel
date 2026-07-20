"""Cross-repository knowledge API routes."""


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_repo_access, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.repository import RepositoryRepository
from app.schemas.cross_repo import (
    CrossRepoPatternRequest,
    CrossRepoPatternResponse,
)
from app.services.cross_repo_service import CrossRepoKnowledgeService

router = APIRouter(prefix="/cross-repo", tags=["Cross-Repository"])


@router.post("/patterns", response_model=CrossRepoPatternResponse)
async def find_cross_repo_patterns(
    request: CrossRepoPatternRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Find similar code patterns across repositories."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(request.repository_id)

    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    await check_repo_access(repository, current_user, db)

    service = CrossRepoKnowledgeService(db)
    patterns = await service.find_similar_patterns(
        repository=repository,
        pattern_type=request.pattern_type,
        query=request.query,
        top_k=request.top_k,
    )

    return CrossRepoPatternResponse(patterns=patterns)
