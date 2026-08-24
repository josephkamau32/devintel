"""Tests for chat endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import Repository


class TestChatEndpoints:
    """Test suite for RAG chat endpoints."""

    @pytest.mark.asyncio
    async def test_chat_with_indexed_repository(
        self,
        authenticated_client: AsyncClient,
        indexed_repository: Repository,
    ):
        """Test chatting with an indexed repository."""
        with patch("app.api.v1.chat.ChatService") as MockChatService:
            mock_service = MockChatService.return_value
            mock_service.retrieve_relevant_chunks = AsyncMock(return_value=[
                {
                    "file_path": "test.py",
                    "chunk_text": "def hello(): return 'world'",
                    "similarity": 0.95,
                }
            ])

            async def mock_stream(*args, **kwargs):
                for chunk in ["Hello", " from", " AI"]:
                    yield chunk

            mock_service.stream_chat = mock_stream

            payload = {
                "question": "What does the hello function do?",
            }

            response = await authenticated_client.post(
                f"/api/v1/chat/{indexed_repository.id}/stream",
                json=payload,
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_chat_with_unindexed_repository(
        self, authenticated_client: AsyncClient, test_repository: Repository
    ):
        """Test chatting with a repository that hasn't been indexed yet."""
        payload = {
            "question": "What does this code do?",
        }

        # Should return 400 error since repository is not indexed
        response = await authenticated_client.post(
            f"/api/v1/chat/{test_repository.id}/stream",
            json=payload,
        )
        assert response.status_code == 400
        assert "must be fully indexed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_chat_with_nonexistent_repository(
        self, authenticated_client: AsyncClient
    ):
        """Test chatting with a repository that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        payload = {"question": "Test question"}

        response = await authenticated_client.post(
            f"/api/v1/chat/{fake_id}/stream",
            json=payload,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_chat_unauthorized(self, async_client: AsyncClient, test_repository: Repository):
        """Test chat endpoint without authentication."""
        payload = {
            "question": "Test question",
        }
        response = await async_client.post(
            f"/api/v1/chat/{test_repository.id}/stream",
            json=payload,
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_chat_missing_payload(
        self, authenticated_client: AsyncClient, indexed_repository: Repository
    ):
        """Test chat with missing required payload fields."""
        payload = {}

        response = await authenticated_client.post(
            f"/api/v1/chat/{indexed_repository.id}/stream",
            json=payload,
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_chat_streaming_response(
        self, authenticated_client: AsyncClient, indexed_repository: Repository
    ):
        """Test that chat response is streamed via SSE."""
        with patch("app.api.v1.chat.ChatService") as MockChatService:
            mock_service = MockChatService.return_value
            mock_service.retrieve_relevant_chunks = AsyncMock(return_value=[])

            async def mock_stream(*args, **kwargs):
                yield "Hello "
                yield "World"

            mock_service.stream_chat = mock_stream

            payload = {
                "question": "Test",
            }

            response = await authenticated_client.post(
                f"/api/v1/chat/{indexed_repository.id}/stream",
                json=payload,
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_chat_error_handling(
        self, authenticated_client: AsyncClient, indexed_repository: Repository
    ):
        """Test chat error handling when retrieval fails."""
        with patch("app.api.v1.chat.ChatService") as MockChatService:
            mock_service = MockChatService.return_value
            mock_service.retrieve_relevant_chunks = AsyncMock(side_effect=Exception(
                "OpenAI API error"
            ))

            payload = {
                "question": "Test",
            }

            response = await authenticated_client.post(
                f"/api/v1/chat/{indexed_repository.id}/stream",
                json=payload,
            )
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_chat_stream_error_returns_generic_message_without_leaking_exception(
        self, async_client: AsyncClient, test_user_token: str, test_repository: Repository, db_session: AsyncSession, caplog
    ):
        """Test chat SSE stream error returns generic error payload without leaking internal exception (Finding C)."""
        test_repository.indexing_status = "complete"
        await db_session.commit()
        await db_session.refresh(test_repository)

        with patch("app.api.v1.chat.ChatService") as MockChatService:
            mock_service = MockChatService.return_value
            mock_service.retrieve_relevant_chunks = AsyncMock(return_value=[])

            async def mock_failing_stream(*args, **kwargs):
                raise RuntimeError("Internal secret OpenAI model key leak: sk-secret-12345")
                yield "never"

            mock_service.stream_chat = mock_failing_stream

            response = await async_client.post(
                f"/api/v1/chat/{test_repository.id}/stream",
                json={"question": "What is this?"},
                headers={
                    "Authorization": f"Bearer {test_user_token}",
                    "X-Request-ID": "test-chat-stream-req-123",
                },
            )

            assert response.status_code == 200, f"Status: {response.status_code}, Body: {response.text}"
            assert "text/event-stream" in response.headers.get("content-type", "")
            response_text = response.text

            # Check that client gets generic error
            assert "An error occurred while processing your request." in response_text
            assert "test-chat-stream-req-123" in response_text

            # Check that raw exception and sensitive keys are NOT in response
            assert "RuntimeError" not in response_text
            assert "sk-secret-12345" not in response_text

            # Check server-side error was logged
            assert any(
                record.levelname == "ERROR" and "test-chat-stream-req-123" in record.message
                for record in caplog.records
            )

