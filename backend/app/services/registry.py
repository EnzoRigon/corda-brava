"""Per-match registry: running consumer tasks + broadcast callback sets."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

Broadcast = Callable[[dict[str, Any]], Awaitable[None]]


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
                self._listeners[match_id].discard(cb)

    def is_running(self, match_id: str) -> bool:
        task = self._tasks.get(match_id)
        return task is not None and not task.done()

    def start_loop(self, match_id: str, coro: Awaitable[None]) -> None:
        self._tasks[match_id] = asyncio.ensure_future(coro)

    async def stop_loop(self, match_id: str) -> None:
        task = self._tasks.pop(match_id, None)
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
