"""Test chat service functionality."""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.models.embedding import Embedding
from app.models.repository import Repository
from app.services.chat import ChatService


@pytest.mark.asyncio
async def test_chat_service_retrieve_chunks():
    """Test retrieving relevant code chunks."""
    # Mock repository
    repo = Repository(
        id=uuid4(),
        repo_name="repo",
        full_name="test/repo",
        user_id=uuid4(), # required field
        url="https://github.com/test/repo", # required field
        indexing_status="complete",
    )

    # Mock embeddings
    mock_embeddings = [
        (Embedding(id=uuid4(), chunk_text="def test(): pass", file_path="test.py", chunk_index=0), 0.95),
        (Embedding(id=uuid4(), chunk_text="class TestClass: pass", file_path="test.py", chunk_index=1), 0.90),
    ]

    # Mock embedding repository
    mock_embedding_repo = Mock()
    mock_embedding_repo.vector_search = AsyncMock(return_value=mock_embeddings)
    mock_embedding_repo.get_neighbors = AsyncMock(side_effect=lambda **kwargs: [emb for emb, sim in mock_embeddings if emb.file_path == kwargs.get("file_path") and emb.chunk_index == kwargs.get("chunk_index")])

    # Mock embedding service
    mock_embedding_service = Mock()
    mock_embedding_service.generate_embedding = AsyncMock(return_value=[0.1] * 1536)

    # Create chat service
    with patch("app.services.chat.EmbeddingService", return_value=mock_embedding_service):
        chat_service = ChatService()
        # Inject mock if needed or rely on patched class
        chat_service.embedding_service = mock_embedding_service

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
    chat_service = ChatService()

    # Create mock embeddings
    emb1 = Mock(spec=Embedding)
    emb1.chunk_text = "Code chunk 1"
    emb1.file_path = "file1.py"
    emb1.chunk_index = 0

    emb2 = Mock(spec=Embedding)
    emb2.chunk_text = "Code chunk 2"
    emb2.file_path = "file2.py"
    emb2.chunk_index = 1

    context_chunks = [
        (emb1, 0.9),
        (emb2, 0.8),
    ]

    prompt = chat_service.build_system_prompt("test-repo", context_chunks)

    assert "file1.py" in prompt
    assert "file2.py" in prompt
    assert "Code chunk 1" in prompt
    assert "Code chunk 2" in prompt
    assert "test-repo" in prompt
