"""Context reranker — re-scores retrieved chunks for relevance.

This is a stub implementation that simply preserves the original
similarity ordering.  It's designed to be swapped out with a cross-
encoder or Cohere reranker when the team is ready.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class ContextReranker:
    """Re-rank retrieved context chunks.

    Currently a passthrough — sorts by original similarity score.
    Replace with a cross-encoder model for better precision.
    """

    async def rerank(
        self,
        query: str,
        chunks: list[tuple[Any, float]],
        top_k: int | None = None,
    ) -> list[tuple[Any, float]]:
        """Re-rank chunks by relevance to the query.

        Args:
            query: The user's search query.
            chunks: List of (Embedding, similarity_score) tuples.
            top_k: Optional limit on returned results.

        Returns:
            Re-ranked list of (Embedding, similarity_score) tuples.
        """
        if not chunks:
            return []

        # Default: sort by similarity descending (passthrough)
        ranked = sorted(chunks, key=lambda x: x[1], reverse=True)

        if top_k is not None:
            ranked = ranked[:top_k]

        return ranked
