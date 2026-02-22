"""PR review routes."""

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.integrations.openai_client import OpenAIClient
from app.models.user import User
from app.repositories.repository import RepositoryRepository
from app.schemas.pr_review import PRReviewRequest, PRReviewResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/pr-review", tags=["PR Review"])

# Maximum diff size to prevent context window overflow and runaway API costs
MAX_DIFF_CHARS = 100_000  # ~30K tokens
REVIEW_TIMEOUT_SECONDS = 60


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
    
    # Validate diff size to prevent context window overflow
    if len(request.pull_request_diff) > MAX_DIFF_CHARS:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PR diff is too large ({len(request.pull_request_diff):,} chars). "
                   f"Maximum allowed is {MAX_DIFF_CHARS:,} chars (~30K tokens). "
                   f"Please split the PR into smaller changes.",
        )
    
    # Build prompt
    prompt = f"""You are an expert code reviewer. Review the following pull request and provide structured feedback.

Repository: {repository.full_name}
PR Title: {request.pr_title}
PR Description: {request.pr_description}

Diff:
{request.pull_request_diff}

Provide a review as a JSON object with these exact keys:
{{
  "summary": "Overall assessment of the PR quality, correctness, and impact",
  "potential_issues": ["List of bugs, logic errors, or correctness concerns"],
  "refactoring_suggestions": ["Code quality improvements and cleaner approaches"],
  "security_warnings": ["Security vulnerabilities or unsafe patterns"],
  "performance_notes": ["Performance impacts or optimization opportunities"]
}}
"""
    
    # Call OpenAI with timeout and structured JSON output
    openai_client = OpenAIClient()
    try:
        response = await asyncio.wait_for(
            openai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                json_mode=True,
            ),
            timeout=REVIEW_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.error(f"PR review timed out after {REVIEW_TIMEOUT_SECONDS}s")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="PR review timed out. The diff may be too complex. Try a smaller PR.",
        )
    
    # Parse response
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
