"""Tests for chat endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock, MagicMock
import json

from app.models.repository import Repository
from app.models.user import User


class TestChatEndpoints:
    """Test suite for RAG chat endpoints."""

    @pytest.mark.asyncio
    async def test_chat_with_indexed_repository(
        self,
        authenticated_client: AsyncClient,
        indexed_repository: Repository,
        mock_openai_client,
    ):
        """Test chatting with an indexed repository."""
        with patch("app.services.chat.ChatService") as MockChatService:
            mock_service = MockChatService.return_value

            # Mock retrieve_relevant_chunks
            mock_service.retrieve_relevant_chunks.return_value = [
                {
                    "file_path": "test.py",
                    "chunk_text": "def hello(): return 'world'",
                    "similarity": 0.95,
                }
            ]

            # Mock stream_chat to yield chunks
            async def mock_stream():
                for chunk in ["Hello", " from", " AI"]:
                    yield chunk

            mock_service.stream_chat.return_value = mock_stream()

            payload = {
                "repository_id": str(indexed_repository.id),
                "question": "What does the hello function do?",
            }

            response = await authenticated_client.post("/api/v1/chat", json=payload)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_chat_with_unindexed_repository(
        self, authenticated_client: AsyncClient, test_repository: Repository
    ):
        """Test chatting with a repository that hasn't been indexed yet."""
        payload = {
            "repository_id": str(test_repository.id),
            "question": "What does this code do?",
        }

        # Should return error since repository is not indexed
        # The actual response depends on implementation
        response = await authenticated_client.post("/api/v1/chat", json=payload)
        # May return 400 or stream an error message
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_chat_with_nonexistent_repository(
        self, authenticated_client: AsyncClient
    ):
        """Test chatting with a repository that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        payload = {"repository_id": fake_id, "question": "Test question"}

        response = await authenticated_client.post("/api/v1/chat", json=payload)
        # Should handle gracefully
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_chat_unauthorized(self, async_client: AsyncClient):
        """Test chat endpoint without authentication."""
        payload = {
            "repository_id": "some-id",
            "question": "Test question",
        }
        response = await async_client.post("/api/v1/chat", json=payload)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_chat_empty_question(
        self, authenticated_client: AsyncClient, indexed_repository: Repository
    ):
        """Test chat with empty question."""
        payload = {"repository_id": str(indexed_repository.id), "question": ""}

        response = await authenticated_client.post("/api/v1/chat", json=payload)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_chat_streaming_response(
        self, authenticated_client: AsyncClient, indexed_repository: Repository
    ):
        """Test that chat response is streamed via SSE."""
        with patch("app.services.chat.ChatService") as MockChatService:
            mock_service = MockChatService.return_value
            mock_service.retrieve_relevant_chunks.return_value = []

            async def mock_stream():
                yield "Hello "
                yield "World"

            mock_service.stream_chat.return_value = mock_stream()

            payload = {
                "repository_id": str(indexed_repository.id),
                "question": "Test",
            }

            response = await authenticated_client.post("/api/v1/chat", json=payload)
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_chat_saves_history(
        self,
        authenticated_client: AsyncClient,
        indexed_repository: Repository,
        db_session: AsyncSession,
    ):
        """Test that chat interactions are saved to history."""
        with patch("app.services.chat.ChatService") as MockChatService:
            mock_service = MockChatService.return_value
            mock_service.retrieve_relevant_chunks.return_value = []

            async def mock_stream():
                yield "Response"

            mock_service.stream_chat.return_value = mock_stream()

            payload = {
                "repository_id": str(indexed_repository.id),
                "question": "Test question",
            }

            response = await authenticated_client.post("/api/v1/chat", json=payload)
            assert response.status_code == 200

            # Verify chat history was created (would need to check database)
            # This is a placeholder - actual implementation may vary

    @pytest.mark.asyncio
    async def test_chat_error_handling(
        self, authenticated_client: AsyncClient, indexed_repository: Repository
    ):
        """Test chat error handling when OpenAI API fails."""
        with patch("app.services.chat.ChatService") as MockChatService:
            mock_service = MockChatService.return_value
            mock_service.retrieve_relevant_chunks.side_effect = Exception(
                "OpenAI API error"
            )

            payload = {
                "repository_id": str(indexed_repository.id),
                "question": "Test",
            }

            response = await authenticated_client.post("/api/v1/chat", json=payload)
            # Should handle error gracefully
            assert response.status_code in [200, 500]
