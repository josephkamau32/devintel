"""Background job poller for durable indexing job processing.

Replaces fire-and-forget asyncio.create_task() with a reliable poll loop
that dequeues jobs from the ``indexing_jobs`` table and dispatches them to
the appropriate handler.  Each handler now re-raises on failure, so
dispatch() treats "no exception" as success and "exception" as failure.
"""

import asyncio
import os
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.indexing_job import IndexingJob
from app.repositories.indexing_job import IndexingJobRepository

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Dispatch: route a job to its handler
# ---------------------------------------------------------------------------

# Expected payload keys for each job type (used for defensive filtering).
_EXPECTED_KEYS: dict[str, set[str]] = {
    "full": {"repo_id", "clone_url", "access_token"},
    "incremental": {
        "repo_id", "clone_url", "access_token",
        "changed_files", "added_files", "removed_files", "head_commit_sha",
    },
    "code_health": {"repo_id"},
    "pr_review": {"repo_id", "pr_number", "pr_title", "access_token"},
}


async def dispatch(job: IndexingJob) -> None:
    """Route *job* to its handler based on ``job.job_type``.

    The handler is awaited directly.  If it raises, the exception
    propagates to ``run_worker_loop`` which marks the job as failed.
    """
    payload: dict[str, Any] = dict(job.payload or {})
    job_type = job.job_type

    # Defensively filter payload to expected keys only.
    expected = _EXPECTED_KEYS.get(job_type)
    if expected is not None:
        payload = {k: v for k, v in payload.items() if k in expected}

    if job_type == "full":
        from app.tasks.indexing import index_repository_task
        await index_repository_task(**payload)

    elif job_type == "incremental":
        from app.services.incremental_indexer import process_push_event
        await process_push_event(**payload)

    elif job_type == "code_health":
        from app.tasks.code_health import compute_code_health_task
        await compute_code_health_task(**payload)

    elif job_type == "pr_review":
        from app.tasks.pr_review import review_pull_request_task
        await review_pull_request_task(**payload)

    else:
        raise ValueError(f"Unknown job_type: {job_type!r}")


# ---------------------------------------------------------------------------
# Worker loop
# ---------------------------------------------------------------------------

async def run_worker_loop(
    worker_id: str,
    stop_event: asyncio.Event,
) -> None:
    """Continuously dequeue and process jobs until *stop_event* is set."""
    poll_interval = settings.JOB_POLL_INTERVAL_SECONDS
    logger.info("Worker %s started (poll_interval=%.1fs)", worker_id, poll_interval)

    while not stop_event.is_set():
        job: IndexingJob | None = None
        try:
            # --- Dequeue -------------------------------------------------
            async with AsyncSessionLocal() as session:
                repo = IndexingJobRepository(session)
                job = await repo.dequeue_next(worker_id)
                await session.commit()  # persist running status + release lock

            if job is None:
                # Nothing to do — sleep then retry.
                try:
                    await asyncio.wait_for(
                        stop_event.wait(), timeout=poll_interval,
                    )
                except asyncio.TimeoutError:
                    pass  # normal: just means poll_interval elapsed
                continue

            # --- Dispatch ------------------------------------------------
            logger.info(
                "Worker %s processing job %s (type=%s, attempt=%d/%d)",
                worker_id, job.id, job.job_type,
                job.attempt_count, job.max_attempts,
            )
            await dispatch(job)

            # --- Mark complete -------------------------------------------
            async with AsyncSessionLocal() as session:
                repo = IndexingJobRepository(session)
                await repo.mark_complete(job.id)
                await session.commit()
            logger.info("Worker %s completed job %s", worker_id, job.id)

        except Exception as exc:
            # Job dispatch (or dequeue) failed.
            if job is not None:
                logger.error(
                    "Worker %s job %s failed: %s",
                    worker_id, job.id, exc,
                    exc_info=True,
                )
                try:
                    async with AsyncSessionLocal() as session:
                        repo = IndexingJobRepository(session)
                        await repo.mark_failed(job.id, str(exc))
                        await session.commit()
                except Exception as mark_err:
                    logger.error(
                        "Worker %s failed to mark job %s as failed: %s",
                        worker_id, job.id, mark_err,
                    )
            else:
                # Error during dequeue itself — log and keep going.
                logger.error(
                    "Worker %s dequeue error: %s", worker_id, exc,
                    exc_info=True,
                )
                try:
                    await asyncio.wait_for(
                        stop_event.wait(), timeout=poll_interval,
                    )
                except asyncio.TimeoutError:
                    pass

    logger.info("Worker %s stopped.", worker_id)


# ---------------------------------------------------------------------------
# Start / stop helpers
# ---------------------------------------------------------------------------

async def start_poller() -> tuple[list[asyncio.Task], asyncio.Event]:
    """Bootstrap the poller: recover orphaned jobs, then spawn workers.

    Returns ``(tasks, stop_event)`` so the caller can pass them to
    :func:`stop_poller` at shutdown.
    """
    # Recover any jobs left in 'running' from a prior crash.
    try:
        async with AsyncSessionLocal() as session:
            repo = IndexingJobRepository(session)
            recovered = await repo.recover_orphaned_jobs()
            await session.commit()
        logger.info("Job poller: recovered %d orphaned job(s).", recovered)
    except Exception as exc:
        logger.error("Job poller: orphan recovery failed: %s", exc, exc_info=True)

    stop_event = asyncio.Event()
    concurrency = settings.JOB_POLLER_CONCURRENCY
    pid = os.getpid()
    tasks: list[asyncio.Task] = []

    for i in range(concurrency):
        wid = f"worker-{pid}-{i}"
        task = asyncio.create_task(
            run_worker_loop(wid, stop_event),
            name=f"job-poller-{wid}",
        )
        tasks.append(task)

    logger.info(
        "Job poller started: %d worker(s), poll_interval=%.1fs.",
        concurrency, settings.JOB_POLL_INTERVAL_SECONDS,
    )
    return tasks, stop_event


async def stop_poller(
    tasks: list[asyncio.Task],
    stop_event: asyncio.Event,
    timeout: float = 10.0,
) -> None:
    """Signal all workers to stop and wait for them to finish.

    In-flight jobs get up to *timeout* seconds to complete before their
    tasks are cancelled.
    """
    logger.info("Job poller: stopping %d worker(s)…", len(tasks))
    stop_event.set()

    if tasks:
        done, pending = await asyncio.wait(tasks, timeout=timeout)
        for task in pending:
            logger.warning("Job poller: cancelling worker %s (timed out).", task.get_name())
            task.cancel()
        # Suppress CancelledError from cancelled tasks.
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

    logger.info("Job poller stopped.")
