"""Tests for repository endpoints."""

from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import Repository
from app.models.user import User


class TestRepositoryEndpoints:
    """Test suite for repository management endpoints."""

    @pytest.mark.asyncio
    async def test_list_repositories(
        self, authenticated_client: AsyncClient, test_repository: Repository
    ):
        """Test listing user repositories."""
        response = await authenticated_client.get("/api/v1/repos")
        assert response.status_code == 200
        data = response.json()
        assert "repositories" in data
        assert isinstance(data["repositories"], list)
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_repositories_unauthorized(self, async_client: AsyncClient):
        """Test listing repositories without authentication."""
        response = await async_client.get("/api/v1/repos")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_add_repository(
        self, authenticated_client: AsyncClient, db_session: AsyncSession
    ):
        """Test adding a new repository."""
        payload = {
            "repo_name": "newrepo",
            "full_name": "newuser/newrepo",
            "url": "https://github.com/newuser/newrepo.git",
            "default_branch": "main",
        }
        response = await authenticated_client.post("/api/v1/repos", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == payload["full_name"]
        assert data["indexing_status"] == "pending"
        assert data["default_branch"] == "main"

    @pytest.mark.asyncio
    async def test_add_duplicate_repository(
        self, authenticated_client: AsyncClient, test_repository: Repository
    ):
        """Test adding a repository that already exists."""
        payload = {
            "repo_name": test_repository.repo_name,
            "full_name": test_repository.full_name,
            "url": test_repository.url,
        }
        response = await authenticated_client.post("/api/v1/repos", json=payload)
        assert response.status_code == 409  # Conflict
        data = response.json()
        assert "already connected" in data["detail"]

    @pytest.mark.asyncio
    async def test_search_not_indexed_returns_400(
        self, authenticated_client: AsyncClient, test_repository: Repository
    ):
        """Test that search on an un-indexed repository returns 400."""
        response = await authenticated_client.get(
            f"/api/v1/repos/{test_repository.id}/search",
            params={"q": "authentication logic"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "not indexed" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_trigger_indexing(
        self, authenticated_client: AsyncClient, test_repository: Repository, db_session: AsyncSession
    ):
        """Test triggering repository indexing enqueues a durable job in DB."""
        response = await authenticated_client.post(
            "/api/v1/repos/index", json={"repository_id": str(test_repository.id)}
        )
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data

        from app.repositories.indexing_job import IndexingJobRepository
        job_repo = IndexingJobRepository(db_session)
        jobs = await job_repo.get_by_repository(test_repository.id)
        assert len(jobs) == 1
        job = jobs[0]
        assert job.job_type == "full"
        assert job.status == "pending"
        assert job.payload["repo_id"] == str(test_repository.id)
        assert str(job.id) == data["task_id"]

    @pytest.mark.asyncio
    async def test_trigger_indexing_already_indexed(
        self, authenticated_client: AsyncClient, indexed_repository: Repository, db_session: AsyncSession
    ):
        """Test triggering indexing on already indexed repository enqueues a new job."""
        response = await authenticated_client.post(
            "/api/v1/repos/index",
            json={"repository_id": str(indexed_repository.id)},
        )
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data

        from app.repositories.indexing_job import IndexingJobRepository
        job_repo = IndexingJobRepository(db_session)
        jobs = await job_repo.get_by_repository(indexed_repository.id)
        assert len(jobs) == 1
        assert jobs[0].job_type == "full"
        assert str(jobs[0].id) == data["task_id"]

    @pytest.mark.asyncio
    async def test_refresh_code_health(
        self, authenticated_client: AsyncClient, indexed_repository: Repository, db_session: AsyncSession
    ):
        """Test manually triggering code health re-analysis enqueues a code_health job."""
        response = await authenticated_client.post(
            f"/api/v1/repos/{indexed_repository.id}/health/refresh"
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"
        assert "task_id" in data

        from app.repositories.indexing_job import IndexingJobRepository
        job_repo = IndexingJobRepository(db_session)
        jobs = await job_repo.get_by_repository(indexed_repository.id)
        assert len(jobs) == 1
        job = jobs[0]
        assert job.job_type == "code_health"
        assert job.status == "pending"
        assert job.payload["repo_id"] == str(indexed_repository.id)
        assert str(job.id) == data["task_id"]

    @pytest.mark.asyncio
    async def test_get_repository_by_id(
        self, authenticated_client: AsyncClient, test_repository: Repository
    ):
        """Test getting a repository by ID."""
        response = await authenticated_client.get(f"/api/v1/repos/{test_repository.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_repository.id)
        assert data["full_name"] == test_repository.full_name

    @pytest.mark.asyncio
    async def test_get_repository_not_found(self, authenticated_client: AsyncClient):
        """Test getting a non-existent repository."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await authenticated_client.get(f"/api/v1/repos/{fake_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_repository(
        self, authenticated_client: AsyncClient, test_repository: Repository
    ):
        """Test deleting a repository."""
        response = await authenticated_client.delete(
            f"/api/v1/repos/{test_repository.id}"
        )
        assert response.status_code == 200

        # Verify it's deleted
        get_response = await authenticated_client.get(
            f"/api/v1/repos/{test_repository.id}"
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_repository_unauthorized(
        self, async_client: AsyncClient, test_repository: Repository
    ):
        """Test deleting repository without authentication."""
        response = await async_client.delete(f"/api/v1/repos/{test_repository.id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_repository_permissions(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        """Test that users can only access their own repositories."""
        # Create another user's repository
        other_user = User(
            github_id="other_123",
            email="other@example.com",
            full_name="Other User",
            avatar_url="https://example.com/avatar.jpg",
        )
        db_session.add(other_user)
        await db_session.commit()

        other_repo = Repository(
            user_id=other_user.id,
            repo_name="repo",
            full_name="other/repo",
            url="https://github.com/other/repo.git",
            indexing_status="pending",
        )
        db_session.add(other_repo)
        await db_session.commit()

        # Try to access other user's repository
        response = await authenticated_client.get(f"/api/v1/repos/{other_repo.id}")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_repository_url(
        self, authenticated_client: AsyncClient
    ):
        """Test adding repository with invalid URL."""
        payload = {
            "full_name": "user/repo",
            "clone_url": "not_a_valid_url",
        }
        response = await authenticated_client.post("/api/v1/repos", json=payload)
        assert response.status_code == 422
