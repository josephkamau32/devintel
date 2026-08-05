"""Embedding service."""

from collections.abc import Callable, Coroutine
from typing import Any, Optional

from app.ai.orchestrator import get_orchestrator
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating and searching embeddings."""

    def __init__(self):
        """Initialize service."""
        self.orchestrator = get_orchestrator()

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text."""
        return await self.orchestrator.embed(text, agent="embedding")

    async def generate_embeddings_batch(
        self,
        texts: list[str],
        batch_size: int = 50,
        on_progress: Optional[Callable[[int, int], Coroutine[Any, Any, None]]] = None,
    ) -> list[list[float]]:
        """
        Generate embeddings in batches to handle large volumes.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch
            on_progress: Async callback(current_count, total_count)

        Returns:
            List of embeddings
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            response = await self.orchestrator.embed_batch(
                batch, agent="embedding"
            )
            all_embeddings.extend(response.embeddings)

            current_count = len(all_embeddings)
            total_count = len(texts)
            logger.info(
                "Generated embeddings for batch %d/%d (%d/%d)",
                i // batch_size + 1,
                max(1, (len(texts) + batch_size - 1) // batch_size),
                current_count,
                total_count,
            )

            if on_progress:
                await on_progress(current_count, total_count)

        return all_embeddings

