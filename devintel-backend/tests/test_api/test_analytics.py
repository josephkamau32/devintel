"""Tests for analytics endpoints."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.models.repository import IndexingStatus, Repository
from app.models.user import User


class TestAnalyticsEndpoints:
    """Test suite for analytics dashboard endpoint."""

    @pytest.mark.asyncio
    async def test_dashboard_unauthenticated(self, async_client: AsyncClient):
        """Test that unauthenticated requests are rejected."""
        response = await async_client.get("/api/v1/analytics/dashboard")
        assert response.status_code in [401, 403, 422]

    @pytest.mark.asyncio
    async def test_dashboard_empty_user(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test dashboard returns zeros for a user with no activity."""
        response = await authenticated_client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 200

        data = response.json()
        assert data["total_queries"] == 0
        assert data["total_tokens"] == 0
        assert data["total_repos_indexed"] == 0
        assert data["usage_trend"] == []
        assert data["top_repositories"] == []
        assert data["last_active_at"] is None

    @pytest.mark.asyncio
    async def test_dashboard_derived_from_real_records(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test dashboard derives all numbers honestly from real Repository and Chat records."""
        # 1. Repositories: 2 completed, 1 indexing
        repo1 = Repository(
            repo_name="core-backend",
            full_name="testorg/core-backend",
            user_id=test_user.id,
            indexing_status=IndexingStatus.COMPLETE,
        )
        repo2 = Repository(
            repo_name="web-frontend",
            full_name="testorg/web-frontend",
            user_id=test_user.id,
            indexing_status=IndexingStatus.INDEXING,
        )
        repo3 = Repository(
            repo_name="docs-hub",
            full_name="testorg/docs-hub",
            user_id=test_user.id,
            indexing_status=IndexingStatus.COMPLETE,
        )
        db_session.add_all([repo1, repo2, repo3])
        await db_session.commit()
        await db_session.refresh(repo1)
        await db_session.refresh(repo2)
        await db_session.refresh(repo3)

        # 2. Chat records for test_user
        now = datetime.now(UTC)
        yesterday = now - timedelta(days=1)
        chat1 = Chat(
            user_id=test_user.id,
            repo_id=repo1.id,
            question="How does auth work?",
            response="Auth uses JWT.",
            agent_type="chat",
            token_usage=120,
            input_tokens=70,
            output_tokens=50,
            created_at=now,
        )
        chat2 = Chat(
            user_id=test_user.id,
            repo_id=repo1.id,
            question="Where is the DB pool configured?",
            response="In app/db/session.py",
            agent_type="chat",
            token_usage=230,
            input_tokens=150,
            output_tokens=80,
            created_at=now,
        )
        chat3 = Chat(
            user_id=test_user.id,
            repo_id=repo3.id,
            question="Explain API endpoints",
            response="See openapi docs.",
            agent_type="chat",
            token_usage=150,
            input_tokens=100,
            output_tokens=50,
            created_at=yesterday,
        )
        db_session.add_all([chat1, chat2, chat3])
        await db_session.commit()

        response = await authenticated_client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 200

        data = response.json()
        # Only completed repos are counted (repo1, repo3)
        assert data["total_repos_indexed"] == 2
        # Total queries matches Chat rows (chat1, chat2, chat3)
        assert data["total_queries"] == 3
        # Total tokens matches sum of Chat token_usage (120 + 230 + 150)
        assert data["total_tokens"] == 500
        assert data["last_active_at"] is not None

        # Top repositories by queries
        assert len(data["top_repositories"]) == 2
        top_repo_map = {r["repo_name"]: r["queries"] for r in data["top_repositories"]}
        assert top_repo_map["core-backend"] == 2
        assert top_repo_map["docs-hub"] == 1

        # Usage trend
        assert len(data["usage_trend"]) >= 1
        trend_total = sum(d["queries"] for d in data["usage_trend"])
        assert trend_total == 3

    @pytest.mark.asyncio
    async def test_chat_stream_persists_chat_record_and_updates_dashboard(
        self,
        authenticated_client: AsyncClient,
        indexed_repository: Repository,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test streaming chat persists the answer and token counts and increments dashboard numbers."""
        with patch("app.api.v1.chat.ChatService") as mock_chat_service_cls:
            mock_service = mock_chat_service_cls.return_value
            mock_service.retrieve_relevant_chunks = AsyncMock(return_value=[])

            async def mock_stream(*args, **kwargs):
                yield "Hello "
                yield "from "
                yield "DevIntel!"

            mock_service.stream_chat = mock_stream
            mock_service.count_messages_tokens.return_value = 45
            mock_service.count_tokens.return_value = 15

            payload = {"question": "What is DevIntel?"}

            stream_res = await authenticated_client.post(
                f"/api/v1/chat/{indexed_repository.id}/stream",
                json=payload,
            )
            assert stream_res.status_code == 200
            assert "text/event-stream" in stream_res.headers.get("content-type", "")

            # Verify chat record was persisted
            chat_records = (
                await db_session.execute(
                    select(Chat).where(Chat.user_id == test_user.id)
                )
            ).scalars().all()
            assert len(chat_records) == 1
            chat = chat_records[0]
            assert chat.question == "What is DevIntel?"
            assert chat.response == "Hello from DevIntel!"
            assert chat.input_tokens == 45
            assert chat.output_tokens == 15
            assert chat.token_usage == 60

            # Verify dashboard reflects the new query
            dash_res = await authenticated_client.get("/api/v1/analytics/dashboard")
            assert dash_res.status_code == 200
            dash_data = dash_res.json()
            assert dash_data["total_queries"] == 1
            assert dash_data["total_tokens"] == 60
            assert dash_data["total_repos_indexed"] == 1
            assert len(dash_data["top_repositories"]) == 1
            assert dash_data["top_repositories"][0]["queries"] == 1
