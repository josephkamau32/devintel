"""PR review routes."""

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_repo_access, get_current_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.integrations.github_client import GitHubClient
from app.models.repository import IndexingStatus
from app.models.user import User
from app.repositories.embedding import EmbeddingRepository
from app.repositories.repository import RepositoryRepository
from app.schemas.pr_review import PRReviewRequest, PRReviewResponse
from app.services.chat import ChatService
from app.services.encryption import encryption_service

logger = get_logger(__name__)
router = APIRouter(prefix="/pr-review", tags=["PR Review"])

# Also mount under /repos for the pulls listing
pulls_router = APIRouter(prefix="/repos", tags=["PR Review"])

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

    # Authorization: use shared helper — handles both org and personal repos
    await check_repo_access(repository, current_user, db)

    # Get diff (either from request or from GitHub)
    diff_content = request.pull_request_diff

    if request.pr_number:
        if not current_user.github_token_encrypted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub token not found. Please re-authenticate.",
            )

        token = encryption_service.decrypt(current_user.github_token_encrypted)
        github_client = GitHubClient(token)
        try:
            diff_content = await github_client.get_pull_request_diff(
                repository.full_name, request.pr_number
            )
        except Exception as e:
            logger.error(f"Failed to fetch diff for PR #{request.pr_number}: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch PR diff from GitHub: {str(e)}",
            )

    if not diff_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No diff content provided and pr_number is missing or invalid",
        )

    # Validate diff size to prevent context window overflow
    if len(diff_content) > MAX_DIFF_CHARS:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PR diff is too large ({len(diff_content):,} chars). "
                   f"Maximum allowed is {MAX_DIFF_CHARS:,} chars (~30K tokens).",
        )

    # Optional: Enhance with RAG context if the repository is indexed
    context_text = ""
    if repository.indexing_status == IndexingStatus.COMPLETE:
        try:
            chat_service = ChatService()
            embedding_repo = EmbeddingRepository(db)

            # Simple heuristic: use the PR title and description to find relevant architectural context
            search_query = f"{request.pr_title} {request.pr_description}"
            relevant_chunks = await chat_service.retrieve_relevant_chunks(
                repo_id=repository.id,
                question=search_query,
                embedding_repo=embedding_repo,
                top_k=5
            )

            if relevant_chunks:
                context_text = "\n\nRelevant Repository Context:\n"
                for embedding, _ in relevant_chunks:
                    context_text += f"\n--- File: {embedding.file_path} ---\n{embedding.chunk_text[:500]}...\n"
        except Exception as e:
            logger.warning(f"Failed to retrieve RAG context for PR review: {e}")
            # Non-critical, continue without context

    # Build prompt
    prompt = f"""You are an expert code reviewer. Review the following pull request and provide structured feedback.
{context_text}

Repository: {repository.full_name}
PR Title: {request.pr_title}
PR Description: {request.pr_description}

Diff:
{diff_content}

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


from uuid import UUID

from app.schemas.pr_review import PullRequestListResponse


@pulls_router.get("/{repository_id}/pulls", response_model=PullRequestListResponse)
async def list_pull_requests(
    repository_id: UUID,
    state: str = "open",
    page: int = 1,
    per_page: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List pull requests for a repository from GitHub."""
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    await check_repo_access(repository, current_user, db)

    if not current_user.github_token_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub token not found. Please re-authenticate with GitHub.",
        )

    token = encryption_service.decrypt(current_user.github_token_encrypted)
    github_client = GitHubClient(token)

    try:
        pulls_data = await github_client.get_repository_pull_requests(
            full_name=repository.full_name,
            state=state,
            page=page,
            per_page=per_page,
        )
    except Exception as e:
        logger.error(f"Failed to fetch PRs for {repository.full_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch pull requests from GitHub: {str(e)}",
        )

    return PullRequestListResponse(
        pulls=pulls_data,
        repository_id=repository_id,
    )
