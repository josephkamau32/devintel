"""Background task for autonomous AI pull request review."""

import asyncio
from uuid import UUID

from asgiref.sync import async_to_sync

from app.core.logging import get_logger
from app.tasks.celery import celery

logger = get_logger(__name__)


@celery.task(bind=True, max_retries=2, name="app.tasks.pr_review.review_pull_request_task")
def review_pull_request_task(
    self,
    repo_id: str,
    pr_number: int,
    pr_title: str,
    access_token: str,
):
    """
    Celery task: generate an AI code review for a GitHub pull request and
    post it as a comment on the PR.

    Args:
        repo_id: Repository UUID string
        pr_number: GitHub pull request number
        pr_title: PR title (for display in the review)
        access_token: Decrypted GitHub access token with write access
    """
    try:
        async_to_sync(_review_pull_request_async)(
            repo_id, pr_number, pr_title, access_token
        )
    except Exception as e:
        logger.error(f"PR review task wrapper failed: {e}", exc_info=True)
        raise
    return {"status": "completed", "repo_id": repo_id, "pr_number": pr_number}


async def _review_pull_request_async(
    repo_id: str,
    pr_number: int,
    pr_title: str,
    access_token: str,
) -> None:
    """Async implementation of PR review generation and posting."""
    from app.db.session import AsyncSessionLocal
    from app.integrations.github_client import GitHubClient
    from app.repositories.embedding import EmbeddingRepository
    from app.repositories.repository import RepositoryRepository
    from app.services.pr_review_service import PRReviewService, REVIEW_WATERMARK

    async with AsyncSessionLocal() as db:
        try:
            repo_repo = RepositoryRepository(db)
            repo = await repo_repo.get_by_id(UUID(repo_id))

            if not repo:
                logger.error(f"PR review task: repository not found: {repo_id}")
                return

            if not repo.indexed_status:
                logger.info(
                    f"PR review skipped for {repo.full_name}#{pr_number} "
                    "— repository is not indexed yet."
                )
                return

            github_client = GitHubClient(access_token)

            # 1. Check for existing DevIntel review to prevent duplicates
            existing_comments_data = await _get_pr_comments(github_client, repo.full_name, pr_number)
            for comment_body in existing_comments_data:
                if REVIEW_WATERMARK in comment_body:
                    logger.info(
                        f"PR #{pr_number} in {repo.full_name} already has a DevIntel review — skipping."
                    )
                    return

            # 2. Get changed files with diffs
            logger.info(f"Fetching files for {repo.full_name}#{pr_number}")
            changed_files = await github_client.get_pull_request_files(
                full_name=repo.full_name,
                pr_number=pr_number,
            )

            if not changed_files:
                logger.info(f"No files found for PR #{pr_number} — skipping review.")
                return

            # 3. Generate AI review
            embedding_repo = EmbeddingRepository(db)
            review_service = PRReviewService()

            logger.info(f"Generating AI review for {repo.full_name}#{pr_number}")
            review_comment = await review_service.generate_review(
                repository=repo,
                pr_number=pr_number,
                pr_title=pr_title,
                changed_files=changed_files,
                embedding_repo=embedding_repo,
            )

            # 4. Post the comment to GitHub
            result = await github_client.post_pull_request_comment(
                full_name=repo.full_name,
                pr_number=pr_number,
                body=review_comment,
            )

            logger.info(
                f"Successfully posted AI review for {repo.full_name}#{pr_number} "
                f"→ {result.get('url', 'unknown url')}"
            )

        except Exception as e:
            logger.error(
                f"Failed to generate/post review for {repo_id}#{pr_number}: {e}",
                exc_info=True,
            )
            # Don't retry on review failures — the repo might not be ready
            # or the PR may have been closed


async def _get_pr_comments(
    github_client,
    full_name: str,
    pr_number: int,
) -> list[str]:
    """Return list of existing comment bodies on a PR."""
    import asyncio

    try:
        def _fetch_comments():
            repo = github_client.client.get_repo(full_name)
            pr = repo.get_pull(pr_number)
            return [c.body for c in pr.get_issue_comments()]

        return await asyncio.to_thread(_fetch_comments)
    except Exception as e:
        logger.warning(f"Could not fetch PR comments for duplicate check: {e}")
        return []
