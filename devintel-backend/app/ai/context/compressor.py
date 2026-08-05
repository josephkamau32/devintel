"""Context compressor — reduces context size while preserving relevance.

Handles the problem where N retrieved chunks × neighbor expansion can
easily exceed the model's context window.  The compressor provides:

1. **Token budget enforcement**: Trim/truncate to stay within limits.
2. **Deduplication**: Merge overlapping chunks from the same file.
3. **Relevance ordering**: Sort by file grouping then by relevance score.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class ContextCompressor:
    """Compress and deduplicate retrieval context for LLM prompts."""

    def __init__(self, max_chars: int = 15_000, max_chunks: int = 20) -> None:
        """
        Args:
            max_chars: Hard character budget for the context window portion.
            max_chunks: Maximum number of chunks to include.
        """
        self.max_chars = max_chars
        self.max_chunks = max_chunks

    def compress(
        self,
        chunks: list[tuple[Any, float]],
    ) -> list[tuple[Any, float]]:
        """Compress a list of (embedding, similarity) tuples.

        Steps:
        1. Deduplicate by (file_path, chunk_index)
        2. Group by file_path and sort within each group by chunk_index
        3. Enforce max_chunks limit
        4. Enforce max_chars budget

        Args:
            chunks: List of (Embedding, similarity_score) tuples.

        Returns:
            Compressed list of (Embedding, similarity_score) tuples.
        """
        if not chunks:
            return []

        # 1. Deduplicate — keep highest-scored version of each chunk
        seen: dict[tuple[str, int], tuple[Any, float]] = {}
        for emb, score in chunks:
            key = (emb.file_path, emb.chunk_index)
            if key not in seen or score > seen[key][1]:
                seen[key] = (emb, score)

        # 2. Group by file, sort by chunk_index within each file
        by_file: dict[str, list[tuple[Any, float, int]]] = {}
        for (file_path, chunk_index), (emb, score) in seen.items():
            by_file.setdefault(file_path, []).append((emb, score, chunk_index))

        for file_path in by_file:
            by_file[file_path].sort(key=lambda x: x[2])

        # 3. Order files by best score (files with highest-scored chunk first)
        file_order = sorted(
            by_file.keys(),
            key=lambda f: max(s for _, s, _ in by_file[f]),
            reverse=True,
        )

        # 4. Flatten, respecting max_chunks and max_chars
        result: list[tuple[Any, float]] = []
        total_chars = 0

        for file_path in file_order:
            for emb, score, _ in by_file[file_path]:
                if len(result) >= self.max_chunks:
                    break

                chunk_text = emb.chunk_text or ""
                chunk_len = len(chunk_text) + len(file_path) + 30  # header overhead
                if total_chars + chunk_len > self.max_chars:
                    # Try truncating this chunk to fit
                    remaining = self.max_chars - total_chars - len(file_path) - 30
                    if remaining > 200:  # Only include if meaningful
                        # We can't mutate the ORM object, so just track the budget
                        total_chars += remaining
                        result.append((emb, score))
                    break

                total_chars += chunk_len
                result.append((emb, score))

            if len(result) >= self.max_chunks:
                break

        original_count = len(chunks)
        compressed_count = len(result)
        if compressed_count < original_count:
            logger.info(
                "Context compressed: %d → %d chunks (%d chars)",
                original_count,
                compressed_count,
                total_chars,
            )

        return result

    def format_context(
        self,
        chunks: list[tuple[Any, float]],
    ) -> str:
        """Format compressed chunks into a context string for the LLM.

        Groups consecutive chunks from the same file and adds headers.

        Args:
            chunks: Compressed (Embedding, score) tuples.

        Returns:
            Formatted context string.
        """
        if not chunks:
            return "\n[No relevant code was found for this query.]\n"

        parts: list[str] = []
        current_file: str | None = None
        total_chars = 0

        for emb, score in chunks:
            chunk_text = emb.chunk_text or ""

            if emb.file_path != current_file:
                current_file = emb.file_path
                parts.append(f"\n--- File: {emb.file_path} ---")

            # Truncate individual chunks if they'd exceed budget
            remaining = self.max_chars - total_chars
            if remaining <= 0:
                break
            if len(chunk_text) > remaining:
                chunk_text = chunk_text[:remaining] + "\n... [truncated]"

            parts.append(chunk_text)
            total_chars += len(chunk_text)

        return "\n".join(parts)
