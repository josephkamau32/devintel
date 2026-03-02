"""GitHub Webhook handler — auto re-indexes repositories on push events."""

import hashlib
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.repositories.repository import RepositoryRepository
from app.tasks.indexing import index_repository_task

logger = get_logger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def _verify_github_signature(payload: bytes, signature: str) -> bool:
    """Verify X-Hub-Signature-256 header from GitHub.

    Returns True if the signature is valid or if webhook secret is not configured
    (development fallback). In production, GITHUB_WEBHOOK_SECRET must be set.
    """
    secret = settings.github_webhook_secret
    if not secret:
        logger.warning(
            "GITHUB_WEBHOOK_SECRET is not set — webhook signature validation skipped. "
            "Configure this in production for security."
        )
        return True

    mac = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    return hmac.compare_digest(expected, signature)



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
    - ``ping``: Responds with a confirmation that the hook is registered.

    All other events are acknowledged and ignored gracefully.
    """
    payload_bytes = await request.body()

    # Validate signature
    if x_hub_signature_256 and not _verify_github_signature(
        payload_bytes, x_hub_signature_256
    ):
        logger.warning(
            f"Invalid webhook signature for delivery {x_github_delivery}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature.",
        )

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

    # --- Push event: re-index the repository ---
    if event == "push":
        repo_full_name: str = payload.get("repository", {}).get("full_name", "")
        default_branch: str = payload.get("repository", {}).get("default_branch", "main")
        pushed_ref: str = payload.get("ref", "")

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

        # Enqueue indexing task (fire-and-forget)
        task = index_repository_task.delay(
            repo_id=str(repository.id),
            clone_url=repository.url,
            access_token="",  # Public repos or tokens already stored
        )

        logger.info(
            f"Webhook triggered re-index for {repo_full_name} "
            f"(repo_id={repository.id}, task_id={task.id})"
        )
        return {
            "status": "queued",
            "repository": repo_full_name,
            "task_id": task.id,
        }

    # All other events acknowledged but not acted upon
    return {"status": "ignored", "event": event}
