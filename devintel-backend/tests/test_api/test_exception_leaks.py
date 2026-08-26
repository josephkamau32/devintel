"""Tests verifying no raw exception details leak to clients across API endpoints (F-09)."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import pytest
from httpx import AsyncClient
from fastapi import HTTPException, Request

from app.models.repository import Repository
from app.models.user import User
from app.api.v1.pr_review import list_pull_requests as pr_review_list_pull_requests


@pytest.mark.asyncio
async def test_pr_review_diff_fetch_exception_leak(
    authenticated_client: AsyncClient,
    test_repository: Repository,
):
    """Test that failure to fetch PR diff from GitHub returns generic 502 without leaking exception text."""
    sensitive_error = "GitHub API 500: internal secret https://api.internal.corp/secret_key=xyz"
    
    with patch("app.api.v1.pr_review.encryption_service.decrypt", return_value="dummy_token"), \
         patch("app.api.v1.pr_review.GitHubClient.get_pull_request_diff", new_callable=AsyncMock, side_effect=RuntimeError(sensitive_error)), \
         patch("app.api.v1.pr_review.logger.error") as mock_logger:
        
        response = await authenticated_client.post(
            "/api/v1/pr-review",
            json={
                "repository_id": str(test_repository.id),
                "pr_title": "Add feature",
                "pr_description": "New feature PR",
                "pr_number": 42,
            },
            headers={"X-Request-ID": "test-pr-diff-req-123"},
        )

        assert response.status_code == 502
        data = response.json()
        assert data["detail"] == "Failed to fetch PR diff from GitHub. Please try again."
        assert "secret_key=xyz" not in response.text
        assert "RuntimeError" not in response.text
        assert "internal.corp" not in response.text

        # Verify logger.error was called with exc_info=True
        mock_logger.assert_called_once()
        _, kwargs = mock_logger.call_args
        assert kwargs.get("exc_info") is True


@pytest.mark.asyncio
async def test_list_pull_requests_endpoint_exception_leak(
    authenticated_client: AsyncClient,
    test_repository: Repository,
):
    """Test that failure to list PRs from GitHub via HTTP endpoint returns generic 502 without leaking exception text."""
    sensitive_error = "GitHub API rate limit exceeded: token ghp_secret123456789 expired"

    with patch("app.api.v1.repositories.encryption_service.decrypt", return_value="dummy_token"), \
         patch("app.api.v1.repositories.GitHubClient.get_repository_pull_requests", new_callable=AsyncMock, side_effect=RuntimeError(sensitive_error)), \
         patch("app.api.v1.repositories.logger.error") as mock_logger:

        response = await authenticated_client.get(
            f"/api/v1/repos/{test_repository.id}/pulls",
            headers={"X-Request-ID": "test-pulls-req-456"},
        )

        assert response.status_code == 502
        data = response.json()
        assert data["detail"] == "Failed to fetch pull requests from GitHub. Please try again."
        assert "ghp_secret123456789" not in response.text
        assert "RuntimeError" not in response.text

        # Verify logger.error was called with exc_info=True
        mock_logger.assert_called_once()
        _, kwargs = mock_logger.call_args
        assert kwargs.get("exc_info") is True


@pytest.mark.asyncio
async def test_pr_review_list_pulls_handler_exception_leak(
    test_repository: Repository,
    test_user: User,
    db_session,
):
    """Directly test pr_review.py's list_pull_requests handler sanitizes exception text and logs exc_info=True."""
    sensitive_error = "GitHub API 500: private token ghp_rawsecret999 failure"
    mock_request = MagicMock(spec=Request)
    mock_request.state.request_id = "test-pr-review-req-999"

    with patch("app.api.v1.pr_review.encryption_service.decrypt", return_value="dummy_token"), \
         patch("app.api.v1.pr_review.GitHubClient.get_repository_pull_requests", new_callable=AsyncMock, side_effect=RuntimeError(sensitive_error)), \
         patch("app.api.v1.pr_review.logger.error") as mock_logger:

        with pytest.raises(HTTPException) as exc_info:
            await pr_review_list_pull_requests(
                repository_id=test_repository.id,
                http_request=mock_request,
                state="open",
                page=1,
                per_page=30,
                current_user=test_user,
                db=db_session,
            )

        assert exc_info.value.status_code == 502
        assert exc_info.value.detail == "Failed to fetch pull requests from GitHub. Please try again."
        assert "ghp_rawsecret999" not in exc_info.value.detail
        assert "RuntimeError" not in exc_info.value.detail

        # Verify logger.error was called with exc_info=True
        mock_logger.assert_called_once()
        _, kwargs = mock_logger.call_args
        assert kwargs.get("exc_info") is True


@pytest.mark.asyncio
async def test_health_score_auto_fix_exception_leak(
    authenticated_client: AsyncClient,
    indexed_repository: Repository,
):
    """Test that failure in auto-fix returns generic 500 without leaking internal error details."""
    sensitive_error = "OpenAI API connection failed: key sk-proj-super-secret-key-123 invalid"

    with patch("app.api.v1.health_score.AutoFixService.generate_and_apply_fix", new_callable=AsyncMock, side_effect=RuntimeError(sensitive_error)), \
         patch("app.api.v1.health_score.logger.error") as mock_logger:

        response = await authenticated_client.post(
            f"/api/v1/repos/{indexed_repository.id}/auto-fix",
            json={"issue_description": "Fix SQL injection vulnerability in user login"},
            headers={"X-Request-ID": "test-autofix-req-789"},
        )

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Failed to generate auto-fix for code health issue. Please try again."
        assert "sk-proj-super-secret-key-123" not in response.text
        assert "RuntimeError" not in response.text

        # Verify logger.error was called with exc_info=True
        mock_logger.assert_called_once()
        _, kwargs = mock_logger.call_args
        assert kwargs.get("exc_info") is True


@pytest.mark.asyncio
async def test_git_blame_exception_leak(
    authenticated_client: AsyncClient,
    test_repository: Repository,
):
    """Test that failure in git blame returns generic 500 without leaking file/server details."""
    sensitive_error = "Git exec failed: fatal: cannot open /var/data/private/keys/.git/config"

    with patch("app.api.v1.git_history.encryption_service.decrypt", return_value="dummy_token"), \
         patch("app.api.v1.git_history.GitHistoryService.get_blame_for_file", new_callable=AsyncMock, side_effect=RuntimeError(sensitive_error)), \
         patch("app.api.v1.git_history.logger.error") as mock_logger:

        response = await authenticated_client.post(
            "/api/v1/git/blame",
            json={
                "repository_id": str(test_repository.id),
                "file_path": "src/main.py",
                "ref": "main",
            },
            headers={"X-Request-ID": "test-blame-req-101"},
        )

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Failed to retrieve blame information for the file."
        assert "/var/data/private/keys" not in response.text
        assert "RuntimeError" not in response.text

        # Verify logger.error was called with exc_info=True
        mock_logger.assert_called_once()
        _, kwargs = mock_logger.call_args
        assert kwargs.get("exc_info") is True
