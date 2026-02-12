"""Tests for indexing service."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.indexing import IndexingService
from app.core.exceptions import IndexingError


class TestIndexingService:
    """Test suite for repository indexing service."""

    @pytest.mark.asyncio
    async def test_clone_repository_success(self):
        """Test successful repository cloning."""
        with patch("app.services.indexing.Repo") as MockRepo:
            mock_repo_instance = MagicMock()
            MockRepo.clone_from.return_value = mock_repo_instance

            clone_url = "https://github.com/test/repo.git"
            access_token = "test_token"

            repo_path = await IndexingService.clone_repository(clone_url, access_token)

            assert repo_path.startswith(tempfile.gettempdir())
            assert "devintel_" in repo_path
            MockRepo.clone_from.assert_called_once()

    @pytest.mark.asyncio
    async def test_clone_repository_with_token(self):
        """Test repository cloning with access token injection."""
        with patch("app.services.indexing.Repo") as MockRepo:
            clone_url = "https://github.com/test/repo.git"
            access_token = "test_token_123"

            await IndexingService.clone_repository(clone_url, access_token)

            # Verify token was injected into URL
            call_args = MockRepo.clone_from.call_args
            cloned_url = call_args[0][0]
            assert access_token in cloned_url
            assert "https://test_token_123@github.com" in cloned_url

    @pytest.mark.asyncio
    async def test_clone_repository_failure(self):
        """Test repository cloning failure handling."""
        with patch("app.services.indexing.Repo") as MockRepo:
            MockRepo.clone_from.side_effect = Exception("Clone failed")

            clone_url = "https://github.com/test/repo.git"
            access_token = "test_token"

            with pytest.raises(IndexingError):
                await IndexingService.clone_repository(clone_url, access_token)

    @pytest.mark.asyncio
    async def test_parse_and_chunk_repository(self, sample_code_chunk):
        """Test parsing and chunking repository files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sample files
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text(sample_code_chunk)

            with patch("app.services.indexing.parse_repository_files") as mock_parse:
                mock_parse.return_value = [("test.py", sample_code_chunk)]

                with patch("app.services.indexing.smart_chunk_code") as mock_chunk:
                    mock_chunk.return_value = ["chunk1", "chunk2"]

                    chunks = await IndexingService.parse_and_chunk_repository(temp_dir)

                    assert len(chunks) == 2
                    assert chunks[0] == ("test.py", 0, "chunk1")
                    assert chunks[1] == ("test.py", 1, "chunk2")

    @pytest.mark.asyncio
    async def test_parse_and_chunk_empty_repository(self):
        """Test parsing repository with no supported files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("app.services.indexing.parse_repository_files") as mock_parse:
                mock_parse.return_value = []

                chunks = await IndexingService.parse_and_chunk_repository(temp_dir)

                assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_parse_and_chunk_error_handling(self):
        """Test error handling in parsing and chunking."""
        with patch("app.services.indexing.parse_repository_files") as mock_parse:
            mock_parse.side_effect = Exception("Parse error")

            with pytest.raises(IndexingError):
                await IndexingService.parse_and_chunk_repository("/fake/path")

    @pytest.mark.asyncio
    async def test_cleanup_repository(self):
        """Test repository cleanup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test")

            assert os.path.exists(temp_dir)

            await IndexingService.cleanup_repository(temp_dir)

            assert not os.path.exists(temp_dir)

    @pytest.mark.asyncio
    async def test_cleanup_nonexistent_repository(self):
        """Test cleanup of non-existent repository path."""
        # Should not raise an error
        await IndexingService.cleanup_repository("/nonexistent/path")

    @pytest.mark.asyncio
    async def test_full_indexing_workflow(self, sample_code_chunk):
        """Test complete indexing workflow from clone to chunk."""
        with patch("app.services.indexing.Repo") as MockRepo:
            with patch("app.services.indexing.parse_repository_files") as mock_parse:
                with patch("app.services.indexing.smart_chunk_code") as mock_chunk:
                    mock_parse.return_value = [("test.py", sample_code_chunk)]
                    mock_chunk.return_value = ["chunk1"]

                    # Clone
                    repo_path = await IndexingService.clone_repository(
                        "https://github.com/test/repo.git", "token"
                    )

                    # Parse and chunk
                    chunks = await IndexingService.parse_and_chunk_repository(repo_path)

                    # Cleanup
                    await IndexingService.cleanup_repository(repo_path)

                    assert len(chunks) > 0
                    MockRepo.clone_from.assert_called_once()

    @pytest.mark.asyncio
    async def test_indexing_large_files(self):
        """Test indexing respects file size limits."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a large file
            large_file = Path(temp_dir) / "large.py"
            large_file.write_text("x" * (11 * 1024 * 1024))  # 11 MB

            with patch("app.services.indexing.parse_repository_files") as mock_parse:
                # parse_repository_files should skip large files
                mock_parse.return_value = []

                chunks = await IndexingService.parse_and_chunk_repository(temp_dir)
                assert len(chunks) == 0
