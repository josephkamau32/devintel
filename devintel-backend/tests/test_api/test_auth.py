"""Comprehensive authentication API tests."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, create_refresh_token
from app.models.user import User


@pytest.mark.asyncio
async def test_signup_success(async_client: AsyncClient):
    """Test successful user registration."""
    response = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "newuser@example.com",
            "password": "securepassword123",
            "name": "New User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "newuser@example.com"


@pytest.mark.asyncio
async def test_signup_duplicate_email(async_client: AsyncClient, test_user_token: str):
    """Test signup with existing email fails."""
    # First signup
    await async_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
            "name": "User One",
        },
    )
    # Duplicate signup
    response = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "password456",
            "name": "User Two",
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_signup_weak_password(async_client: AsyncClient):
    """Test signup with password shorter than 8 characters fails."""
    response = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "weakpass@example.com",
            "password": "short",
            "name": "Weak Password User",
        },
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, test_user: User):
    """Test successful login with valid credentials."""
    # First create user with password
    from app.core.security import hash_password
    from app.repositories.user import UserRepository
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        user_repo = UserRepository(db)
        await user_repo.update(test_user.id, hashed_password=get_password_hash("testpassword123"))
        await db.commit()

    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient, test_user: User):
    """Test login with invalid password fails."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient):
    """Test login with nonexistent email fails."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "somepassword",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_token_refresh(async_client: AsyncClient, test_user_token: str):
    """Test token refresh endpoint."""
    response = await async_client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": test_user_token,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_token_refresh_invalid_token(async_client: AsyncClient):
    """Test refresh with invalid token fails."""
    response = await async_client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": "invalid.token.string",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
@patch("app.api.v1.auth.GitHubClient")
@patch("app.api.v1.auth.exchange_code_for_token")
async def test_github_oauth_flow(mock_exchange, mock_github_client_cls, async_client: AsyncClient):
    """Test complete GitHub OAuth flow."""
    mock_exchange.return_value = "mock_github_token"
    mock_github = AsyncMock()
    mock_github.get_user_info.return_value = {
        "github_id": "github_123",
        "login": "githubuser",
        "email": "github@example.com",
        "name": "GitHub User",
        "avatar_url": "https://avatars.githubusercontent.com/u/123",
    }
    mock_github_client_cls.return_value = mock_github

    response = await async_client.get(
        "/api/v1/auth/github/callback?code=mock_code",
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_get_current_user(async_client: AsyncClient, test_user_token: str):
    """Test /me endpoint returns user info."""
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_logout(async_client: AsyncClient, test_user_token: str):
    """Test logout endpoint clears refresh token."""
    response = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert response.status_code == 200
    assert "Logged out" in response.json()["message"]


@pytest.mark.asyncio
async def test_missing_auth_header(async_client: AsyncClient):
    """Test protected endpoint without auth header."""
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 422  # Missing header


@pytest.mark.asyncio
async def test_invalid_auth_header(async_client: AsyncClient):
    """Test protected endpoint with invalid auth header format."""
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "InvalidFormat token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_sql_injection_in_login(async_client: AsyncClient):
    """Test SQL injection attempt in login is blocked."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com'; DROP TABLE users; --",
            "password": "anypassword",
        },
    )
    assert response.status_code == 400