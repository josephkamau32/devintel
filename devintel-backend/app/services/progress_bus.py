"""In-process event bus for real-time progress broadcasting.

Replaces Redis pub/sub for single-instance deployments.
Each subscriber gets its own asyncio.Queue, so multiple WebSocket
clients can independently consume events from the same channel.
"""

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class ProgressBus:
    """Simple in-process pub/sub bus using asyncio.Queue per subscriber."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)

    async def publish(self, channel: str, data: Any) -> None:
        """Publish data to all subscribers on a channel."""
        queues = self._subscribers.get(channel, [])
        for q in queues:
            try:
                q.put_nowait(data)
            except asyncio.QueueFull:
                logger.warning(f"Subscriber queue full on {channel}, dropping message")

    async def subscribe(self, channel: str) -> AsyncIterator[Any]:
        """Subscribe to a channel, yielding messages as they arrive.

        Usage::

            async for message in progress_bus.subscribe("indexing:repo-id"):
                await websocket.send_json(message)
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=256)
        self._subscribers[channel].append(queue)
        try:
            while True:
                data = await queue.get()
                yield data
        finally:
            # Cleanup when the subscriber disconnects
            try:
                self._subscribers[channel].remove(queue)
            except ValueError:
                pass
            if not self._subscribers[channel]:
                del self._subscribers[channel]


# Global singleton
progress_bus = ProgressBus()
