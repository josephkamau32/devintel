"""Test authentication endpoints."""

import pytest
from fastapi import status
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_github_login_redirect():
    """Test GitHub OAuth login redirect."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/github")

        assert response.status_code == status.HTTP_200_OK
        assert "url" in response.json()
        assert "github.com/login/oauth/authorize" in response.json()["url"]


@pytest.mark.asyncio
async def test_get_current_user_unauthenticated(async_client: AsyncClient):
    """Test getting current user without authentication."""
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 422  # Standard FastAPI behavior for missing required header


@pytest.mark.asyncio
async def test_get_current_user_authenticated(async_client: AsyncClient, auth_headers: dict):
    """Test getting current user with authentication."""
    response = await async_client.get(
        "/api/v1/auth/me",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
