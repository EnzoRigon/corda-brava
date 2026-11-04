"""Per-match registry: running consumer tasks + broadcast callback sets."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

Broadcast = Callable[[dict[str, Any]], Awaitable[None]]

log = logging.getLogger(__name__)


class MatchRegistry:
    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._listeners: dict[str, set[Broadcast]] = {}

    def add_listener(self, match_id: str, cb: Broadcast) -> None:
        self._listeners.setdefault(match_id, set()).add(cb)

    def remove_listener(self, match_id: str, cb: Broadcast) -> None:
        self._listeners.get(match_id, set()).discard(cb)

    async def broadcast(self, match_id: str, payload: dict[str, Any]) -> None:
        """Send to every listener; a failing listener is dropped, never breaks the loop."""
        for cb in list(self._listeners.get(match_id, ())):
            try:
                await cb(payload)
            except Exception:  # noqa: BLE001 - dead socket etc.
                self._listeners.get(match_id, set()).discard(cb)

    def is_running(self, match_id: str) -> bool:
        task = self._tasks.get(match_id)
        return task is not None and not task.done()

    def clear(self, match_id: str) -> None:
        """Drop all listeners for a finished/cancelled match."""
        self._listeners.pop(match_id, None)

    def start_loop(self, match_id: str, coro: Awaitable[None]) -> None:
        task = asyncio.ensure_future(coro)
        self._tasks[match_id] = task

        def _done(t: asyncio.Task[None]) -> None:
            if self._tasks.get(match_id) is t:
                del self._tasks[match_id]
                self.clear(match_id)
            if not t.cancelled() and t.exception() is not None:
                log.error("consumer loop for %s crashed", match_id, exc_info=t.exception())

        task.add_done_callback(_done)

    async def stop_all(self) -> None:
        for match_id in list(self._tasks):
            await self.stop_loop(match_id)

    async def stop_loop(self, match_id: str) -> None:
        task = self._tasks.pop(match_id, None)
        if task is not None and not task.done():
            task.cancel()
            await asyncio.wait([task])  # unlike awaiting, never masks our own cancellation
        self.clear(match_id)
