"""Incremental indexer service for processing git push events.

Only updates embeddings for changed files instead of re-indexing the entire repository.
"""

import asyncio
import os
import shutil
import tempfile
from datetime import datetime
from typing import Any
from uuid import UUID

from git import Repo

from app.core.exceptions import IndexingError
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.repository import IndexingStatus
from app.repositories.embedding import EmbeddingRepository
from app.repositories.repository import RepositoryRepository
from app.services.embedding import EmbeddingService
from app.services.indexing import IndexingService
from app.services.progress_bus import progress_bus
from app.utils.chunking import smart_chunk_code

logger = get_logger(__name__)


async def _publish_progress(repo_id: str, progress: int, status: str) -> None:
    """Publish indexing progress via the in-process event bus."""
    try:
        payload = {"progress": progress, "status": status}
        await progress_bus.publish(f"indexing:{repo_id}", payload)
    except Exception as e:
        logger.debug(f"Progress publish failed (non-critical): {e}")


async def process_push_event(
    repo_id: str,
    clone_url: str,
    access_token: str,
    changed_files: list[str],
    added_files: list[str],
    removed_files: list[str],
    head_commit_sha: str,
) -> dict[str, Any]:
    """
    Process a git push event with incremental indexing.

    Only processes files that have been added or modified.
    Removes embeddings for deleted files.
    """
    repo_path = None
    incremental_service = IncrementalIndexer()

    try:
        async with AsyncSessionLocal() as db:
            repo_repo = RepositoryRepository(db)

            # Update status to in-progress
            await repo_repo.update(
                UUID(repo_id),
                indexing_status=IndexingStatus.INDEXING,
                indexing_progress=0,
                indexing_error=None,
                indexing_mode="incremental",
            )
            await db.commit()
            await _publish_progress(repo_id, 0, "starting_incremental")

            # Clone repository at the specific commit
            repo_path = await asyncio.wait_for(
                incremental_service.clone_repository_at_commit(clone_url, access_token, head_commit_sha),
                timeout=120,
            )

            await _publish_progress(repo_id, 20, "cloned")

            # Process removed files - delete their embeddings
            if removed_files:
                embedding_repo = EmbeddingRepository(db)
                deleted_total = 0
                for file_path in removed_files:
                    deleted = await embedding_repo.delete_by_file_path(UUID(repo_id), file_path)
                    deleted_total += deleted
                logger.info(f"Deleted {deleted_total} embeddings for {len(removed_files)} removed files")
                await db.commit()

            # Process changed + added files
            files_to_process = list(set(changed_files + added_files))
            if not files_to_process:
                logger.info("No files to process in incremental update")
                await repo_repo.update(
                    UUID(repo_id),
                    indexing_status=IndexingStatus.COMPLETE,
                    last_indexed_at=datetime.utcnow(),
                    last_indexed_commit_sha=head_commit_sha,
                    indexing_progress=100,
                    indexing_mode="incremental",
                )
                await db.commit()
                return {"status": "completed", "files_processed": 0}

            await _publish_progress(repo_id, 40, "processing_files")

            # Parse and chunk only the changed files
            chunks = incremental_service.parse_files(repo_path, files_to_process)

            # Update embeddings
            embedding_repo = EmbeddingRepository(db)
            total_deleted = 0
            total_created = 0

            for file_path in files_to_process:
                # Delete existing embeddings for this file
                deleted = await embedding_repo.delete_by_file_path(UUID(repo_id), file_path)
                total_deleted += deleted

            await db.commit()

            # Generate embeddings for new chunks
            if chunks:
                embedding_service = EmbeddingService()
                chunk_texts = [chunk[2] for chunk in chunks]

                async def update_progress(current: int, total: int):
                    progress = 40 + int((current / total) * 50)
                    await repo_repo.update(UUID(repo_id), indexing_progress=progress)
                    await db.commit()
                    await _publish_progress(repo_id, progress, "embedding")

                embeddings = await asyncio.wait_for(
                    embedding_service.generate_embeddings_batch(
                        chunk_texts,
                        batch_size=50,
                        on_progress=update_progress
                    ),
                    timeout=1800,
                )

                # Store embeddings
                embeddings_data = []
                for (file_path, chunk_index, chunk_text), embedding in zip(chunks, embeddings, strict=False):
                    embeddings_data.append({
                        "repo_id": UUID(repo_id),
                        "file_path": file_path,
                        "chunk_index": chunk_index,
                        "chunk_text": chunk_text,
                        "embedding": embedding,
                    })

                await embedding_repo.create_bulk(embeddings_data)
                total_created = len(embeddings_data)
                await db.commit()

            # Finalize
            await repo_repo.update(
                UUID(repo_id),
                indexing_status=IndexingStatus.COMPLETE,
                last_indexed_at=datetime.utcnow(),
                last_indexed_commit_sha=head_commit_sha,
                indexing_progress=100,
                indexing_mode="incremental",
            )
            await db.commit()

            # Clear cache
            from app.services.cache import cache
            await cache.delete_pattern(f"embed:{repo_id}:*")

            logger.info(
                f"Incremental indexing complete for {repo_id}: "
                f"{total_created} chunks created, {total_deleted} deleted"
            )

            return {
                "status": "completed",
                "files_processed": len(files_to_process),
                "chunks_created": total_created,
                "chunks_deleted": total_deleted,
            }

    except asyncio.TimeoutError:
        error_msg = "Incremental indexing timed out"
        logger.error(f"Timeout for repo {repo_id}")
        await _handle_incremental_failure(repo_id, error_msg)
        raise
    except Exception as e:
        safe_error = IndexingService.redact_token_from_url(str(e), access_token)
        error_msg = f"Unexpected error: {safe_error}"
        logger.error(f"Failed incremental indexing for {repo_id}: {safe_error}", exc_info=True)
        await _handle_incremental_failure(repo_id, error_msg)
        raise
    finally:
        if repo_path and os.path.exists(repo_path):
            try:
                shutil.rmtree(repo_path)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup {repo_path}: {cleanup_error}")


