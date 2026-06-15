"""Retry queue for failed background tasks with exponential backoff."""

import asyncio
import time
from dataclasses import dataclass
from typing import Optional

from app.core.logging import get_logger
from app.core.exceptions import IndexingError

logger = get_logger(__name__)


@dataclass
class RetryTask:
    """Represents a task queued for retry."""
    task_name: str
    args: tuple
    kwargs: dict
    attempt: int
    max_attempts: int
    next_retry_at: float
    created_at: float


class TaskRetryQueue:
    """Manages retry attempts for failed background tasks."""

    def __init__(self, max_retries: int = 3, base_delay: float = 60.0):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._tasks: dict[str, RetryTask] = {}  # task_name -> task
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._running = False
        self._lock = asyncio.Lock()

    async def enqueue(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict = None,
        attempt: int = 0,
    ) -> None:
        """Add a task to the retry queue."""
        if kwargs is None:
            kwargs = {}

        if attempt >= self._max_retries:
            logger.error(f"Max retries exceeded for {task_name}, giving up")
            return

        next_retry = time.time() + self._base_delay * (2 ** attempt)
        task = RetryTask(
            task_name=task_name,
            args=args,
            kwargs=kwargs,
            attempt=attempt,
            max_attempts=self._max_retries,
            next_retry_at=next_retry,
            created_at=time.time(),
        )

        async with self._lock:
            self._tasks[task_name] = task
            await self._queue.put((next_retry, task_name))

        logger.info(f"Queued {task_name} for retry in {self._base_delay * (2 ** attempt):.0f}s")

    async def start(self) -> None:
        """Start the retry worker loop."""
        self._running = True
        while self._running:
            try:
                next_retry, task_name = await self._queue.get()

                if next_retry > time.time():
                    await asyncio.sleep(1)
                    await self._queue.put((next_retry, task_name))
                    continue

                task = self._tasks.get(task_name)
                if not task:
                    continue

                success = await self._execute_task(task)

                if success:
                    async with self._lock:
                        self._tasks.pop(task_name, None)
                else:
                    task.attempt += 1
                    if task.attempt < task.max_attempts:
                        task.next_retry_at = time.time() + self._base_delay * (2 ** task.attempt)
                        await self._queue.put((task.next_retry_at, task_name))
                    else:
                        logger.error(f"Task {task_name} failed after {task.max_attempts} attempts")
                        async with self._lock:
                            self._tasks.pop(task_name, None)

            except Exception as e:
                logger.error(f"Retry queue error: {e}")
                await asyncio.sleep(5)

    async def stop(self) -> None:
        """Stop the retry worker loop."""
        self._running = False

    async def _execute_task(self, task: RetryTask) -> bool:
        """Execute a retry task. Returns True if successful."""
        from app.tasks.indexing import index_repository_task

        task_handlers = {
            "index_repository": index_repository_task,
        }

        handler = task_handlers.get(task.task_name)
        if not handler:
            logger.error(f"No handler for task: {task.task_name}")
            return False

        try:
            await handler(*task.args, **task.kwargs)
            logger.info(f"Task {task.task_name} succeeded on retry")
            return True
        except Exception as e:
            logger.error(f"Task {task.task_name} failed on retry: {e}")
            return False


# Global retry queue instance
retry_queue = TaskRetryQueue()