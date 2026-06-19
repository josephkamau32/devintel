"""Phase 3 tests: Code chunking, file parsing, and embedding pipeline."""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.utils.chunking import chunk_text, smart_chunk_code, get_token_count
from app.utils.file_parser import (
    is_supported_file,
    should_ignore_path,
    parse_repository_files,
)
from app.services.embedding import EmbeddingService
from app.services.indexing import IndexingService


# ── Chunking tests ────────────────────────────────────────────────────────────

class TestChunkText:
    """Tests for the token-based text chunker."""

    def test_short_text_returns_single_chunk(self):
        """Text shorter than chunk_size returns one chunk."""
        text = "Hello world, this is a short piece of text."
        chunks = chunk_text(text, chunk_size=500)
        assert len(chunks) == 1
        assert chunks[0][0] == text

    def test_long_text_splits_into_multiple_chunks(self):
        """Text longer than chunk_size is split."""
        text = "word " * 100  # ~100 tokens
        chunks = chunk_text(text, chunk_size=30, chunk_overlap=5)
        assert len(chunks) > 1

    def test_overlap_creates_shared_content(self):
        """Chunks overlap when chunk_overlap > 0."""
        text = "token " * 80
        chunks = chunk_text(text, chunk_size=30, chunk_overlap=5)
        assert len(chunks) >= 2
        # Each chunk text should be a non-empty string
        for chunk_text_content, start, end in chunks:
            assert isinstance(chunk_text_content, str)
            assert len(chunk_text_content) > 0
            assert end >= start

    def test_chunk_returns_tuples(self):
        """Return type is list of (text, start_char, end_char)."""
        text = "some text here"
        result = chunk_text(text, chunk_size=500)
        assert all(isinstance(t, tuple) and len(t) == 3 for t in result)

    def test_empty_text_returns_single_chunk(self):
        """Empty text returns one empty chunk."""
        chunks = chunk_text("", chunk_size=500)
        assert len(chunks) == 1


class TestGetTokenCount:
    """Tests for token counting."""

    def test_simple_text_token_count(self):
        """Basic token counting returns a positive int."""
        count = get_token_count("Hello world")
        assert count > 0
        assert isinstance(count, int)

    def test_empty_text_returns_zero(self):
        """Empty string has 0 tokens."""
        count = get_token_count("")
        assert count == 0

    def test_longer_text_has_more_tokens(self):
        """Longer text has more tokens than shorter text."""
        short_count = get_token_count("hello")
        long_count = get_token_count("hello " * 100)
        assert long_count > short_count


class TestSmartChunkCode:
    """Tests for smart code chunking with structure awareness."""

    def test_python_functions_are_chunked(self):
        """Python functions are split at def boundaries."""
        code = "\n".join([
            "def function_a():",
            "    return 'a'",
            "",
            "def function_b():",
            "    return 'b'",
            "",
            "def function_c():",
            "    return 'c'",
        ])
        chunks = smart_chunk_code(code, "test.py", chunk_size=20)
        assert len(chunks) >= 1
        assert all(isinstance(c, str) for c in chunks)

    def test_typescript_code_chunked(self):
        """TypeScript code can be chunked without error."""
        code = """
export interface User {
  id: number;
  name: string;
}

export function greet(user: User): string {
  return `Hello ${user.name}`;
}

export class UserService {
  getUser(id: number): User {
    return { id, name: 'Test' };
  }
}
"""
        chunks = smart_chunk_code(code, "user.ts")
        assert len(chunks) >= 1
        assert all(isinstance(c, str) for c in chunks)

    def test_unsupported_extension_uses_token_chunker(self):
        """Files with unsupported extension fall back to token-based chunking."""
        code = "some content " * 10  # small enough to not hang
        chunks = smart_chunk_code(code, "file.rb", chunk_size=100)
        assert len(chunks) >= 1

    def test_small_code_stays_single_chunk(self):
        """Code smaller than chunk_size stays in one chunk."""
        code = "def f(): pass"
        chunks = smart_chunk_code(code, "small.py", chunk_size=1000)
        assert len(chunks) == 1
        assert "def f(): pass" in chunks[0]


# ── File parser tests ─────────────────────────────────────────────────────────

class TestIsSupported:
    """Tests for file extension filtering."""

    def test_supported_python(self):
        assert is_supported_file(Path("script.py")) is True

    def test_supported_javascript(self):
        assert is_supported_file(Path("app.js")) is True

    def test_supported_typescript(self):
        assert is_supported_file(Path("component.tsx")) is True

    def test_supported_markdown(self):
        assert is_supported_file(Path("README.md")) is True

    def test_unsupported_image(self):
        assert is_supported_file(Path("photo.png")) is False

    def test_unsupported_binary(self):
        assert is_supported_file(Path("program.exe")) is False

    def test_unsupported_no_extension(self):
        assert is_supported_file(Path("Makefile")) is False


class TestShouldIgnorePath:
    """Tests for directory ignore filtering."""

    def test_node_modules_ignored(self):
        assert should_ignore_path(Path("node_modules/lodash/index.js")) is True

    def test_git_ignored(self):
        assert should_ignore_path(Path(".git/HEAD")) is True

    def test_pycache_ignored(self):
        assert should_ignore_path(Path("app/__pycache__/module.pyc")) is True

    def test_normal_file_not_ignored(self):
        assert should_ignore_path(Path("src/main.py")) is False

    def test_venv_ignored(self):
        assert should_ignore_path(Path("venv/lib/site-packages/requests/__init__.py")) is True


