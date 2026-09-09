import json
from unittest.mock import AsyncMock, patch

import pytest

from app.services.auto_fix_service import AutoFixService


@pytest.mark.asyncio
@patch("app.services.auto_fix_service.get_orchestrator")
@patch("app.services.auto_fix_service.EmbeddingService")
async def test_generate_fix_with_linter_retry(mock_embedding_cls, mock_orch):
    """Test that _generate_fix retries when the LLM produces syntax errors."""
    service = AutoFixService()
    service.orchestrator = AsyncMock()

    file_contents = {"src/test.py": "def test():\n    pass"}

    # Mock LLM responses:
    # 1. First attempt: Broken Python code with syntax error (missing colon)
    # 2. Second attempt: Good Python code

    bad_json = {
        "pr_title": "Fix",
        "pr_summary": "Sum",
        "modified_files": [
            {
                "file_path": "src/test.py",
                "search_block": "def test():\n    pass",
                "replace_block": "def test()  # syntax error missing colon\n    return True"
            }
        ]
    }

    good_json = {
        "pr_title": "Fix",
        "pr_summary": "Sum",
        "modified_files": [
            {
                "file_path": "src/test.py",
                "search_block": "def test():\n    pass",
                "replace_block": "def test():\n    return True"
            }
        ]
    }

    # Mocking openai response objects
    class MockResponse:
        def __init__(self, content):
            self.content = content

    service.orchestrator.complete.side_effect = [
        MockResponse(json.dumps(bad_json)),
        MockResponse(json.dumps(good_json))
    ]

    result = await service._generate_fix("repo", "issue", file_contents)

    # Assert it eventually succeeded
    assert "modified_files" in result
    assert result["modified_files"][0]["new_content"] == "def test():\n    return True"

    # Assert orchestrator was called exactly 2 times (initial failure + 1 retry)
    assert service.orchestrator.complete.call_count == 2
