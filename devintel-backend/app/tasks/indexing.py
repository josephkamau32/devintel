"""Background tasks for repository indexing."""

import asyncio
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.repository import Repository
from app.repositories.embedding import EmbeddingRepository
from app.repositories.repository import RepositoryRepository
from app.services.embedding import EmbeddingService
from app.services.indexing import IndexingService
from app.tasks.celery import celery

logger = get_logger(__name__)


@celery.task(bind=True, max_retries=3)
def index_repository_task(self, repo_id: str, clone_url: str, access_token: str = ""):
    """
    Background task to index a repository.
    
    Args:
        repo_id: Repository UUID
        clone_url: Git clone URL
        access_token: GitHub access token for private repos
    """
    # Run async code in thread
    asyncio.run(_index_repository_async(repo_id, clone_url, access_token, self))
    return {"status": "completed", "repo_id": repo_id}


async def _index_repository_async(
    repo_id: str,
    clone_url: str,
    access_token: str,
    task: any,
) -> None:
    """Async implementation of repository indexing."""
    repo_path = None
    
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
            indexing_service = IndexingService()
            repo_path = await indexing_service.clone_repository(clone_url, access_token)
            
            # Update progress
            await repo_repo.update(UUID(repo_id), indexing_progress=20)
            await db.commit()
            
            # Parse and chunk files
            logger.info(f"Parsing and chunking repository")
            chunks = await indexing_service.parse_and_chunk_repository(repo_path)
            
            if not chunks:
                raise Exception("No supported files found in repository")
            
            # Update progress
            await repo_repo.update(UUID(repo_id), indexing_progress=40)
            await db.commit()
            
            # Delete old embeddings before re-indexing (prevents duplicates)
            deleted_count = await embedding_repo.delete_by_repo(UUID(repo_id))
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} old embeddings for repo {repo_id}")
                await db.commit()
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            embedding_service = EmbeddingService()
            
            chunk_texts = [chunk[2] for chunk in chunks]
            embeddings = await embedding_service.generate_embeddings_batch(chunk_texts)
            
            # Update progress
            await repo_repo.update(UUID(repo_id), indexing_progress=70)
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
            
            # Update analytics counter
            from app.repositories.analytics import AnalyticsRepository
            analytics_repo = AnalyticsRepository(db)
            await analytics_repo.increment_repositories_indexed(repo.user_id)
            
            await db.commit()
            
            logger.info(f"Successfully indexed repository: {repo_id}")
            
        except Exception as e:
            logger.error(f"Failed to index repository {repo_id}: {e}")
            
            # Update repository with error
            try:
                await repo_repo.update(
                    UUID(repo_id),
                    indexed_status=False,
                    indexing_error=str(e),
                    indexing_progress=0,
                )
                await db.commit()
            except Exception as update_error:
                logger.error(f"Failed to update repository error status: {update_error}")
            
            # Retry task
            raise self.retry(exc=e, countdown=60)
        
        finally:
            # Cleanup
            if repo_path:
                await indexing_service.cleanup_repository(repo_path)
