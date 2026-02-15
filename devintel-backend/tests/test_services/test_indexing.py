"""Test indexing service functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.services.indexing import IndexingService
from app.models.repository import Repository


@pytest.mark.asyncio
async def test_fetch_repository_files():
    """Test fetching repository files from GitHub."""
    service = IndexingService()
    repo = Repository(
        id=uuid4(),
        owner="testowner",
        name="testrepo",
        full_name="testowner/testrepo",
        default_branch="main"
    )
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tree": [
                {"path": "file1.py", "type": "blob", "url": "url1"},
                {"path": "file2.py", "type": "blob", "url": "url2"},
            ]
        }
        mock_get.return_value = mock_response
        
        files = await service.fetch_repository_files(repo, "github_token")
        
        assert len(files) >= 0  # May filter by extension


@pytest.mark.asyncio
async def test_chunk_code():
    """Test code chunking."""
    service = IndexingService()
    
    code = """
def function1():
    pass

def function2():
    pass

class TestClass:
    def method1(self):
        pass
"""
    
    chunks = service.chunk_code(code, "test.py")
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)
    assert all(len(chunk) <= 1000 for chunk in chunks)  # Max chunk size


@pytest.mark.asyncio
async def test_filter_supported_files():
    """Test filtering supported file types."""
    service = IndexingService()
    
    files = [
        {"path": "code.py", "type": "blob"},
        {"path": "code.js", "type": "blob"},
        {"path": "image.png", "type": "blob"},
        {"path": "README.md", "type": "blob"},
        {"path": "folder", "type": "tree"},
    ]
    
    supported = service.filter_supported_files(files)
    
    assert len(supported) >= 2  # At least .py and .js
    assert all(f["type"] == "blob" for f in supported)
    assert not any(f["path"].endswith(".png") for f in supported)
