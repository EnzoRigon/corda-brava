"""Provider-agnostic queue abstractions for Corda Brava.

``QueueMessage`` is a thin envelope so no vendor-SDK type ever leaks into
services or domain code.  ``EventQueue`` is a ``Protocol`` whose exact shape
mirrors real broker semantics (Azure Service Bus, SQS, etc.) so swapping the
backend later is: add one adapter file + flip one env var — nothing else
changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.domain.entities import PullEvent


@dataclass
class QueueMessage:
    """Provider-agnostic message envelope.

    Fields
    ------
    id              Broker message id.  In-memory uses ``PullEvent.batch_id``.
    payload         The wrapped ``PullEvent``.
    delivery_count  Number of times this message has been delivered.
                    Starts at 1; increments on every redelivery (lease expiry
                    or ``abandon``).
    raw             Opaque broker handle (e.g. the SDK message that carries the
                    lock) which ``ack`` / ``abandon`` need.  ``None`` for the
                    in-memory queue.  Only the queue that produced it may look
                    inside; services and domain code must ignore it.
    """

    id: str
    payload: PullEvent
    delivery_count: int = field(default=1)
    raw: Any = field(default=None, repr=False, compare=False)


class EventQueue(Protocol):
    """Broker-shaped async queue interface.

    All implementations must honour these semantics:

    * ``receive_batch`` **leases** messages — it does NOT delete them.
    * ``ack`` permanently removes a leased message (at-least-once guarantee).
    * Unacked messages become visible again after the lease timeout
      (redelivery), with ``delivery_count`` incremented.
    * ``abandon`` releases a lease early (makes message visible immediately).
    * ``start`` / ``close`` manage the underlying connection lifecycle.

    The identical receive/ack shape ensures the consumer loop works with both
    in-memory and cloud broker implementations without modification.
    """

    async def start(self) -> None:
        """Open the broker connection (no-op for in-memory)."""
        ...

    async def close(self) -> None:
        """Close the broker connection gracefully."""
        ...

    async def enqueue(self, event: PullEvent) -> None:
        """Publish a new ``PullEvent`` to the queue."""
        ...

    async def receive_batch(self, max_messages: int, max_wait_s: float) -> list[QueueMessage]:
        """Lease up to ``max_messages`` messages.

        Blocks up to ``max_wait_s`` seconds waiting for at least one message
        to arrive.  May return fewer than ``max_messages`` or an empty list if
        none arrive within the timeout.  Messages are **leased**, not deleted.
        """
        ...

    async def ack(self, messages: list[QueueMessage]) -> None:
        """Permanently remove (complete) the given messages from the queue."""
        ...

    async def abandon(self, messages: list[QueueMessage]) -> None:
        """Release leases immediately, returning messages to pending.

        The next ``receive_batch`` will see them again.  Delivery count is
        **not** incremented here — that happens on lease-expiry redelivery.
        """
        ...
