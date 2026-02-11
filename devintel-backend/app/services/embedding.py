"""Embedding service."""

from typing import List

from app.core.logging import get_logger
from app.integrations.openai_client import OpenAIClient

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating and searching embeddings."""

    def __init__(self):
        """Initialize service."""
        self.openai_client = OpenAIClient()

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        return await self.openai_client.generate_embedding(text)

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 100,
    ) -> List[List[float]]:
        """
        Generate embeddings in batches to handle large volumes.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch
            
        Returns:
            List of embeddings
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = await self.openai_client.generate_embeddings_batch(batch)
            all_embeddings.extend(embeddings)
            logger.info(f"Generated embeddings for batch {i // batch_size + 1}")
        
        return all_embeddings
