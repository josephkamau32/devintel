"""Repository indexing service."""

import os
import re
import shutil
import tempfile

from git import Repo

from app.core.exceptions import IndexingError
from app.core.logging import get_logger
from app.utils.chunking import smart_chunk_code
from app.utils.file_parser import parse_repository_files

logger = get_logger(__name__)


def _redact_token_from_url(text: str, token: str = "") -> str:
    """Strip credentials/tokens from a URL or text containing a URL for safe logging and error reporting."""
    if not text:
        return ""
    sanitized = str(text)
    if token and len(token) >= 4:
        sanitized = sanitized.replace(token, "***")
    # Strip user:token@ or token@ from http/https URLs
    sanitized = re.sub(r'(https?://)[^/@\s]+@', r'\1', sanitized)
    # Strip standard GitHub token prefixes if any remain
    sanitized = re.sub(r'gh[pousr]_[A-Za-z0-9_]{16,}', '***', sanitized)
    return sanitized


class IndexingService:
    """Service for repository indexing operations."""

    @staticmethod
    def redact_token_from_url(text: str, token: str = "") -> str:
        """Helper to redact tokens/credentials from URLs or exception strings."""
        return _redact_token_from_url(text, token=token)

    @staticmethod
    async def clone_repository(clone_url: str, access_token: str) -> str:
        """
        Clone repository to temporary directory.

        Returns:
            Path to cloned repository
        """
        try:
            temp_dir = tempfile.mkdtemp(prefix="devintel_")

            auth_clone_url = clone_url
            # Add token to clone URL for private repos
            if access_token and "github.com" in clone_url:
                auth_clone_url = clone_url.replace(
                    "https://",
                    f"https://{access_token}@"
                )

            safe_url = _redact_token_from_url(clone_url, access_token)
            logger.info(f"Cloning repository {safe_url} to {temp_dir}")
            import asyncio
            await asyncio.to_thread(Repo.clone_from, auth_clone_url, temp_dir, depth=1)

            return temp_dir
        except Exception as e:
            safe_error = _redact_token_from_url(str(e), access_token)
            logger.error(f"Failed to clone repository: {safe_error}")
            raise IndexingError(
                detail=f"Failed to clone repository: {safe_error}",
            )

    @staticmethod
    async def parse_and_chunk_repository(
        repo_path: str,
    ) -> list[tuple[str, int, str]]:
        """
        Parse repository files and chunk them.

        Returns:
            List of (file_path, chunk_index, chunk_text) tuples
        """
        try:
            files_data = parse_repository_files(repo_path)

            all_chunks = []
            for file_path, content in files_data:
                chunks = smart_chunk_code(content, file_path)

                for chunk_index, chunk_text in enumerate(chunks):
                    all_chunks.append((file_path, chunk_index, chunk_text))

            logger.info(f"Generated {len(all_chunks)} chunks from {len(files_data)} files")
            return all_chunks
        except Exception as e:
            logger.error(f"Failed to parse and chunk repository: {e}")
            raise IndexingError(
                detail=f"Failed to parse repository: {str(e)}",
            )

    @staticmethod
    async def cleanup_repository(repo_path: str) -> None:
        """Clean up cloned repository."""
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
                logger.info(f"Cleaned up repository: {repo_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup repository: {e}")
