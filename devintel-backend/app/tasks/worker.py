"""Base background worker — structured task execution with logging, locking, and error handling.

Provides a consistent pattern for all background tasks with:
- Distributed lock acquisition (prevents duplicate execution)
- Structured logging with task context
- Error handling and retry tracking
- Execution time measurement

Usage::

    class IndexingWorker(BaseWorker):
        task_name = "indexing"

        async def execute(self, repo_id: str, **kwargs):
            # ... indexing logic ...
            return {"indexed_files": 42}

    worker = IndexingWorker()
    result = await worker.run(repo_id="abc-123")
"""

from __future__ import annotations

import time
import traceback
from abc import ABC, abstractmethod
from typing import Any, Optional

from app.core.logging import get_logger, log_context
from app.services.cache import cache

logger = get_logger(__name__)


class TaskResult:
    """Result of a background task execution."""

    def __init__(
        self,
        task_name: str,
        status: str = "success",
        result: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
        duration_ms: float = 0.0,
    ) -> None:
        self.task_name = task_name
        self.status = status  # "success", "error", "skipped", "locked"
        self.result = result or {}
        self.error = error
        self.duration_ms = duration_ms

    @property
    def is_success(self) -> bool:
        return self.status == "success"


class BaseWorker(ABC):
    """Abstract base class for background workers.

    Subclasses must set ``task_name`` and implement ``execute()``.
    """

    task_name: str = "unknown"
    lock_ttl: int = 300  # 5 minutes default lock TTL
    use_lock: bool = True  # Whether to use distributed locking

    async def run(self, **kwargs: Any) -> TaskResult:
        """Execute the task with locking, logging, and error handling.

        Args:
            **kwargs: Task-specific arguments.

        Returns:
            TaskResult with status and result data.
        """
        lock_key = self._lock_key(**kwargs)

        # Set logging context
        log_context.set(agent=f"worker:{self.task_name}")

        # Try to acquire lock
        if self.use_lock:
            acquired = await cache.acquire_lock(lock_key, ttl=self.lock_ttl)
            if not acquired:
                logger.info(
                    "Task %s skipped — already running (lock: %s)",
                    self.task_name, lock_key,
                )
                return TaskResult(
                    task_name=self.task_name,
                    status="locked",
                    error="Another instance is already running",
                )

        start = time.perf_counter()
        try:
            logger.info("Starting task: %s", self.task_name)
            result = await self.execute(**kwargs)
            elapsed = (time.perf_counter() - start) * 1000

            logger.info(
                "Task %s completed in %.0fms",
                self.task_name, elapsed,
            )

            return TaskResult(
                task_name=self.task_name,
                status="success",
                result=result or {},
                duration_ms=elapsed,
            )

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(
                "Task %s failed after %.0fms: %s",
                self.task_name, elapsed, e,
                exc_info=True,
            )
            return TaskResult(
                task_name=self.task_name,
                status="error",
                error=str(e),
                duration_ms=elapsed,
            )

        finally:
            if self.use_lock:
                await cache.release_lock(lock_key)
            log_context.clear()

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Optional[dict[str, Any]]:
        """Execute the task logic. Override in subclasses.

        Args:
            **kwargs: Task-specific arguments.

        Returns:
            Optional dict of result data.
        """
        ...

    def _lock_key(self, **kwargs: Any) -> str:
        """Generate a lock key for this task invocation."""
        # Include task-specific identifiers in the key
        parts = [self.task_name]
        for key in sorted(kwargs.keys()):
            val = kwargs[key]
            if val is not None:
                parts.append(f"{key}={val}")
        return ":".join(parts)
