"""Background task for repository indexing.

Runs as an asyncio task in-process — no Celery or Redis required.
"""

import asyncio
import json
from datetime import datetime
from uuid import UUID

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.repository import Repository
from app.repositories.embedding import EmbeddingRepository
from app.repositories.repository import RepositoryRepository
from app.services.embedding import EmbeddingService
from app.services.indexing import IndexingService
from app.services.progress_bus import progress_bus

logger = get_logger(__name__)


async def _publish_progress(repo_id: str, progress: int, status: str) -> None:
    """Publish indexing progress via the in-process event bus."""
    try:
        payload = {"progress": progress, "status": status}
        await progress_bus.publish(f"indexing:{repo_id}", payload)
    except Exception as e:
        # Progress publishing is best-effort — never fail indexing over it
        logger.debug(f"Progress publish failed (non-critical): {e}")


async def index_repository_task(repo_id: str, clone_url: str, access_token: str = "") -> dict:
    """
    Background task to index a repository.

    Runs as a fire-and-forget asyncio task via asyncio.create_task().

    Args:
        repo_id: Repository UUID
        clone_url: Git clone URL
        access_token: GitHub access token for private repos
    """
    try:
        await _index_repository_async(repo_id, clone_url, access_token)
    except Exception as e:
        logger.error(f"Indexing task failed for {repo_id}: {e}", exc_info=True)
    return {"status": "completed", "repo_id": repo_id}


async def _index_repository_async(
    repo_id: str,
    clone_url: str,
    access_token: str,
) -> None:
    """Async implementation of repository indexing."""
    repo_path = None
    indexing_service = IndexingService()
    
    async with AsyncSessionLocal() as db:
        try:
            repo_repo = RepositoryRepository(db)
            embedding_repo = EmbeddingRepository(db)
            
            # Get repository
            repo = await repo_repo.get_by_id(UUID(repo_id))
            if not repo:
                logger.error(f"Repository not found: {repo_id}")
                return
            
            # Update status to in-progress
            await repo_repo.update(
                UUID(repo_id),
                indexed_status=False,
                indexing_progress=0,
                indexing_error=None,
            )
            await db.commit()
            
            # Clone repository
            logger.info(f"Cloning repository: {clone_url}")
            # 10 minute timeout for cloning
            repo_path = await asyncio.wait_for(
                indexing_service.clone_repository(clone_url, access_token),
                timeout=600 
            )
            
            # Update progress: Finished cloning
            await repo_repo.update(UUID(repo_id), indexing_progress=15)
            await db.commit()
            await _publish_progress(repo_id, 15, "cloning")
            
            # Parse and chunk files
            logger.info(f"Parsing and chunking repository")
            chunks = await indexing_service.parse_and_chunk_repository(repo_path)
            
            if not chunks:
                logger.warning(f"No supported files found in repo {repo_id}")
                await repo_repo.update(
                    UUID(repo_id),
                    indexed_status=True, # Mark as "indexed" even if empty to avoid stuck status
                    indexing_progress=100,
                    indexing_error="No supported files found"
                )
                await db.commit()
                return
            
            # Update progress: Finished parsing
            await repo_repo.update(UUID(repo_id), indexing_progress=30)
            await db.commit()
            await _publish_progress(repo_id, 30, "parsing")
            
            # Delete old embeddings before re-indexing (prevents duplicates)
            deleted_count = await embedding_repo.delete_by_repo(UUID(repo_id))
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} old embeddings for repo {repo_id}")
                await db.commit()
            
            # Update progress: Starting embedding
            await repo_repo.update(UUID(repo_id), indexing_progress=40)
            await db.commit()
            await _publish_progress(repo_id, 40, "embedding")

            # Generate embeddings
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            embedding_service = EmbeddingService()
            
            chunk_texts = [chunk[2] for chunk in chunks]
            
            async def update_embedding_progress(current: int, total: int):
                # Map current progress between 40% and 80%
                progress = 40 + int((current / total) * 40)
                await repo_repo.update(UUID(repo_id), indexing_progress=progress)
                await db.commit()
                await _publish_progress(repo_id, progress, "embedding")

            # 30 minute timeout for large embedding jobs
            embeddings = await asyncio.wait_for(
                embedding_service.generate_embeddings_batch(
                    chunk_texts, 
                    batch_size=50,
                    on_progress=update_embedding_progress
                ),
                timeout=1800
            )
            
            # Update progress: Finished embeddings
            await repo_repo.update(UUID(repo_id), indexing_progress=80)
            await db.commit()
            
            # Store embeddings in database
            logger.info(f"Storing embeddings in database")
            embeddings_data = []
            for (file_path, chunk_index, chunk_text), embedding in zip(chunks, embeddings):
                embeddings_data.append({
                    "repo_id": UUID(repo_id),
                    "file_path": file_path,
                    "chunk_index": chunk_index,
                    "chunk_text": chunk_text,
                    "embedding": embedding,
                })
            
            # Bulk insert
            await embedding_repo.create_bulk(embeddings_data)
            await db.commit()
            
            # Update repository as indexed
            await repo_repo.update(
                UUID(repo_id),
                indexed_status=True,
                last_indexed_at=datetime.utcnow(),
                indexing_progress=100,
                indexing_error=None,
            )
            
            # Clear embedding cache for this repository
            from app.services.cache import cache
            await cache.delete_pattern(f"embed:{repo_id}:*")
            
            # Update analytics counter (only for personal repos; org repos don't have a direct user_id)
            if repo.user_id:
                from app.repositories.analytics import AnalyticsRepository
                analytics_repo = AnalyticsRepository(db)
                await analytics_repo.increment_repositories_indexed(repo.user_id)
            
            await db.commit()
            logger.info(f"Successfully indexed repository: {repo_id} ({len(chunks)} chunks)")

            # Fire code health analysis as a follow-up background task
            from app.tasks.code_health import compute_code_health_task
            asyncio.create_task(compute_code_health_task(repo_id))
            
        except asyncio.TimeoutError:
            error_msg = "Indexing timed out during processing (cloning or embedding)"
            logger.error(f"Timeout indexing repository {repo_id}")
            await _handle_indexing_failure(repo_repo, db, repo_id, error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Failed to index repository {repo_id}: {e}", exc_info=True)
            await _handle_indexing_failure(repo_repo, db, repo_id, error_msg)
        
        finally:
            # Cleanup
            if repo_path:
                try:
                    await indexing_service.cleanup_repository(repo_path)
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup repo path {repo_path}: {cleanup_error}")

async def _handle_indexing_failure(repo_repo, db, repo_id, error_msg):
    """Helper to safely record indexing failure."""
    try:
        await repo_repo.update(
            UUID(repo_id),
            indexed_status=False,
            indexing_error=error_msg,
            indexing_progress=0,
        )
        await db.commit()
    except Exception as update_error:
        logger.error(f"Critical: Failed to update error status for repo {repo_id}: {update_error}")
