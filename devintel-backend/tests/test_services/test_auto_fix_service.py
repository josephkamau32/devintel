"""Tests for the AutoFixService."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import APIError
from app.models.repository import Repository
from app.models.user import User
from app.services.auto_fix_service import AutoFixService


@pytest.fixture
def mock_user():
    return User(
        id=uuid.uuid4(),
        email="test@example.com",
        name="Test User",
        github_id="12345",
        github_access_token="fake-token",
    )


@pytest.fixture
def mock_repository(mock_user):
    return Repository(
        id=uuid.uuid4(),
        repo_name="devintel",
        full_name="josephkamau32/devintel",
        url="https://github.com/josephkamau32/devintel",
        user_id=mock_user.id,
        indexed_status=True,
    )


@pytest.mark.asyncio
async def test_generate_and_apply_fix_no_token(mock_repository, mock_user):
    """Test auto-fix fails if user has no GitHub token."""
    mock_user.github_access_token = None
    service = AutoFixService()
    
    with pytest.raises(APIError, match="GitHub access token required"):
        await service.generate_and_apply_fix(
            repository=mock_repository,
            issue_description="Fix bug",
            user=mock_user,
            embedding_repo=AsyncMock(),
        )


@pytest.mark.asyncio
@patch("app.services.auto_fix_service.GitHubClient")
@patch("app.services.auto_fix_service.OpenAIClient")
@patch("app.services.auto_fix_service.EmbeddingService")
async def test_generate_and_apply_fix_success(
    mock_embedding_cls, 
    mock_openai_cls, 
    mock_github_cls, 
    mock_repository, 
    mock_user
):
    """Test the full happy path for Auto-Fix."""
    # Setup Mocks
    mock_embedding_svc = AsyncMock()
    mock_embedding_cls.return_value = mock_embedding_svc
    mock_embedding_svc.generate_embedding.return_value = [0.1] * 1536
    
    # Mock search results returning 1 file chunk
    mock_embedding_repo = AsyncMock()
    mock_chunk = MagicMock()
    mock_chunk.file_path = "src/main.py"
    mock_embedding_repo.vector_search.return_value = [(mock_chunk, 0.9)]
    
    # Mock GitHub
    mock_github = AsyncMock()
    mock_github_cls.return_value = mock_github
    mock_github.get_user_repositories.return_value = [{"full_name": "josephkamau32/devintel"}]
    mock_github.create_pull_request.return_value = {"url": "https://github.com/pr/1", "number": 1, "title": "Auto-fix"}
    
    # Make the asyncio.to_thread mock return valid branch and content
    with patch("app.services.auto_fix_service.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
        # We call to_thread 2 times in the good path in auto_fix_service:
        # 1. get_repo_details -> {'default_branch': 'main'}
        # 2. get_file_content -> 'print("hello")'
        mock_thread.side_effect = [
            {"default_branch": "main"},
            'print("hello")'
        ]
        
        # Mock LLM Parse Result
        service = AutoFixService()
        with patch.object(service, '_generate_fix', new_callable=AsyncMock) as mock_gen_fix:
            mock_gen_fix.return_value = {
                "pr_title": "Fixed bug",
                "pr_summary": "Summary here",
                "modified_files": [
                    {
                        "file_path": "src/main.py",
                        "new_content": "print('hello world!')"
                    }
                ]
            }

            result = await service.generate_and_apply_fix(
                repository=mock_repository,
                issue_description="Make it say hello world",
                user=mock_user,
                embedding_repo=mock_embedding_repo,
            )
            
            assert result["status"] == "success"
            assert result["pr_url"] == "https://github.com/pr/1"
            assert mock_github.create_branch.called
            assert mock_github.create_commit.called
            assert mock_github.create_pull_request.called
