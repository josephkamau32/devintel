"""Integration tests for the background job poller.

Uses an in-memory SQLite database with StaticPool so multiple concurrent
sessions in worker loops and tests share the exact same database.
Handlers are monkeypatched with fast fakes so tests need no network/GitHub.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.models.base import Base
from app.models.indexing_job import IndexingJob
from app.models.repository import Repository
from app.models.user import User
from app.repositories.indexing_job import IndexingJobRepository
from app.services.job_poller import run_worker_loop, start_poller, stop_poller


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def poller_env(monkeypatch):
    """Set up an in-memory SQLite database with StaticPool and wire it to job_poller."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Patch AsyncSessionLocal in job_poller to use the in-memory SQLite DB
    monkeypatch.setattr("app.services.job_poller.AsyncSessionLocal", TestSessionLocal)

    # Create a test user and repository
    async with TestSessionLocal() as session:
        user = User(
            email="poller_test@example.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Poller Test User",
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.flush()

        repo = Repository(
            user_id=user.id,
            repo_name="poller-test-repo",
            full_name="testowner/poller-test-repo",
            description="Repo for poller tests",
            url="https://github.com/testowner/poller-test-repo",
            default_branch="main",
        )
        session.add(repo)
        await session.commit()
        await session.refresh(repo)
        repo_id = repo.id

    yield TestSessionLocal, repo_id

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _enqueue(
    session_factory,
    repo_id: UUID,
    job_type: str = "code_health",
    payload: dict | None = None,
    max_attempts: int = 3,
) -> UUID:
    """Enqueue a job via a dedicated session and return its id."""
    async with session_factory() as session:
        job_repo = IndexingJobRepository(session)
        job = await job_repo.enqueue(
            repository_id=repo_id,
            job_type=job_type,
            payload=payload or {"repo_id": str(repo_id)},
            max_attempts=max_attempts,
        )
        await session.commit()
        return job.id


async def _get_job(session_factory, job_id: UUID) -> IndexingJob | None:
    """Fetch a job fresh from the DB using a dedicated session."""
    async with session_factory() as session:
        job_repo = IndexingJobRepository(session)
        return await job_repo.get_by_id(job_id)


# ---------------------------------------------------------------------------
# Test 1: Worker picks up and completes a job
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_worker_picks_up_and_completes_job(poller_env, monkeypatch):
    """A pending job should be dequeued, dispatched, and marked complete."""
    session_factory, repo_id = poller_env

    # Enqueue a fake code_health job
    job_id = await _enqueue(session_factory, repo_id, "code_health")
    job = await _get_job(session_factory, job_id)
    assert job is not None
    assert job.status == "pending"

    fake_code_health = AsyncMock()
    monkeypatch.setattr(
        "app.tasks.code_health.compute_code_health_task",
        fake_code_health,
    )
    monkeypatch.setattr("app.services.job_poller.settings.JOB_POLL_INTERVAL_SECONDS", 0.05)

    stop = asyncio.Event()

    async def _stop_when_done():
        for _ in range(30):
            await asyncio.sleep(0.05)
            j = await _get_job(session_factory, job_id)
            if j and j.status == "complete":
                break
        stop.set()

    await asyncio.gather(
        run_worker_loop("test-worker-0", stop),
        _stop_when_done(),
    )

    refreshed = await _get_job(session_factory, job_id)
    assert refreshed is not None
    assert refreshed.status == "complete", f"Expected 'complete', got '{refreshed.status}'"
    assert refreshed.completed_at is not None
    fake_code_health.assert_awaited_once()


# ---------------------------------------------------------------------------
# Test 2: Failed dispatch marks job failed (or re-queued as pending)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_failed_dispatch_marks_job_failed_or_retried(poller_env, monkeypatch):
    """A job whose handler raises should be marked failed when max_attempts is reached."""
    session_factory, repo_id = poller_env

    # Enqueue with max_attempts=1 so first failure → 'failed'
    job_id = await _enqueue(
        session_factory, repo_id, "code_health",
        max_attempts=1,
    )

    stop = asyncio.Event()

    # Monkeypatch handler to always raise
    async def _boom(repo_id: str) -> dict:
        stop.set()
        raise RuntimeError("simulated handler failure")

    monkeypatch.setattr("app.tasks.code_health.compute_code_health_task", _boom)
    monkeypatch.setattr("app.services.job_poller.settings.JOB_POLL_INTERVAL_SECONDS", 0.05)

    await run_worker_loop("test-worker-fail", stop)

    refreshed = await _get_job(session_factory, job_id)
    assert refreshed is not None
    assert refreshed.status == "failed", f"Expected 'failed', got '{refreshed.status}'"
    assert refreshed.error_message is not None
    assert "simulated handler failure" in refreshed.error_message


@pytest.mark.asyncio
async def test_failed_dispatch_retries_if_attempts_remain(poller_env, monkeypatch):
    """A job that fails with attempts remaining should be reset to 'pending'."""
    session_factory, repo_id = poller_env

    job_id = await _enqueue(
        session_factory, repo_id, "code_health",
        max_attempts=3,
    )

    stop = asyncio.Event()

    async def _boom(repo_id: str) -> dict:
        stop.set()  # Stop worker immediately after this attempt
        raise RuntimeError("transient failure")

    monkeypatch.setattr("app.tasks.code_health.compute_code_health_task", _boom)
    monkeypatch.setattr("app.services.job_poller.settings.JOB_POLL_INTERVAL_SECONDS", 0.05)

    await run_worker_loop("test-worker-retry", stop)

    refreshed = await _get_job(session_factory, job_id)
    assert refreshed is not None
    assert refreshed.status == "pending", f"Expected 'pending', got '{refreshed.status}'"
    assert refreshed.error_message is not None
    assert refreshed.attempt_count >= 1


# ---------------------------------------------------------------------------
# Test 3: stop_poller stops the loop
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_stop_poller_stops_loop(poller_env, monkeypatch):
    """After stop_poller, no more jobs should be claimed."""
    session_factory, repo_id = poller_env

    fake_code_health = AsyncMock()
    monkeypatch.setattr(
        "app.tasks.code_health.compute_code_health_task",
        fake_code_health,
    )

    monkeypatch.setattr("app.services.job_poller.settings.JOB_POLL_INTERVAL_SECONDS", 0.05)
    monkeypatch.setattr("app.services.job_poller.settings.JOB_POLLER_CONCURRENCY", 1)

    stop_event = asyncio.Event()
    task = asyncio.create_task(
        run_worker_loop("test-worker-stop", stop_event),
        name="test-stop-worker",
    )
    tasks = [task]

    # Let worker start and poll
    await asyncio.sleep(0.1)

    # Stop the poller
    await stop_poller(tasks, stop_event, timeout=2.0)

    # Now enqueue a job AFTER stop
    job_id = await _enqueue(session_factory, repo_id, "code_health")

    # Wait to confirm the stopped worker does not claim it
    await asyncio.sleep(0.15)

    refreshed = await _get_job(session_factory, job_id)
    assert refreshed is not None
    assert refreshed.status == "pending", (
        f"Job should still be 'pending' after stop, got '{refreshed.status}'"
    )
    fake_code_health.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test 4: recover_orphaned_jobs is invoked on start_poller
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_recover_orphaned_jobs_on_start(poller_env, monkeypatch):
    """Pre-seeded stale 'running' job should be recovered and reprocessed."""
    session_factory, repo_id = poller_env

    stale_time = datetime.now(timezone.utc) - timedelta(hours=2)
    async with session_factory() as session:
        job_repo = IndexingJobRepository(session)
        stale_job = await job_repo.enqueue(
            repository_id=repo_id,
            job_type="code_health",
            payload={"repo_id": str(repo_id)},
        )
        stale_job.status = "running"
        stale_job.locked_at = stale_time
        stale_job.locked_by = "dead-worker-999"
        stale_job.attempt_count = 1
        await session.commit()
        stale_job_id = stale_job.id

    fake_code_health = AsyncMock()
    monkeypatch.setattr(
        "app.tasks.code_health.compute_code_health_task",
        fake_code_health,
    )

    monkeypatch.setattr("app.services.job_poller.settings.JOB_POLL_INTERVAL_SECONDS", 0.05)
    monkeypatch.setattr("app.services.job_poller.settings.JOB_POLLER_CONCURRENCY", 1)

    # start_poller should call recover_orphaned_jobs and start workers
    tasks, stop_event = await start_poller()

    # Wait for recovery + processing
    for _ in range(30):
        await asyncio.sleep(0.05)
        j = await _get_job(session_factory, stale_job_id)
        if j and j.status == "complete":
            break

    await stop_poller(tasks, stop_event, timeout=2.0)

    refreshed = await _get_job(session_factory, stale_job_id)
    assert refreshed is not None
    assert refreshed.status == "complete", (
        f"Expected 'complete' after recovery+processing, got '{refreshed.status}'"
    )
    fake_code_health.assert_awaited_once()
