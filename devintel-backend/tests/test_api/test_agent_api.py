"""Tests for agent API endpoints (/api/v1/chat/draft and /api/v1/chat/execute)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.models.repository import Repository
from app.models.user import User


DRAFT_URL = "/api/v1/chat/draft"
EXECUTE_URL = "/api/v1/chat/execute"


class TestAgentDraftEndpoint:
    """Test suite for POST /api/v1/chat/draft."""

    @pytest.mark.asyncio
    async def test_draft_success(
        self,
        authenticated_client: AsyncClient,
        indexed_repository: Repository,
    ):
        """Successful draft returns the LLM-generated PR plan."""
        draft_payload = {
            "branch_name": "feature/add-tests",
            "pr_title": "Add unit tests",
            "pr_body": "This PR adds unit tests for the utils module.",
            "commit_message": "test: add unit tests for utils",
            "file_changes": [
                {"path": "tests/test_utils.py", "content": "def test_add(): assert 1+1 == 2"}
            ],
        }

        with patch("app.api.v1.chat.AgentService") as MockAgent, \
             patch("app.api.v1.chat.encryption_service") as mock_enc:
            mock_enc.decrypt.return_value = "fake_gh_token"
            instance = MockAgent.return_value
            instance.draft_pr_plan = AsyncMock(return_value=draft_payload)

            response = await authenticated_client.post(
                DRAFT_URL,
                json={
                    "repository_id": str(indexed_repository.id),
                    "instruction": "Add unit tests for the utils module",
                },
            )

        assert response.status_code == 200
        body = response.json()
        assert body["draft"]["pr_title"] == "Add unit tests"
        assert len(body["draft"]["file_changes"]) == 1

    @pytest.mark.asyncio
    async def test_draft_repo_not_found(self, authenticated_client: AsyncClient):
        """Returns 404 when repository does not exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await authenticated_client.post(
            DRAFT_URL,
            json={"repository_id": fake_id, "instruction": "Do something useful"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_draft_unindexed_repo(
        self,
        authenticated_client: AsyncClient,
        test_repository: Repository,
    ):
        """Returns 400 when repository has not been indexed."""
        response = await authenticated_client.post(
            DRAFT_URL,
            json={
                "repository_id": str(test_repository.id),
                "instruction": "Refactor the login component",
            },
        )
        assert response.status_code == 400
        assert "indexed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_draft_no_github_token(
        self,
        authenticated_client: AsyncClient,
        indexed_repository: Repository,
        db_session,
        test_user: User,
    ):
        """Returns 400 when user has no encrypted GitHub token."""
        # Remove the token
        test_user.github_access_token_encrypted = None
        db_session.add(test_user)
        await db_session.commit()

        response = await authenticated_client.post(
            DRAFT_URL,
            json={
                "repository_id": str(indexed_repository.id),
                "instruction": "Refactor the login component",
            },
        )
        assert response.status_code == 400
        assert "token" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_draft_llm_value_error(
        self,
        authenticated_client: AsyncClient,
        indexed_repository: Repository,
    ):
        """Returns 400 when AgentService raises ValueError."""
        with patch("app.api.v1.chat.AgentService") as MockAgent, \
             patch("app.api.v1.chat.encryption_service") as mock_enc:
            mock_enc.decrypt.return_value = "fake_gh_token"
            instance = MockAgent.return_value
            instance.draft_pr_plan = AsyncMock(
                side_effect=ValueError("The AI failed to generate a Pull Request instruction.")
            )

            response = await authenticated_client.post(
                DRAFT_URL,
                json={
                    "repository_id": str(indexed_repository.id),
                    "instruction": "Implement something vague",
                },
            )

        assert response.status_code == 400
        assert "failed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_draft_unauthorized(self, async_client: AsyncClient):
        """Rejects unauthenticated requests."""
        response = await async_client.post(
            DRAFT_URL,
            json={
                "repository_id": "00000000-0000-0000-0000-000000000000",
                "instruction": "Do something",
            },
        )
        assert response.status_code in (401, 422)


class TestAgentExecuteEndpoint:
    """Test suite for POST /api/v1/chat/execute."""

    @pytest.mark.asyncio
    async def test_execute_success(
        self,
        authenticated_client: AsyncClient,
        indexed_repository: Repository,
    ):
        """Successful execution returns the PR URL and metadata."""
        draft = {
            "branch_name": "feature/add-tests",
            "pr_title": "Add unit tests",
            "pr_body": "Adds tests",
            "commit_message": "test: add tests",
            "file_changes": [
                {"path": "tests/test_utils.py", "content": "assert True"}
            ],
        }

        with patch("app.api.v1.chat.AgentService") as MockAgent, \
             patch("app.api.v1.chat.encryption_service") as mock_enc:
            mock_enc.decrypt.return_value = "fake_gh_token"
            instance = MockAgent.return_value
            instance.execute_pr = AsyncMock(return_value={
                "pr_url": "https://github.com/test-user/test-repo/pull/42",
                "pr_number": 42,
                "branch_name": "feature/add-tests",
            })

            response = await authenticated_client.post(
                EXECUTE_URL,
                json={
                    "repository_id": str(indexed_repository.id),
                    "draft": draft,
                },
            )

        assert response.status_code == 200
        body = response.json()
        assert body["pr_number"] == 42
        assert "github.com" in body["pr_url"]

    @pytest.mark.asyncio
    async def test_execute_repo_not_found(self, authenticated_client: AsyncClient):
        """Returns 404 when repository does not exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        draft = {
            "branch_name": "fix/bug",
            "pr_title": "Fix",
            "pr_body": "Fix",
            "commit_message": "fix",
            "file_changes": [{"path": "x.py", "content": "pass"}],
        }
        response = await authenticated_client.post(
            EXECUTE_URL,
            json={"repository_id": fake_id, "draft": draft},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_execute_github_failure(
        self,
        authenticated_client: AsyncClient,
        indexed_repository: Repository,
    ):
        """Returns 500 when GitHub API call inside execute_pr fails."""
        draft = {
            "branch_name": "feature/x",
            "pr_title": "X",
            "pr_body": "X",
            "commit_message": "x",
            "file_changes": [{"path": "x.py", "content": "pass"}],
        }

        with patch("app.api.v1.chat.AgentService") as MockAgent, \
             patch("app.api.v1.chat.encryption_service") as mock_enc:
            mock_enc.decrypt.return_value = "fake_gh_token"
            instance = MockAgent.return_value
            instance.execute_pr = AsyncMock(
                side_effect=Exception("GitHub API 422: branch already exists")
            )

            response = await authenticated_client.post(
                EXECUTE_URL,
                json={
                    "repository_id": str(indexed_repository.id),
                    "draft": draft,
                },
            )

        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_execute_unauthorized(self, async_client: AsyncClient):
        """Rejects unauthenticated requests."""
        draft = {
            "branch_name": "fix/bug",
            "pr_title": "Fix",
            "pr_body": "Fix",
            "commit_message": "fix",
            "file_changes": [{"path": "x.py", "content": "pass"}],
        }
        response = await async_client.post(
            EXECUTE_URL,
            json={
                "repository_id": "00000000-0000-0000-0000-000000000000",
                "draft": draft,
            },
        )
        assert response.status_code in (401, 422)
