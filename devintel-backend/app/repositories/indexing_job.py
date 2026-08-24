"""Indexing job repository for durable asynchronous repository indexing tasks."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.indexing_job import IndexingJob
from app.repositories.base import BaseRepository


class IndexingJobRepository(BaseRepository[IndexingJob]):
    """Repository for managing durable indexing jobs."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with IndexingJob model."""
        super().__init__(IndexingJob, db)

    async def enqueue(
        self,
        repository_id: UUID,
        job_type: str,
        payload: Optional[dict[str, Any]] = None,
        max_attempts: int = 3,
    ) -> IndexingJob:
        """Enqueue a new indexing job with status='pending'."""
        if payload is None:
            payload = {}

        return await self.create(
            repository_id=repository_id,
            job_type=job_type,
            status="pending",
            payload=payload,
            attempt_count=0,
            max_attempts=max_attempts,
        )

    async def dequeue_next(self, worker_id: str) -> Optional[IndexingJob]:
        """Atomically claim the oldest pending job using SELECT ... FOR UPDATE SKIP LOCKED.

        Updates the claimed job to status='running', locked_at=now(),
        locked_by=worker_id, and increments attempt_count within the same transaction.
        Returns None if no pending job exists.
        """
        stmt = (
            select(IndexingJob)
            .where(IndexingJob.status == "pending")
            .order_by(IndexingJob.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )

        result = await self.db.execute(stmt)
        job = result.scalar_one_or_none()

        if job is None:
            return None

        now = datetime.now(timezone.utc)
        job.status = "running"
        job.locked_at = now
        job.locked_by = worker_id
        job.attempt_count += 1

        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def mark_complete(self, job_id: UUID) -> Optional[IndexingJob]:
        """Mark an indexing job as complete."""
        job = await self.get_by_id(job_id)
        if not job:
            return None

        now = datetime.now(timezone.utc)
        job.status = "complete"
        job.completed_at = now
        job.locked_at = None
        job.locked_by = None

        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def mark_failed(self, job_id: UUID, error_message: str) -> Optional[IndexingJob]:
        """Mark an indexing job as failed or reset to pending for retry if attempts remain."""
        job = await self.get_by_id(job_id)
        if not job:
            return None

        job.error_message = error_message
        job.locked_at = None
        job.locked_by = None

        if job.attempt_count >= job.max_attempts:
            job.status = "failed"
        else:
            job.status = "pending"

        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def recover_orphaned_jobs(self, stale_after_minutes: int = 30) -> int:
        """Find and recover jobs stuck in 'running' status past the timeout threshold.

        Resets jobs to 'pending' if attempt_count < max_attempts, or marks them
        as 'failed' if attempts are exhausted. Returns the count of recovered jobs.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=stale_after_minutes)

        stmt = (
            select(IndexingJob)
            .where(
                IndexingJob.status == "running",
                IndexingJob.locked_at <= cutoff,
            )
        )

        result = await self.db.execute(stmt)
        stale_jobs = list(result.scalars().all())

        if not stale_jobs:
            return 0

        for job in stale_jobs:
            job.locked_at = None
            job.locked_by = None
            if job.attempt_count >= job.max_attempts:
                job.status = "failed"
                job.error_message = (
                    f"Job orphaned and failed after exceeding max attempts ({job.max_attempts})"
                )
            else:
                job.status = "pending"
                job.error_message = "Job recovered from stale worker"

        await self.db.flush()
        return len(stale_jobs)

    async def get_by_repository(
        self, repository_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[IndexingJob]:
        """Get all indexing jobs for a repository."""
        stmt = (
            select(IndexingJob)
            .where(IndexingJob.repository_id == repository_id)
            .order_by(IndexingJob.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_active_job(self, repository_id: UUID) -> Optional[IndexingJob]:
        """Get the currently active (pending or running) job for a repository."""
        stmt = (
            select(IndexingJob)
            .where(
                IndexingJob.repository_id == repository_id,
                IndexingJob.status.in_(["pending", "running"]),
            )
            .order_by(IndexingJob.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