async def _handle_incremental_failure(repo_id: str, error_msg: str) -> None:
    """Record incremental indexing failure."""
    try:
        async with AsyncSessionLocal() as db:
            repo_repo = RepositoryRepository(db)
            await repo_repo.update(
                UUID(repo_id),
                indexing_status=IndexingStatus.FAILED,
                indexing_mode="full",  # Fall back to full mode on error
                indexing_error=error_msg,
                indexing_progress=0,
            )
            await db.commit()
    except Exception as update_error:
        logger.error(f"Failed to update error status: {update_error}")


class IncrementalIndexer:
    """Service for incremental repository indexing operations."""

    @staticmethod
    def clone_repository_at_commit(clone_url: str, access_token: str, sha: str) -> str:
        """Clone repository at a specific commit (shallow clone with specific SHAs)."""
        try:
            temp_dir = tempfile.mkdtemp(prefix="devintel_incremental_")

            auth_clone_url = clone_url
            if access_token and "github.com" in clone_url:
                auth_clone_url = clone_url.replace(
                    "https://",
                    f"https://{access_token}@"
                )

            safe_url = IndexingService.redact_token_from_url(clone_url, access_token)
            logger.info(f"Cloning repository {safe_url} at commit {sha} to {temp_dir}")

            # Clone with depth 1 and specific branch, then fetch the specific commit
            repo = Repo.clone_from(
                auth_clone_url,
                temp_dir,
                depth=1,
                branch="main",
            )

            # Fetch the specific commit if different from HEAD
            try:
                repo.git.fetch(prune=True)
                repo.git.checkout(sha)
            except Exception:
                # If specific SHA checkout fails, use whatever we have
                pass

            return temp_dir
        except Exception as e:
            safe_error = IndexingService.redact_token_from_url(str(e), access_token)
            logger.error(f"Failed to clone repository for incremental indexing: {safe_error}")
            raise IndexingError(
                detail=f"Failed to clone repository for incremental indexing: {safe_error}",
            )

    @staticmethod
    def parse_files(repo_path: str, file_paths: list[str]) -> list[tuple[str, int, str]]:
        """
        Parse only specified files and chunk them.

        Returns:
            List of (file_path, chunk_index, chunk_text) tuples
        """
        all_chunks = []

        for file_path in file_paths:
            full_path = os.path.join(repo_path, file_path)
            if not os.path.exists(full_path):
                logger.debug(f"File not found in repo: {file_path}")
                continue

            try:
                with open(full_path, encoding="utf-8") as f:
                    content = f.read()

                chunks = smart_chunk_code(content, file_path)
                for chunk_index, chunk_text in enumerate(chunks):
                    all_chunks.append((file_path, chunk_index, chunk_text))
            except Exception as e:
                logger.warning(f"Failed to process file {file_path}: {e}")

        return all_chunks
