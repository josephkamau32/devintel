"""Test embedding service functionality."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import EmbeddingError
from app.services.embedding import EmbeddingService


@pytest.mark.asyncio
async def test_generate_embedding():
    """Test embedding generation."""
    service = EmbeddingService()

    # Mock the OpenAIClient.generate_embedding method directly
    with patch('app.integrations.openai_client.OpenAIClient.generate_embedding', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = [0.1] * 1536

        result = await service.generate_embedding("test text")

        assert len(result) == 1536
        assert result[0] == 0.1
        mock_gen.assert_called_once_with("test text")


@pytest.mark.asyncio
async def test_generate_embeddings_batch():
    """Test batch embedding generation."""
    service = EmbeddingService()
    texts = ["text 1", "text 2", "text 3"]

    # Mock the OpenAIClient.generate_embeddings_batch method
    with patch('app.integrations.openai_client.OpenAIClient.generate_embeddings_batch', new_callable=AsyncMock) as mock_batch_gen:
        # It should return a list of embeddings (lists of floats)
        mock_batch_gen.return_value = [[0.1] * 1536 for _ in texts]

        results = await service.generate_embeddings_batch(texts)

        assert len(results) == 3
        assert all(len(emb) == 1536 for emb in results)
        mock_batch_gen.assert_called()


@pytest.mark.asyncio
async def test_embedding_error_handling():
    """Test error handling in embedding generation."""
    service = EmbeddingService()

    with patch('app.integrations.openai_client.OpenAIClient.generate_embedding', new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = EmbeddingError("API Error")

        with pytest.raises(EmbeddingError):
            await service.generate_embedding("test")
