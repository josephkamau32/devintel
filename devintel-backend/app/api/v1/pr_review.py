"""PR review routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.integrations.openai_client import OpenAIClient
from app.models.user import User
from app.repositories.repository import RepositoryRepository
from app.schemas.pr_review import PRReviewRequest, PRReviewResponse

logger =get_logger(__name__)
router = APIRouter(prefix="/pr-review", tags=["PR Review"])


@router.post("", response_model=PRReviewResponse)
async def review_pull_request(
    request: PRReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Review a pull request using AI."""
    # Get repository
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(request.repository_id)
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )
    
    if repository.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )
    
    # Build prompt
    prompt = f"""You are an expert code reviewer. Review the following pull request and provide structured feedback.

Repository: {repository.full_name}
PR Title: {request.pr_title}
PR Description: {request.pr_description}

Diff:
{request.pull_request_diff}

Provide a review in the following JSON format:
{{
  "summary": "Overall assessment",
  "potential_issues": ["Issue 1", "Issue 2"],
  "refactoring_suggestions": ["Suggestion 1"],
  "security_warnings": ["Warning 1"],
  "performance_notes": ["Note 1"]
}}
"""
    
    # Call OpenAI
    openai_client = OpenAIClient()
    response = await openai_client.chat_completion(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    
    # Parse response
    import json
    try:
        review_data = json.loads(response)
        return PRReviewResponse(**review_data)
    except Exception as e:
        logger.error(f"Failed to parse PR review response: {e}")
        # Fallback
        return PRReviewResponse(
            summary=response[:500],
            potential_issues=[],
            refactoring_suggestions=[],
            security_warnings=[],
            performance_notes=[],
        )
