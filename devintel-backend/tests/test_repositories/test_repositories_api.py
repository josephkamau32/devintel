import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, MagicMock, AsyncMock

from app.models.user import User
from app.models.repository import Repository
from app.services.encryption import encryption_service
import app.api.v1.repositories


@pytest.fixture
async def auth_token(client: AsyncClient, db_session: AsyncSession):
    # Create user with github token
    signup = await client.post("/api/v1/auth/signup", json={
        "email": "repo_user@example.com",
        "password": "Password1",
        "full_name": "Repo User",
    })
    token = signup.json()["access_token"]
    
    # Manually add github token to user
    from sqlalchemy import select
    result = await db_session.execute(select(User).filter_by(email="repo_user@example.com"))
    user = result.scalar_one()
    user.github_token_encrypted = encryption_service.encrypt("mock_github_token")
    await db_session.commit()
    
    return token


@pytest.mark.asyncio
async def test_list_github_repositories(client: AsyncClient, auth_token: str):
    mock_repos = [
        {"id": 1, "name": "repo-1", "full_name": "user/repo-1", "private": False, "html_url": "https://github.com/user/repo-1", "description": "Desc 1", "stargazers_count": 10, "language": "Python", "default_branch": "main"},
        {"id": 2, "name": "repo-2", "full_name": "user/repo-2", "private": True, "html_url": "https://github.com/user/repo-2", "description": "Desc 2", "stargazers_count": 5, "language": "TypeScript", "default_branch": "main"},
    ]
    
    with patch("app.api.v1.repositories.GitHubClient") as mock_client_class:
        mock_instance = mock_client_class.return_value
        mock_instance.get_user_repositories = AsyncMock(return_value=mock_repos)
        
        response = await client.get("/api/v1/repos/github", headers={"Authorization": f"Bearer {auth_token}"})
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["repositories"]) == 2
        assert data["repositories"][0]["full_name"] == "user/repo-1"


@pytest.mark.asyncio
async def test_create_and_list_repositories(client: AsyncClient, auth_token: str):
    # Connect a repository
    repo_data = {
        "repo_name": "my-repo",
        "full_name": "user/my-repo",
        "description": "A test repo",
        "url": "https://github.com/user/my-repo",
        "stars": 42,
        "language": "Python",
        "default_branch": "main"
    }
    
    response = await client.post("/api/v1/repos", json=repo_data, headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 200
    created = response.json()
    assert created["full_name"] == "user/my-repo"
    assert created["id"] is not None
    
    # List connected repos
    list_response = await client.get("/api/v1/repos", headers={"Authorization": f"Bearer {auth_token}"})
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["total"] == 1
    assert list_data["repositories"][0]["id"] == created["id"]


@pytest.mark.asyncio
async def test_duplicate_repository(client: AsyncClient, auth_token: str):
    repo_data = {
        "repo_name": "dup-repo",
        "full_name": "user/dup-repo",
        "url": "https://github.com/user/dup-repo",
        "default_branch": "main"
    }
    await client.post("/api/v1/repos", json=repo_data, headers={"Authorization": f"Bearer {auth_token}"})
    
    response2 = await client.post("/api/v1/repos", json=repo_data, headers={"Authorization": f"Bearer {auth_token}"})
    assert response2.status_code == 409
    assert "already connected" in response2.json()["detail"]


@pytest.mark.asyncio
async def test_index_repository(client: AsyncClient, auth_token: str):
    # Connect repo first
    repo_data = {
        "repo_name": "index-repo",
        "full_name": "user/index-repo",
        "url": "https://github.com/user/index-repo",
        "default_branch": "main"
    }
    repo_res = await client.post("/api/v1/repos", json=repo_data, headers={"Authorization": f"Bearer {auth_token}"})
    repo_id = repo_res.json()["id"]
    
    with patch("app.api.v1.repositories.index_repository_task") as mock_task:
        response = await client.post("/api/v1/repos/index", json={"repository_id": repo_id}, headers={"Authorization": f"Bearer {auth_token}"})
        
        assert response.status_code == 200
        assert response.json()["message"] == "Indexing started"
        
        # Check status
        status_res = await client.get(f"/api/v1/repos/{repo_id}/status", headers={"Authorization": f"Bearer {auth_token}"})
        assert status_res.status_code == 200
        assert status_res.json()["indexed_status"] == "pending"
