"""Background task for computing code health scores after repository indexing.

Runs as an asyncio task in-process — no Celery or Redis required.
"""

from uuid import UUID

from app.core.logging import get_logger

logger = get_logger(__name__)


async def compute_code_health_task(repo_id: str) -> dict:
    """
    Background task: analyze repo code quality and persist the result.

    Triggered automatically after a repository is successfully indexed.

    Args:
        repo_id: Repository UUID string
    """
    try:
        await _compute_code_health_async(repo_id)
    except Exception as e:
        logger.error(f"Code health task failed for {repo_id}: {e}", exc_info=True)
    return {"status": "completed", "repo_id": repo_id}


async def _compute_code_health_async(repo_id: str) -> None:
    """Async implementation of code health computation."""
    from app.db.session import AsyncSessionLocal
    from app.models.repository import IndexingStatus
    from app.repositories.code_health import CodeHealthRepository
    from app.repositories.embedding import EmbeddingRepository
    from app.repositories.repository import RepositoryRepository
    from app.services.code_health_service import CodeHealthService

    async with AsyncSessionLocal() as db:
        try:
            repo_repo = RepositoryRepository(db)
            repo = await repo_repo.get_by_id(UUID(repo_id))

            if not repo:
                logger.error(f"Code health task: repository not found: {repo_id}")
                return

            if repo.indexing_status != IndexingStatus.COMPLETE:
                logger.info(f"Code health skipped for {repo_id} — not indexed yet.")
                return

            embedding_repo = EmbeddingRepository(db)
            health_repo = CodeHealthRepository(db)
            service = CodeHealthService()

            result = await service.analyze(
                repository=repo,
                embedding_repo=embedding_repo,
                health_repo=health_repo,
            )

            await db.commit()
            logger.info(
                f"Code health analysis complete for {repo.full_name}: "
                f"overall={result.get('overall_score', 0):.1f}/100"
            )

        except Exception as e:
            logger.error(f"Code health analysis failed for {repo_id}: {e}", exc_info=True)
