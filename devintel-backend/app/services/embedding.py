"""Embedding service."""

from collections.abc import Callable, Coroutine
from typing import Any, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.logging import get_logger
from app.integrations.openai_client import OpenAIClient

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating and searching embeddings."""

    def __init__(self):
        """Initialize service."""
        self.openai_client = OpenAIClient()

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text."""
        return await self.openai_client.generate_embedding(text)

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

            @retry(
                stop=stop_after_attempt(5),
                wait=wait_exponential(multiplier=1, min=4, max=30),
                reraise=True
            )
            async def _generate_with_retry():
                return await self.openai_client.generate_embeddings_batch(batch)

            embeddings = await _generate_with_retry()
            all_embeddings.extend(embeddings)

            current_count = len(all_embeddings)
            total_count = len(texts)
            logger.info(f"Generated embeddings for batch {i // batch_size + 1}/{max(1, (len(texts) + batch_size - 1) // batch_size)} ({current_count}/{total_count})")

            if on_progress:
                await on_progress(current_count, total_count)

        return all_embeddings
