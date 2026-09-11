"""Test embedding service functionality."""

from unittest.mock import AsyncMock, patch

import pytest

from app.ai.models import EmbeddingResponse
from app.core.config import settings
from app.core.exceptions import EmbeddingError
from app.services.embedding import EmbeddingService


@pytest.mark.asyncio
async def test_generate_embedding():
    """Test embedding generation."""
    service = EmbeddingService()

    with patch.object(service.orchestrator, "embed", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = [0.1] * settings.EMBEDDING_DIMENSIONS

        result = await service.generate_embedding("test text")

        assert len(result) == settings.EMBEDDING_DIMENSIONS
        assert result[0] == 0.1
        mock_gen.assert_called_once_with("test text", agent="embedding")


@pytest.mark.asyncio
async def test_generate_embeddings_batch():
    """Test batch embedding generation."""
    service = EmbeddingService()
    texts = ["text 1", "text 2", "text 3"]

    with patch.object(service.orchestrator, "embed_batch", new_callable=AsyncMock) as mock_batch_gen:
        mock_batch_gen.return_value = EmbeddingResponse(
            embeddings=[[0.1] * settings.EMBEDDING_DIMENSIONS for _ in texts]
        )

        results = await service.generate_embeddings_batch(texts)

        assert len(results) == 3
        assert all(len(emb) == settings.EMBEDDING_DIMENSIONS for emb in results)
        mock_batch_gen.assert_called()


@pytest.mark.asyncio
async def test_embedding_error_handling():
    """Test error handling in embedding generation."""
    service = EmbeddingService()

    with patch.object(service.orchestrator, "embed", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = EmbeddingError("API Error")

        with pytest.raises(EmbeddingError):
            await service.generate_embedding("test")