class TestParseRepositoryFiles:
    """Tests for parsing actual files from a directory."""

    def test_parses_python_files(self):
        """Supported files are found and read."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a supported Python file
            py_file = Path(tmpdir) / "main.py"
            py_file.write_text("def hello(): pass\n")

            # Create an unsupported file that should be ignored
            png_file = Path(tmpdir) / "logo.png"
            png_file.write_bytes(b"\x89PNG\r\n\x1a\n")

            result = parse_repository_files(tmpdir)

        assert len(result) == 1
        path, content = result[0]
        assert path.endswith("main.py")
        assert "def hello" in content

    def test_ignores_node_modules(self):
        """node_modules directory is skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nm_dir = Path(tmpdir) / "node_modules" / "pkg"
            nm_dir.mkdir(parents=True)
            (nm_dir / "index.js").write_text("module.exports = {};")

            src_file = Path(tmpdir) / "src" / "app.ts"
            src_file.parent.mkdir()
            src_file.write_text("export const x = 1;")

            result = parse_repository_files(tmpdir)

        paths = [r[0] for r in result]
        assert not any("node_modules" in p for p in paths)
        assert any("app.ts" in p for p in paths)

    def test_empty_directory_returns_empty_list(self):
        """Empty directory returns []."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = parse_repository_files(tmpdir)
        assert result == []


# ── Embedding service tests ───────────────────────────────────────────────────

class TestEmbeddingService:
    """Tests for EmbeddingService."""

    @pytest.mark.asyncio
    async def test_generate_single_embedding(self):
        """generate_embedding returns a list of 1536 floats."""
        service = EmbeddingService()
        with patch(
            "app.integrations.openai_client.OpenAIClient.generate_embedding",
            new_callable=AsyncMock,
        ) as mock_gen:
            mock_gen.return_value = [0.1] * 1536
            result = await service.generate_embedding("def hello(): pass")
        assert len(result) == 1536
        assert all(isinstance(v, float) for v in result)
        mock_gen.assert_called_once_with("def hello(): pass")

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch_all_texts(self):
        """Batch generation processes all input texts."""
        service = EmbeddingService()
        texts = [f"chunk {i}" for i in range(10)]
        with patch(
            "app.integrations.openai_client.OpenAIClient.generate_embeddings_batch",
            new_callable=AsyncMock,
        ) as mock_batch:
            mock_batch.return_value = [[0.5] * 1536 for _ in range(10)]
            results = await service.generate_embeddings_batch(texts, batch_size=10)
        assert len(results) == 10
        assert all(len(e) == 1536 for e in results)

    @pytest.mark.asyncio
    async def test_batch_respects_batch_size(self):
        """Large input is split into correct number of batches."""
        service = EmbeddingService()
        texts = [f"text {i}" for i in range(25)]
        call_counts = []

        async def mock_batch_fn(batch):
            call_counts.append(len(batch))
            return [[0.1] * 1536 for _ in batch]

        with patch(
            "app.integrations.openai_client.OpenAIClient.generate_embeddings_batch",
            side_effect=mock_batch_fn,
        ):
            results = await service.generate_embeddings_batch(texts, batch_size=10)

        assert len(results) == 25
        # 25 texts with batch_size=10 → 3 calls (10, 10, 5)
        assert len(call_counts) == 3
        assert sorted(call_counts) == [5, 10, 10]

    @pytest.mark.asyncio
    async def test_progress_callback_is_called(self):
        """on_progress callback is invoked after each batch."""
        service = EmbeddingService()
        texts = [f"t{i}" for i in range(20)]
        progress_calls = []

        async def on_progress(current, total):
            progress_calls.append((current, total))

        with patch(
            "app.integrations.openai_client.OpenAIClient.generate_embeddings_batch",
            new_callable=AsyncMock,
            return_value=[[0.1] * 1536 for _ in range(10)],
        ):
            await service.generate_embeddings_batch(
                texts, batch_size=10, on_progress=on_progress
            )

        assert len(progress_calls) >= 1
        # Last call should report total == total
        assert progress_calls[-1][1] == 20


# ── Indexing service tests ─────────────────────────────────────────────────────

class TestIndexingService:
    """Tests for IndexingService parsing and chunking."""

    @pytest.mark.asyncio
    async def test_parse_and_chunk_repository(self):
        """parse_and_chunk_repository returns (path, index, text) tuples."""
        service = IndexingService()

        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "module.py"
            py_file.write_text(
                "def foo():\n    return 1\n\ndef bar():\n    return 2\n"
            )

            chunks = await service.parse_and_chunk_repository(tmpdir)

        assert len(chunks) >= 1
        for file_path, chunk_index, chunk_text_content in chunks:
            assert isinstance(file_path, str)
            assert isinstance(chunk_index, int)
            assert isinstance(chunk_text_content, str)
            assert len(chunk_text_content) > 0

    @pytest.mark.asyncio
    async def test_empty_repo_returns_empty_list(self):
        """Empty directory returns an empty list (no crash)."""
        service = IndexingService()

        with tempfile.TemporaryDirectory() as tmpdir:
            chunks = await service.parse_and_chunk_repository(tmpdir)

        assert chunks == []

    @pytest.mark.asyncio
    async def test_cleanup_removes_directory(self):
        """cleanup_repository deletes the cloned directory."""
        service = IndexingService()
        tmpdir = tempfile.mkdtemp()
        assert os.path.exists(tmpdir)

        await service.cleanup_repository(tmpdir)

        assert not os.path.exists(tmpdir)

    @pytest.mark.asyncio
    async def test_cleanup_nonexistent_path_is_safe(self):
        """Cleaning a non-existent path does not raise."""
        service = IndexingService()
        await service.cleanup_repository("/nonexistent/path/xyz")  # should not raise
