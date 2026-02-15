"""Test embedding service functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import numpy as np

from app.services.embedding import EmbeddingService


@pytest.mark.asyncio
async def test_generate_embedding():
    """Test embedding generation."""
    service = EmbeddingService()
    
    with patch('openai.embeddings.create') as mock_create:
        mock_create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )
        
        result = await service.generate_embedding("test text")
        
        assert len(result) == 1536
        assert all(isinstance(x, float) for x in result)


@pytest.mark.asyncio
async def test_batch_generate_embeddings():
    """Test batch embedding generation."""
    service = EmbeddingService()
    texts = ["text 1", "text 2", "text 3"]
    
    with patch('openai.embeddings.create') as mock_create:
        mock_create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536) for _ in texts]
        )
        
        results = await service.batch_generate_embeddings(texts)
        
        assert len(results) == 3
        assert all(len(emb) == 1536 for emb in results)


@pytest.mark.asyncio
async def test_compute_similarity():
    """Test cosine similarity computation."""
    service = EmbeddingService()
    
    # Identical vectors should have similarity ~1.0
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    similarity = service.compute_similarity(vec1, vec2)
    assert abs(similarity - 1.0) < 0.01
    
    # Orthogonal vectors should have similarity ~0.0
    vec3 = [0.0, 1.0, 0.0]
    similarity = service.compute_similarity(vec1, vec3)
    assert abs(similarity - 0.0) < 0.01


@pytest.mark.asyncio
async def test_embedding_error_handling():
    """Test error handling in embedding generation."""
    service = EmbeddingService()
    
    with patch('openai.embeddings.create') as mock_create:
        mock_create.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            await service.generate_embedding("test")
