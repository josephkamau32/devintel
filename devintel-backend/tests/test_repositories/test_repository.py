"""Test repository layer functionality."""

import pytest

from app.repositories.repository import RepositoryRepository
from app.models.repository import IndexingStatus


@pytest.mark.asyncio
async def test_create_repository(db_session, test_user):
    """Test creating a repository."""
    repo_repo = RepositoryRepository(db_session)

    repo_data = {
        "user_id": test_user.id,
        "repo_name": "testrepo",
        "full_name": "testowner/testrepo",
        "description": "Test repository",
        "url": "https://github.com/testowner/testrepo",
        "default_branch": "main",
    }

    repo = await repo_repo.create(**repo_data)

    assert repo.id is not None
    assert repo.repo_name == "testrepo"
    assert repo.full_name == "testowner/testrepo"
    assert repo.indexing_status == IndexingStatus.PENDING


@pytest.mark.asyncio
async def test_get_by_full_name(db_session, test_user, test_repository):
    """Test getting repository by full name."""
    repo_repo = RepositoryRepository(db_session)

    repo = await repo_repo.get_by_full_name(
        full_name=test_repository.full_name,
        user_id=test_user.id,
    )

    assert repo is not None
    assert repo.id == test_repository.id
    assert repo.full_name == test_repository.full_name


@pytest.mark.asyncio
async def test_list_user_repositories(db_session, test_user, test_repository):
    """Test listing user repositories."""
    repo_repo = RepositoryRepository(db_session)

    repos = await repo_repo.get_by_user(test_user.id, skip=0, limit=10)

    assert len(repos) >= 1
    assert any(r.id == test_repository.id for r in repos)


@pytest.mark.asyncio
async def test_update_indexing_status(db_session, test_repository):
    """Test updating repository indexing status."""
    repo_repo = RepositoryRepository(db_session)

    updated = await repo_repo.update(
        test_repository.id,
        indexing_status=IndexingStatus.INDEXING,
        indexing_progress=50
    )

    assert updated.indexing_status == IndexingStatus.INDEXING
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


@pytest.mark.asyncio
async def test_count_by_user(db_session, test_user, test_repository):
    """Test counting repositories for a user."""
    repo_repo = RepositoryRepository(db_session)

    count = await repo_repo.count_by_user(test_user.id)

    assert count >= 1


@pytest.mark.asyncio
async def test_get_by_id(db_session, test_repository):
    """Test getting repository by ID."""
    repo_repo = RepositoryRepository(db_session)

    repo = await repo_repo.get_by_id(test_repository.id)

    assert repo is not None
    assert repo.id == test_repository.id


@pytest.mark.asyncio
async def test_duplicate_detection(db_session, test_user, test_repository):
    """Test that duplicate repository detection works correctly."""
    from uuid import uuid4
    repo_repo = RepositoryRepository(db_session)

    # Should find the existing repo
    existing = await repo_repo.get_by_full_name(
        full_name=test_repository.full_name,
        user_id=test_user.id
    )
    assert existing is not None

    # Should not find for a different user_id (simulate another user)
    not_found = await repo_repo.get_by_full_name(
        full_name=test_repository.full_name,
        user_id=uuid4()
    )
    assert not_found is None


@pytest.mark.asyncio
async def test_last_indexed_at_datetime_roundtrip(db_session, test_repository):
    """Test that last_indexed_at stores and retrieves real datetime objects."""
    from datetime import datetime, timezone
    repo_repo = RepositoryRepository(db_session)

    now = datetime.now(timezone.utc)
    updated = await repo_repo.update(
        test_repository.id,
        last_indexed_at=now,
    )
    await db_session.commit()

    # Read back from database
    fetched = await repo_repo.get_by_id(test_repository.id)
    assert fetched is not None
    assert fetched.last_indexed_at is not None
    assert isinstance(fetched.last_indexed_at, datetime)
    # Check timestamp delta is negligible
    ts_fetched = fetched.last_indexed_at.replace(tzinfo=timezone.utc) if fetched.last_indexed_at.tzinfo is None else fetched.last_indexed_at
    assert abs((ts_fetched - now).total_seconds()) < 2
