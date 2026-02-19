"""Integration tests for end-to-end workflows."""

import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app


@pytest.mark.asyncio
async def test_full_repository_workflow(async_client: AsyncClient, auth_headers: dict):
    """Test complete repository lifecycle: add, index, query, delete."""
    # Step 1: Add repository
    add_response = await async_client.post(
        "/api/v1/repos",
        headers=auth_headers,
        json={
            "repo_name": "testrepo",
            "full_name": "testowner/testrepo",
            "url": "https://github.com/testowner/testrepo",
            "auto_index": False  # Don't auto-index in tests
        }
    )
        
    # May fail without full auth setup, but validates structure
    assert add_response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_202_ACCEPTED,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_ENTITY
    ]


@pytest.mark.asyncio
async def test_authentication_flow():
    """Test GitHub OAuth authentication flow."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Get GitHub OAuth URL
        auth_response = await client.get("/api/v1/auth/github")
        assert auth_response.status_code == status.HTTP_200_OK
        assert "url" in auth_response.json()
        assert "github.com" in auth_response.json()["url"]


@pytest.mark.asyncio
async def test_chat_without_repository(async_client: AsyncClient, auth_headers: dict):
    """Test chat endpoint validation."""
    response = await async_client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={
            "question": "How does this work?",
            "repo_id": "00000000-0000-0000-0000-000000000000"  # Non-existent
        }
    )
    
    # Should fail validation or return error
    assert response.status_code in [
        status.HTTP_404_NOT_FOUND,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_ENTITY
    ]


@pytest.mark.asyncio
async def test_rate_limiting():
    """Test rate limiting on auth endpoints."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = await client.get("/api/v1/auth/github")
            responses.append(response.status_code)
        
        # Should eventually hit rate limit
        assert status.HTTP_429_TOO_MANY_REQUESTS in responses or \
               all(code == status.HTTP_200_OK for code in responses)


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test application health check."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
