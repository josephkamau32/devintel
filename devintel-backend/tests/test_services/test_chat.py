"""Test chat service functionality."""

import pytest
from uuid import UUID, uuid4
from unittest.mock import Mock, AsyncMock, patch

from app.services.chat import ChatService
from app.models.repository import Repository
from app.models.embedding import Embedding


@pytest.mark.asyncio
async def test_chat_service_retrieve_chunks():
    """Test retrieving relevant code chunks."""
    # Mock repository
    repo = Repository(
        id=uuid4(),
        owner="test",
        name="repo",
        full_name="test/repo",
        is_indexed=True,
    )
    
    # Mock embeddings
    mock_embeddings = [
        (Embedding(id=uuid4(), chunk_text="def test(): pass", file_path="test.py"), 0.95),
        (Embedding(id=uuid4(), chunk_text="class TestClass: pass", file_path="test.py"), 0.90),
    ]
    
    # Mock embedding repository
    mock_embedding_repo = Mock()
    mock_embedding_repo.vector_search = AsyncMock(return_value=mock_embeddings)
    
    # Mock embedding service
    mock_embedding_service = Mock()
    mock_embedding_service.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
    
    # Create chat service
    chat_service = ChatService(embedding_service=mock_embedding_service)
    
    # Test retrieve
    results = await chat_service.retrieve_relevant_chunks(
        repo_id=repo.id,
        question="How do I test?",
        embedding_repo=mock_embedding_repo,
        top_k=2,
    )
    
    assert len(results) == 2
    assert results[0][1] == 0.95  # Check similarity score
    assert "def test()" in results[0][0].chunk_text


@pytest.mark.asyncio
async def test_chat_service_builds_prompt():
    """Test system prompt building."""
    mock_embedding_service = Mock()
    chat_service = ChatService(embedding_service=mock_embedding_service)
    
    code_chunks = [
        ("# Code chunk 1", "file1.py"),
        ("# Code chunk 2", "file2.py"),
    ]
    
    prompt = chat_service._build_system_prompt(code_chunks)
    
    assert "file1.py" in prompt
    assert "file2.py" in prompt
    assert "Code chunk 1" in prompt
    assert "Code chunk 2" in prompt
