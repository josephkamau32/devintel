"""Tests for analytics endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import Analytics
from app.models.chat import Chat
from app.models.repository import Repository
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
    async def test_dashboard_with_analytics_record(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test dashboard returns correct totals when analytics record exists."""
        analytics = Analytics(
            user_id=test_user.id,
            query_count=42,
            token_usage=15000,
            repositories_indexed=3,
        )
        db_session.add(analytics)
        await db_session.commit()

        response = await authenticated_client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 200

        data = response.json()
        assert data["total_queries"] == 42
        assert data["total_tokens"] == 15000
        assert data["total_repos_indexed"] == 3
