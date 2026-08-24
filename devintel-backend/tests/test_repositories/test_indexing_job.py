"""Unit and integration tests for IndexingJobRepository."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.indexing_job import IndexingJob
from app.models.repository import Repository
from app.repositories.indexing_job import IndexingJobRepository

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def job_db_session():
    """Isolated database session fixture for indexing job repository tests."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def sample_repo_id(job_db_session: AsyncSession) -> uuid4:
    """Create a sample repository and return its ID."""
    repo_id = uuid4()
    user_id = uuid4()
    repo = Repository(
        id=repo_id,
        user_id=user_id,
        repo_name="test-repo",
        full_name="org/test-repo",
        description="Test repo for indexing jobs",
        url="https://github.com/org/test-repo",
        default_branch="main",
    )
    job_db_session.add(repo)
    await job_db_session.flush()
    return repo_id


@pytest.mark.asyncio
async def test_enqueue_creates_pending_job(job_db_session: AsyncSession, sample_repo_id):
    """Test that enqueue inserts a new row with status='pending' and correct defaults."""
    repo = IndexingJobRepository(job_db_session)
    payload = {"commit_sha": "abc1234", "branch": "main"}

    job = await repo.enqueue(
        repository_id=sample_repo_id,
        job_type="full",
        payload=payload,
        max_attempts=3,
    )

    assert job.id is not None
    assert job.repository_id == sample_repo_id
    assert job.job_type == "full"
    assert job.status == "pending"
    assert job.payload == payload
    assert job.attempt_count == 0
    assert job.max_attempts == 3
    assert job.error_message is None
    assert job.locked_at is None
    assert job.locked_by is None
    assert job.completed_at is None
    assert job.created_at is not None
    assert job.updated_at is not None


@pytest.mark.asyncio
async def test_dequeue_next_claims_oldest_pending_job(job_db_session: AsyncSession, sample_repo_id):
    """Test that dequeue_next claims the oldest pending job and updates lock/status fields."""
    repo = IndexingJobRepository(job_db_session)

    job1 = await repo.enqueue(sample_repo_id, "incremental", {"order": 1})
    # Small offset to guarantee created_at ordering
    job2 = await repo.enqueue(sample_repo_id, "full", {"order": 2})

    worker_id = "worker-node-1"
    claimed = await repo.dequeue_next(worker_id=worker_id)

    assert claimed is not None
    assert claimed.id == job1.id
    assert claimed.status == "running"
    assert claimed.locked_by == worker_id
    assert claimed.locked_at is not None
    assert claimed.attempt_count == 1
    assert claimed.payload == {"order": 1}


@pytest.mark.asyncio
async def test_dequeue_next_returns_none_when_empty(job_db_session: AsyncSession):
    """Test that dequeue_next returns None when no pending jobs exist."""
    repo = IndexingJobRepository(job_db_session)
    claimed = await repo.dequeue_next(worker_id="worker-empty-test")
    assert claimed is None


@pytest.mark.asyncio
async def test_dequeue_next_does_not_claim_running_or_completed_jobs(
    job_db_session: AsyncSession, sample_repo_id
):
    """Test that running and completed jobs are skipped by dequeue_next."""
    repo = IndexingJobRepository(job_db_session)

    job = await repo.enqueue(sample_repo_id, "full", {"step": 1})

    # First worker claims the job
    worker_1_job = await repo.dequeue_next(worker_id="worker-1")
    assert worker_1_job is not None
    assert worker_1_job.id == job.id
    assert worker_1_job.status == "running"

    # Second worker attempts to claim — since only 1 job exists and it is 'running', None is returned
    worker_2_job = await repo.dequeue_next(worker_id="worker-2")
    assert worker_2_job is None

    # Complete the job
    await repo.mark_complete(job.id)

    # Third worker attempts to claim — completed job is not claimed
    worker_3_job = await repo.dequeue_next(worker_id="worker-3")
    assert worker_3_job is None


@pytest.mark.asyncio
async def test_mark_complete_sets_status_and_completed_at(
    job_db_session: AsyncSession, sample_repo_id
):
    """Test mark_complete updates status to 'complete', sets completed_at, and releases locks."""
    repo = IndexingJobRepository(job_db_session)
    job = await repo.enqueue(sample_repo_id, "code_health")
    claimed = await repo.dequeue_next("worker-1")
    assert claimed is not None

    completed = await repo.mark_complete(job.id)

    assert completed is not None
    assert completed.status == "complete"
    assert completed.completed_at is not None
    assert completed.locked_at is None
    assert completed.locked_by is None


@pytest.mark.asyncio
async def test_mark_failed_retries_when_under_max_attempts(
    job_db_session: AsyncSession, sample_repo_id
):
    """Test mark_failed resets status to 'pending' if attempt_count < max_attempts."""
    repo = IndexingJobRepository(job_db_session)
    job = await repo.enqueue(sample_repo_id, "full", max_attempts=3)

    # Attempt 1
    claimed = await repo.dequeue_next("worker-1")
    assert claimed.attempt_count == 1

    updated = await repo.mark_failed(job.id, error_message="Transient network timeout")
    assert updated is not None
    assert updated.status == "pending"  # Retried
    assert updated.error_message == "Transient network timeout"
    assert updated.locked_at is None
    assert updated.locked_by is None

    # Job can be dequeued again
    claimed_again = await repo.dequeue_next("worker-2")
    assert claimed_again is not None
    assert claimed_again.id == job.id
    assert claimed_again.attempt_count == 2


