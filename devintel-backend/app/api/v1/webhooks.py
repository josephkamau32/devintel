"""GitHub Webhook handler — auto re-indexes repositories on push events."""

import asyncio
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.webhook import verify_github_signature
from app.db.session import get_db
from app.repositories.repository import RepositoryRepository
from app.services.cache import cache
from app.tasks.indexing import index_repository_task

logger = get_logger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/github", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_hub_signature_256: str = Header(default="", alias="X-Hub-Signature-256"),
    x_github_event: str = Header(default="", alias="X-GitHub-Event"),
    x_github_delivery: str = Header(default="", alias="X-GitHub-Delivery"),
):
    """Handle GitHub webhook events.

    Currently handles:
    - ``push``: Re-indexes the affected repository when code is pushed to
      the default branch, keeping the vector index up to date automatically.
    - ``pull_request``: Triggers an AI code review comment for opened/updated PRs.
    - ``ping``: Responds with a confirmation that the hook is registered.

    All other events are acknowledged and ignored gracefully.
    """
    payload_bytes = await request.body()

    # Validate signature unconditionally (fails closed if secret unset or signature invalid)
    try:
        is_valid = verify_github_signature(payload_bytes, x_hub_signature_256)
    except RuntimeError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature.",
        )

    if not is_valid:
        logger.warning(
            f"Invalid webhook signature for delivery {x_github_delivery}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature.",
        )

    # Validate delivery ID header
    if not x_github_delivery:
        logger.warning("Webhook rejected: missing X-GitHub-Delivery header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-GitHub-Delivery header.",
        )

    # Replay protection: store delivery ID in cache with 24-hour TTL (86400s)
    delivery_key = f"webhook:delivery:{x_github_delivery}"
    is_new = await cache.setnx(delivery_key, "1", ttl=86400)
    if not is_new:
        logger.info(f"Duplicate webhook delivery ignored: {x_github_delivery}")
        return {"status": "ignored", "reason": "Duplicate delivery ID"}

    # Parse body
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload.",
        )

    event = x_github_event.lower()
    logger.info(f"Received GitHub webhook: event={event} delivery={x_github_delivery}")

    # --- Ping: GitHub sends this when the webhook is first set up ---
    if event == "ping":
        return {"status": "pong", "message": "Webhook registered successfully."}

    # --- Push event: incremental re-index the repository ---
    if event == "push":
        repo_full_name: str = payload.get("repository", {}).get("full_name", "")
        default_branch: str = payload.get("repository", {}).get("default_branch", "main")
        pushed_ref: str = payload.get("ref", "")
        head_commit_sha: str = payload.get("after", "")

        # Extract changed files from commits
        commits: list[dict] = payload.get("commits", [])
        changed_files = set()
        added_files = set()
        removed_files = set()

        for commit in commits:
            for f in commit.get("added", []):
                added_files.add(f)
            for f in commit.get("modified", []):
                changed_files.add(f)
            for f in commit.get("removed", []):
                removed_files.add(f)

        if not repo_full_name:
            logger.warning("Push event missing repository.full_name — ignoring.")
            return {"status": "ignored", "reason": "No repository name in payload"}

        # Only re-index pushes to the default branch
        if pushed_ref != f"refs/heads/{default_branch}":
            logger.info(
                f"Push to non-default branch ({pushed_ref}) for {repo_full_name} — skipping re-index."
            )
            return {
                "status": "ignored",
                "reason": f"Push was to {pushed_ref}, not refs/heads/{default_branch}",
            }

        # Look up repository in our DB
        repo_repo = RepositoryRepository(db)
        repository = await repo_repo.get_by_full_name_any(full_name=repo_full_name)

        if not repository:
            logger.info(
                f"Push received for {repo_full_name} but it is not connected — ignoring."
            )
            return {"status": "ignored", "reason": "Repository not connected to DevIntel."}

        # Skip if already indexing to prevent double-queueing
        if 0 < repository.indexing_progress < 100:
            logger.info(
                f"Repository {repo_full_name} is currently indexing — skipping duplicate trigger."
            )
            return {"status": "skipped", "reason": "Repository is already being indexed."}

        # Get access token for cloning (may be empty for public repos)
        access_token = await _get_repo_access_token(repository, db)

        # Determine if we should do incremental or full reindex
        # Fall back to full reindex if we don't have a last_indexed_commit_sha
        if repository.last_indexed_commit_sha and head_commit_sha:
            # Use incremental indexing
            from app.services.incremental_indexer import process_push_event
            task_id = str(uuid.uuid4())
            asyncio.create_task(
                process_push_event(
                    repo_id=str(repository.id),
                    clone_url=repository.url,
                    access_token=access_token,
                    changed_files=list(changed_files),
                    added_files=list(added_files),
                    removed_files=list(removed_files),
                    head_commit_sha=head_commit_sha,
                )
            )
            logger.info(
                f"Webhook triggered incremental re-index for {repo_full_name} "
                f"(repo_id={repository.id}, task_id={task_id})"
            )
            return {
                "status": "queued",
                "mode": "incremental",
                "repository": repo_full_name,
                "task_id": task_id,
                "files_changed": len(changed_files) + len(added_files) + len(removed_files),
            }
        else:
            # Fall back to full reindex
            task_id = str(uuid.uuid4())
            asyncio.create_task(
                index_repository_task(
                    repo_id=str(repository.id),
                    clone_url=repository.url,
                    access_token=access_token,
                )
            )
            logger.info(
                f"Webhook triggered full re-index for {repo_full_name} "
                f"(repo_id={repository.id}, task_id={task_id})"
            )
            return {
                "status": "queued",
                "mode": "full",
                "repository": repo_full_name,
                "task_id": task_id,
            }

    # --- Pull Request event: trigger AI code review ---
    if event == "pull_request":
        action: str = payload.get("action", "")
        pr_data: dict = payload.get("pull_request", {})
        repo_data: dict = payload.get("repository", {})

        # Only review when a PR is opened or new commits are pushed to it
        if action not in ("opened", "synchronize"):
            return {"status": "ignored", "reason": f"PR action '{action}' not reviewed."}

        repo_full_name = repo_data.get("full_name", "")
        pr_number = pr_data.get("number")
        pr_title = pr_data.get("title", "")

        if not repo_full_name or not pr_number:
            return {"status": "ignored", "reason": "Missing repository or PR number."}

        # Look up repository
        repo_repo = RepositoryRepository(db)
        repository = await repo_repo.get_by_full_name_any(full_name=repo_full_name)

        if not repository:
            logger.info(f"PR webhook for {repo_full_name} — not connected to DevIntel.")
            return {"status": "ignored", "reason": "Repository not connected."}

        if not repository.indexed_status:
            logger.info(f"PR webhook for {repo_full_name} — not indexed yet, skipping review.")
            return {"status": "ignored", "reason": "Repository not indexed."}

        # Retrieve the owner's access token for posting the review comment
        access_token = await _get_repo_access_token(repository, db)
        if not access_token:
            logger.warning(f"No access token available for {repo_full_name} — cannot post review.")
            return {"status": "ignored", "reason": "No access token available."}

        # Enqueue PR review task
        from app.tasks.pr_review import review_pull_request_task
        task_id = str(uuid.uuid4())
        asyncio.create_task(
            review_pull_request_task(
                repo_id=str(repository.id),
                pr_number=pr_number,
                pr_title=pr_title,
                access_token=access_token,
            )
        )

        logger.info(
            f"Queued PR review for {repo_full_name}#{pr_number} (task_id={task_id})"
        )
        return {
            "status": "queued",
            "repository": repo_full_name,
            "pr_number": pr_number,
            "task_id": task_id,
        }

    # All other events acknowledged but not acted upon
    return {"status": "ignored", "event": event}


async def _get_repo_access_token(repository, db) -> str:
    """
    Retrieve and decrypt the GitHub access token for the repository owner.
    For org repos, tries the first member with a stored token.
    """
    from app.services.encryption import encryption_service

    # Personal repository — use owner's token directly
    if repository.user_id:
        from app.repositories.user import UserRepository
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(repository.user_id)
        if user and user.github_token_encrypted:
            token = encryption_service.decrypt(user.github_token_encrypted)
            if token:
                return token

    # Org repository — find any org member with a token
    org_id = getattr(repository, "organization_id", None)
    if org_id:
        from sqlalchemy import select

        from app.models.organization import OrganizationMember
        from app.models.user import User
        stmt = (
            select(User)
            .join(OrganizationMember, OrganizationMember.user_id == User.id)
            .where(
                OrganizationMember.organization_id == org_id,
                User.github_token_encrypted.isnot(None),
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user and user.github_token_encrypted:
            token = encryption_service.decrypt(user.github_token_encrypted)
            if token:
                return token

    return ""
