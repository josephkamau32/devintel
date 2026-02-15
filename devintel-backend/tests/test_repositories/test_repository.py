"""Test repository layer functionality."""

import pytest
from uuid import uuid4

from app.repositories.repository import RepositoryRepository
from app.models.repository import Repository


@pytest.mark.asyncio
async def test_create_repository(db_session, test_user):
    """Test creating a repository."""
    repo_repo = RepositoryRepository(db_session)
    
    repo_data = {
        "user_id": test_user.id,
        "owner": "testowner",
        "name": "testrepo",
        "full_name": "testowner/testrepo",
        "description": "Test repository",
        "html_url": "https://github.com/testowner/testrepo",
        "default_branch": "main",
    }
    
    repo = await repo_repo.create(**repo_data)
    
    assert repo.id is not None
    assert repo.owner == "testowner"
    assert repo.name == "testrepo"
    assert repo.is_indexed is False
    assert repo.indexing_status == "pending"


@pytest.mark.asyncio
async def test_get_by_full_name(db_session, test_user, test_repository):
    """Test getting repository by full name."""
    repo_repo = RepositoryRepository(db_session)
    
    repo = await repo_repo.get_by_full_name(
        test_user.id,
        test_repository.full_name
    )
    
    assert repo is not None
    assert repo.id == test_repository.id
    assert repo.full_name == test_repository.full_name


@pytest.mark.asyncio
async def test_list_user_repositories(db_session, test_user, test_repository):
    """Test listing user repositories."""
    repo_repo = RepositoryRepository(db_session)
    
    repos = await repo_repo.list_by_user(test_user.id, skip=0, limit=10)
    
    assert len(repos) >= 1
    assert any(r.id == test_repository.id for r in repos)


@pytest.mark.asyncio
async def test_update_indexing_status(db_session, test_repository):
    """Test updating repository indexing status."""
    repo_repo = RepositoryRepository(db_session)
    
    updated = await repo_repo.update_indexing_status(
        test_repository.id,
        status="indexing",
        progress=50
    )
    
    assert updated.indexing_status == "indexing"
    assert updated.indexing_progress == 50


@pytest.mark.asyncio
async def test_delete_repository(db_session, test_repository):
    """Test deleting a repository."""
    repo_repo = RepositoryRepository(db_session)
    
    result = await repo_repo.delete(test_repository.id)
    
    assert result is True
    
    # Verify deletion
    deleted = await repo_repo.get_by_id(test_repository.id)
    assert deleted is None