@pytest.mark.asyncio
async def test_mark_failed_permanently_fails_when_max_attempts_reached(
    job_db_session: AsyncSession, sample_repo_id
):
    """Test mark_failed transitions to status='failed' once max_attempts are reached."""
    repo = IndexingJobRepository(job_db_session)
    job = await repo.enqueue(sample_repo_id, "pr_review", max_attempts=2)

    # Attempt 1
    await repo.dequeue_next("worker-1")
    await repo.mark_failed(job.id, error_message="First failure")

    # Attempt 2 (exhausts max_attempts)
    claimed_2 = await repo.dequeue_next("worker-1")
    assert claimed_2.attempt_count == 2

    failed = await repo.mark_failed(job.id, error_message="Permanent syntax error in repo")
    assert failed is not None
    assert failed.status == "failed"  # Permanently failed
    assert failed.error_message == "Permanent syntax error in repo"
    assert failed.locked_at is None
    assert failed.locked_by is None

    # Ensure it cannot be dequeued anymore
    next_claim = await repo.dequeue_next("worker-3")
    assert next_claim is None


@pytest.mark.asyncio
async def test_recover_orphaned_jobs_resets_stale_and_ignores_fresh(
    job_db_session: AsyncSession, sample_repo_id
):
    """Test recover_orphaned_jobs recovers stale running jobs and preserves fresh running jobs."""
    repo = IndexingJobRepository(job_db_session)

    # 1. Stale job with retry attempts remaining (locked 45 min ago)
    stale_retryable = await repo.enqueue(sample_repo_id, "full", max_attempts=3)
    stale_retryable.status = "running"
    stale_retryable.attempt_count = 1
    stale_retryable.locked_at = datetime.now(timezone.utc) - timedelta(minutes=45)
    stale_retryable.locked_by = "dead-worker-1"

    # 2. Stale job with attempts exhausted (locked 60 min ago)
    stale_exhausted = await repo.enqueue(sample_repo_id, "incremental", max_attempts=1)
    stale_exhausted.status = "running"
    stale_exhausted.attempt_count = 1
    stale_exhausted.locked_at = datetime.now(timezone.utc) - timedelta(minutes=60)
    stale_exhausted.locked_by = "dead-worker-2"

    # 3. Fresh running job (locked 5 min ago)
    fresh_running = await repo.enqueue(sample_repo_id, "code_health", max_attempts=3)
    fresh_running.status = "running"
    fresh_running.attempt_count = 1
    fresh_running.locked_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    fresh_running.locked_by = "active-worker-3"

    # 4. Completed job (locked 50 min ago, but completed)
    completed_job = await repo.enqueue(sample_repo_id, "pr_review")
    completed_job.status = "complete"
    completed_job.completed_at = datetime.now(timezone.utc) - timedelta(minutes=40)

    await job_db_session.flush()

    # Recover with 30 minute stale threshold
    recovered_count = await repo.recover_orphaned_jobs(stale_after_minutes=30)
    assert recovered_count == 2

    # Check stale retryable was reset to pending
    await job_db_session.refresh(stale_retryable)
    assert stale_retryable.status == "pending"
    assert stale_retryable.locked_at is None
    assert stale_retryable.locked_by is None

    # Check stale exhausted was set to failed
    await job_db_session.refresh(stale_exhausted)
    assert stale_exhausted.status == "failed"
    assert stale_exhausted.locked_at is None
    assert stale_exhausted.locked_by is None

    # Check fresh running job was not touched
    await job_db_session.refresh(fresh_running)
    assert fresh_running.status == "running"
    assert fresh_running.locked_by == "active-worker-3"
    assert fresh_running.locked_at is not None

    # Check completed job remains complete
    await job_db_session.refresh(completed_job)
    assert completed_job.status == "complete"


@pytest.mark.asyncio
async def test_get_by_repository_and_get_active_job(job_db_session: AsyncSession, sample_repo_id):
    """Test get_by_repository and get_active_job queries."""
    repo = IndexingJobRepository(job_db_session)
    other_repo_id = uuid4()

    job1 = await repo.enqueue(sample_repo_id, "full")
    job2 = await repo.enqueue(sample_repo_id, "incremental")
    job_other = await repo.enqueue(other_repo_id, "full")

    # Get by repository
    repo_jobs = await repo.get_by_repository(sample_repo_id)
    assert len(repo_jobs) == 2
    assert all(j.repository_id == sample_repo_id for j in repo_jobs)

    # Active job detection
    active = await repo.get_active_job(sample_repo_id)
    assert active is not None
    assert active.id in {job1.id, job2.id}

    # Mark both complete
    await repo.mark_complete(job1.id)
    await repo.mark_complete(job2.id)

    # No more active jobs
    active_after = await repo.get_active_job(sample_repo_id)
    assert active_after is None
