"""In-memory broker-shaped EventQueue implementation.

Semantics deliberately mirror Azure Service Bus so the consumer loop is
identical for both backends:

* ``enqueue``       → appends to the internal pending deque.
* ``receive_batch`` → moves messages to the in-flight set with a lease expiry.
                     Returns immediately if pending messages are available,
                     otherwise polls until ``max_wait_s`` elapses.  Expired
                     leases are reclaimed *before* serving new messages.
* ``ack``           → permanently removes a message from the in-flight set.
* ``abandon``       → moves a message back to pending immediately (no
                     delivery_count increment — that happens on expiry).

Injectable clock
----------------
The constructor accepts an optional ``time_fn`` (defaults to
``time.monotonic``) and ``lease_timeout_s`` (defaults to
``settings.QUEUE_LEASE_TIMEOUT_S``).  Tests pass a tiny ``lease_timeout_s``
(e.g. 0.05 s) so redelivery can be exercised without real-time waiting.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

from app.domain.entities import PullEvent
from app.queue.interfaces import QueueMessage

# Sentinel default for time_fn so callers can pass None to get the default.
_SENTINEL = object()


@dataclass
class _LeasedMessage:
    """Internal record for a message currently held by a consumer."""

    message: QueueMessage
    expires_at: float  # monotonic timestamp


class InMemoryEventQueue:
    """Async in-memory queue with broker semantics (lease / ack / redelivery).

    Parameters
    ----------
    lease_timeout_s:
        How long (in seconds) a received message stays leased before it
        becomes visible again.  Defaults to ``settings.QUEUE_LEASE_TIMEOUT_S``.
        Pass a small value in tests to force fast redelivery.
    time_fn:
        Monotonic clock function.  Defaults to ``time.monotonic``.  Override
        in tests to simulate time passing without ``asyncio.sleep``.
    """

    def __init__(
        self,
        *,
        lease_timeout_s: float | None = None,
        time_fn: Callable[[], float] | object = _SENTINEL,
    ) -> None:
        from app.core.settings import get_settings

        self._lease_timeout_s: float = (
            lease_timeout_s
            if lease_timeout_s is not None
            else float(get_settings().QUEUE_LEASE_TIMEOUT_S)
        )
        self._time_fn: Callable[[], float] = (
            time.monotonic if time_fn is _SENTINEL else time_fn  # type: ignore[assignment]
        )

        self._pending: deque[QueueMessage] = deque()
        self._inflight: dict[str, _LeasedMessage] = {}  # keyed by QueueMessage.id
        self._lock = asyncio.Lock()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """No-op for the in-memory backend."""

    async def close(self) -> None:
        """No-op for the in-memory backend."""

    # ── Core operations ───────────────────────────────────────────────────────

    async def enqueue(self, event: PullEvent) -> None:
        """Append a new message to the pending queue."""
        msg = QueueMessage(id=event.batch_id, payload=event, delivery_count=1)
        async with self._lock:
            self._pending.append(msg)

    async def receive_batch(self, max_messages: int, max_wait_s: float) -> list[QueueMessage]:
        """Lease up to ``max_messages`` messages, waiting up to ``max_wait_s``.

        Steps:
        1. Reclaim any expired leases (move them back to pending with
           incremented delivery_count).
        2. If pending messages are available, lease up to ``max_messages`` and
           return immediately.
        3. Otherwise sleep in short increments until a message arrives or
           ``max_wait_s`` elapses.
        """
        deadline = self._time_fn() + max_wait_s
        poll_interval = 0.01  # 10 ms polling granularity

        while True:
            async with self._lock:
                self._reclaim_expired_leases()
                if self._pending:
                    return self._take_messages(max_messages)

            remaining = deadline - self._time_fn()
            if remaining <= 0:
                return []
            await asyncio.sleep(min(poll_interval, remaining))

    async def ack(self, messages: list[QueueMessage]) -> None:
        """Permanently remove the given messages from the in-flight set."""
        async with self._lock:
            for msg in messages:
                self._inflight.pop(msg.id, None)

    async def abandon(self, messages: list[QueueMessage]) -> None:
        """Release leases immediately, returning messages to the pending queue.

        Delivery count is intentionally *not* incremented here — that happens
        only on lease-expiry redelivery.
        """
        async with self._lock:
            for msg in messages:
                leased = self._inflight.pop(msg.id, None)
                if leased is not None:
                    self._pending.appendleft(leased.message)

    # ── Internal helpers (must be called with self._lock held) ────────────────

    def _reclaim_expired_leases(self) -> None:
        """Move expired leased messages back to pending with incremented count."""
        now = self._time_fn()
        expired_ids = [
            msg_id for msg_id, leased in self._inflight.items() if leased.expires_at <= now
        ]
        for msg_id in expired_ids:
            leased = self._inflight.pop(msg_id)
            # Clone with delivery_count incremented so consumers can detect
            # redeliveries.
            original = leased.message
            redelivered = QueueMessage(
                id=original.id,
                payload=original.payload,
                delivery_count=original.delivery_count + 1,
            )
            self._pending.append(redelivered)

    def _take_messages(self, max_messages: int) -> list[QueueMessage]:
        """Move up to ``max_messages`` from pending to in-flight and return them."""
        taken: list[QueueMessage] = []
        expires_at = self._time_fn() + self._lease_timeout_s
        for _ in range(min(max_messages, len(self._pending))):
            msg = self._pending.popleft()
            self._inflight[msg.id] = _LeasedMessage(
                message=msg,
                expires_at=expires_at,
            )
            taken.append(msg)
        return taken
