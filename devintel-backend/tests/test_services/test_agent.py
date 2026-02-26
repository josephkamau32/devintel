import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.repository import Repository
from app.services.agent import AgentService


@pytest.fixture
def mock_repository():
    """Mock repository."""
    repo = MagicMock(spec=Repository)
    repo.id = "123e4567-e89b-12d3-a456-426614174000"
    repo.full_name = "testuser/testrepo"
    repo.default_branch = "main"
    return repo


@pytest.fixture
def mock_embedding_repo():
    """Mock embedding repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def agent_service():
    """AgentService instance with mocked clients."""
    with patch("app.services.agent.OpenAIClient") as mock_openai, \
         patch("app.services.agent.GitHubClient") as mock_github, \
         patch("app.services.agent.ChatService") as mock_chat:
        
        service = AgentService("fake_token")
        
        # Setup chat service mock
        service.chat_service.retrieve_relevant_chunks = AsyncMock(return_value=[
            (MagicMock(file_path="src/main.py", chunk_text="def main(): pass"), 0.9)
        ])
        
        # Setup GitHub mock
        service.github_client.create_branch = AsyncMock(return_value="feature/test")
        service.github_client.create_commit = AsyncMock(return_value="fake_sha")
        service.github_client.create_pull_request = AsyncMock(return_value={
            "number": 1,
            "url": "https://github.com/testuser/testrepo/pull/1",
            "title": "Test PR"
        })
        
        yield service


@pytest.mark.asyncio
async def test_draft_pr_plan_success(agent_service, mock_repository, mock_embedding_repo):
    """Test successful PR drafting."""
    # Mock LLM response
    mock_response = MagicMock()
    mock_tool_call = MagicMock()
    
    expected_args = {
        "branch_name": "feature/test",
        "pr_title": "Fix bug",
        "pr_body": "Fixed the bug",
        "commit_message": "fix: bug",
        "file_changes": [{"path": "src/main.py", "content": "def main(): return True"}]
    }
    mock_tool_call.function.arguments = json.dumps(expected_args)
    mock_response.tool_calls = [mock_tool_call]
    agent_service.openai_client.chat_completion = AsyncMock(return_value=mock_response)

    # Execute
    result = await agent_service.draft_pr_plan(
        repository=mock_repository,
        instruction="Fix the bug in main.py",
        embedding_repo=mock_embedding_repo
    )

    # Asserts
    assert result == expected_args
    agent_service.chat_service.retrieve_relevant_chunks.assert_called_once()
    agent_service.openai_client.chat_completion.assert_called_once()


@pytest.mark.asyncio
async def test_draft_pr_plan_missing_tool_call(agent_service, mock_repository, mock_embedding_repo):
    """Test drafting fails gracefully if LLM returns text instead of a tool call."""
    mock_response = MagicMock()
    mock_response.tool_calls = None
    agent_service.openai_client.chat_completion = AsyncMock(return_value=mock_response)

    with pytest.raises(ValueError, match="failed to generate a Pull Request instruction"):
        await agent_service.draft_pr_plan(
            repository=mock_repository,
            instruction="Fix the bug",
            embedding_repo=mock_embedding_repo
        )


@pytest.mark.asyncio
async def test_draft_pr_plan_empty_files(agent_service, mock_repository, mock_embedding_repo):
    """Test drafting fails if no file changes are proposed."""
    mock_response = MagicMock()
    mock_tool_call = MagicMock()
    
    expected_args = {
        "branch_name": "feature/test",
        "pr_title": "Empty",
        "pr_body": "Empty",
        "commit_message": "Empty",
        "file_changes": []
    }
    mock_tool_call.function.arguments = json.dumps(expected_args)
    mock_response.tool_calls = [mock_tool_call]
    agent_service.openai_client.chat_completion = AsyncMock(return_value=mock_response)

    with pytest.raises(ValueError, match="did not suggest any file changes"):
        await agent_service.draft_pr_plan(
            repository=mock_repository,
            instruction="Fix the bug",
            embedding_repo=mock_embedding_repo
        )


@pytest.mark.asyncio
async def test_execute_pr_success(agent_service, mock_repository):
    """Test executing a successfully drafted PR."""
    draft_payload = {
        "branch_name": "feature/test",
        "pr_title": "Fix bug",
        "pr_body": "Fixed the bug",
        "commit_message": "fix: bug",
        "file_changes": [{"path": "src/main.py", "content": "def main(): return True"}]
    }

    result = await agent_service.execute_pr(
        repository=mock_repository,
        draft_payload=draft_payload,
        default_branch="main"
    )

    assert result["pr_url"] == "https://github.com/testuser/testrepo/pull/1"
    assert result["pr_number"] == 1
    assert result["branch_name"] == "feature/test"

    agent_service.github_client.create_branch.assert_called_once_with(
        full_name="testuser/testrepo",
        base_branch="main",
        new_branch_name="feature/test"
    )
    agent_service.github_client.create_commit.assert_called_once_with(
        full_name="testuser/testrepo",
        branch_name="feature/test",
        file_changes=draft_payload["file_changes"],
        commit_message="fix: bug"
    )
    agent_service.github_client.create_pull_request.assert_called_once()
