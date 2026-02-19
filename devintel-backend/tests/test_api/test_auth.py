"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, MagicMock

from app.models.user import User


class TestAuthEndpoints:
    """Test suite for authentication endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test health check endpoint is accessible."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "devintel-ai"

    @pytest.mark.asyncio
    async def test_github_oauth_url(self, async_client: AsyncClient):
        """Test GitHub OAuth URL generation."""
        response = await async_client.get("/api/v1/auth/github")
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "github.com/login/oauth/authorize" in data["url"]
        assert "client_id" in data["url"]

    @pytest.mark.asyncio
    async def test_github_callback_success(
        self, async_client: AsyncClient, db_session: AsyncSession, mock_github_client
    ):
        """Test successful GitHub OAuth callback."""
        with patch("app.api.v1.auth.GitHubClient", return_value=mock_github_client):
            with patch("app.api.v1.auth.exchange_code_for_token") as mock_exchange:
                mock_exchange.return_value = "test_access_token"

                response = await async_client.get(
                    "/api/v1/auth/github/callback",
                    params={"code": "test_auth_code"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
                assert "token_type" in data
                assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_github_callback_no_code(self, async_client: AsyncClient):
        """Test GitHub callback without authorization code."""
        response = await async_client.get("/api/v1/auth/github/callback")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_current_user(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test getting current authenticated user info."""
        response = await authenticated_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert data["github_id"] == test_user.github_id

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, async_client: AsyncClient):
        """Test accessing protected endpoint without authentication."""
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, async_client: AsyncClient):
        """Test accessing protected endpoint with invalid token."""
        async_client.headers["Authorization"] = "Bearer invalid_token_here"
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_jwt_token_expiration(self, async_client: AsyncClient):
        """Test that expired JWT tokens are rejected."""
        # Create an expired token (you'd need to implement this)
        expired_token = "expired.jwt.token"
        async_client.headers["Authorization"] = f"Bearer {expired_token}"
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 401
