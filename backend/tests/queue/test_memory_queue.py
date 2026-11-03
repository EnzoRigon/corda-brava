"""Tests for InMemoryEventQueue — broker semantics: lease / ack / redelivery.

All tests are async (pytest-asyncio, asyncio_mode=auto).

Coverage:
* start() is a no-op
* enqueue → receive_batch returns a leased QueueMessage with the correct payload
* ack removes the message (not redelivered on next receive_batch)
* REDELIVERY: a message not acked before lease expiry is redelivered with
  delivery_count >= 2
* abandon returns a message to pending immediately (next receive_batch picks it up)
* receive_batch returns empty within max_wait_s when queue is empty
* factory: make_event_queue(memory settings) → InMemoryEventQueue instance
* factory: make_event_queue(azure_service_bus settings) → NotImplementedError
  mentioning AzureServiceBusEventQueue
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime

import pytest

from app.core.settings import Settings
from app.domain.entities import PullEvent
from app.domain.enums import Team
from app.queue.factory import make_event_queue
from app.queue.interfaces import QueueMessage
from app.queue.memory import InMemoryEventQueue

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_event(
    batch_id: str = "batch-001",
    match_id: str = "match-abc",
    player_id: str = "player-1",
    team: Team = Team.INTER,
    count: int = 5,
) -> PullEvent:
    """Create a minimal PullEvent for testing."""
    return PullEvent(
        id=f"evt-{batch_id}",
        match_id=match_id,
        player_id=player_id,
        team=team,
        count=count,
        client_ts=time.time(),
        server_ts=datetime.now(tz=UTC),
        batch_id=batch_id,
    )


# ── start() / close() ─────────────────────────────────────────────────────────


async def test_start_is_noop() -> None:
    """start() and close() complete without raising."""
    q = InMemoryEventQueue()
    await q.start()
    await q.close()


# ── enqueue → receive_batch ───────────────────────────────────────────────────


async def test_enqueue_then_receive_returns_message() -> None:
    """enqueue then receive_batch returns exactly one leased QueueMessage."""
    q = InMemoryEventQueue()
    event = _make_event()
    await q.enqueue(event)

    msgs = await q.receive_batch(max_messages=10, max_wait_s=1.0)

    assert len(msgs) == 1
    msg = msgs[0]
    assert isinstance(msg, QueueMessage)
    assert msg.payload == event
    assert msg.id == event.batch_id
    assert msg.delivery_count == 1


async def test_received_message_is_leased_not_deleted() -> None:
    """A received but unacked message is still in the in-flight set, not pending."""
    q = InMemoryEventQueue()
    await q.enqueue(_make_event())

    msgs = await q.receive_batch(max_messages=10, max_wait_s=1.0)
    assert len(msgs) == 1

    # A second receive_batch should return empty because the message is leased
    # (lease has not expired yet — lease_timeout_s defaults to 10 s).
    second = await q.receive_batch(max_messages=10, max_wait_s=0.05)
    assert second == [], "Leased message must not be returned again before ack/expiry"


# ── ack ───────────────────────────────────────────────────────────────────────


async def test_ack_removes_message_permanently() -> None:
    """After ack, the message must not be redelivered on any subsequent receive."""
    q = InMemoryEventQueue()
    await q.enqueue(_make_event())

    msgs = await q.receive_batch(max_messages=10, max_wait_s=1.0)
    assert msgs
    await q.ack(msgs)

    # Must be empty even with a fresh receive.
    second = await q.receive_batch(max_messages=10, max_wait_s=0.05)
    assert second == [], "Acked message must never be redelivered"


# ── REDELIVERY ────────────────────────────────────────────────────────────────


async def test_redelivery_after_lease_expiry() -> None:
    """At-least-once: an unacked message is redelivered after lease expires.

    We use a tiny lease_timeout_s (0.05 s) so the test finishes fast.
    delivery_count must be >= 2 on the redelivered copy.
    """
    LEASE_S = 0.05  # tiny so we don't wait 10 seconds

    q = InMemoryEventQueue(lease_timeout_s=LEASE_S)
    event = _make_event()
    await q.enqueue(event)

    # First receive — leases the message.
    first = await q.receive_batch(max_messages=10, max_wait_s=1.0)
    assert len(first) == 1
    assert first[0].delivery_count == 1

    # Do NOT ack — wait past the lease.
    await asyncio.sleep(LEASE_S + 0.05)

    # Second receive — lease has expired, message must be redelivered.
    second = await q.receive_batch(max_messages=10, max_wait_s=1.0)
    assert len(second) == 1, "Message must be redelivered after lease expiry"
    assert second[0].id == event.batch_id, "Same message id"
    assert (
        second[0].delivery_count >= 2
    ), f"delivery_count must be >= 2 on redelivery, got {second[0].delivery_count}"


# ── abandon ───────────────────────────────────────────────────────────────────


async def test_abandon_returns_message_to_pending_immediately() -> None:
    """abandon() makes the message visible on the very next receive_batch."""
    q = InMemoryEventQueue(lease_timeout_s=30.0)  # long lease so expiry doesn't interfere
    await q.enqueue(_make_event())

    msgs = await q.receive_batch(max_messages=10, max_wait_s=1.0)
    assert msgs

    # Abandon immediately — no sleep needed.
    await q.abandon(msgs)

    # Must be visible again right away.
    second = await q.receive_batch(max_messages=10, max_wait_s=0.5)
    assert len(second) == 1, "Abandoned message must be immediately visible"
    assert second[0].id == msgs[0].id


# ── empty queue / wait ────────────────────────────────────────────────────────


async def test_receive_batch_waits_and_returns_empty_when_queue_empty() -> None:
    """receive_batch returns [] within max_wait_s if no messages are enqueued."""
    q = InMemoryEventQueue()
    max_wait = 0.1  # 100 ms — fast enough for tests

    start = time.monotonic()
    result = await q.receive_batch(max_messages=10, max_wait_s=max_wait)
    elapsed = time.monotonic() - start

    assert result == [], "Expected empty list when no messages"
    # Allow some slack: elapsed should be >= 80% of max_wait but not crazy long.
    assert elapsed >= max_wait * 0.8, f"Expected to wait ~{max_wait}s, only waited {elapsed:.3f}s"


async def test_receive_batch_returns_quickly_when_message_available() -> None:
    """receive_batch should return without waiting full max_wait_s if message exists."""
    q = InMemoryEventQueue()
    await q.enqueue(_make_event())

    start = time.monotonic()
    msgs = await q.receive_batch(max_messages=10, max_wait_s=5.0)
    elapsed = time.monotonic() - start

    assert len(msgs) == 1
    assert elapsed < 1.0, f"Should return quickly, took {elapsed:.3f}s"


# ── multiple messages ─────────────────────────────────────────────────────────


async def test_receive_batch_respects_max_messages() -> None:
    """receive_batch returns at most max_messages items."""
    q = InMemoryEventQueue()
    for i in range(5):
        await q.enqueue(_make_event(batch_id=f"batch-{i:03d}"))

    msgs = await q.receive_batch(max_messages=3, max_wait_s=1.0)
    assert len(msgs) == 3


# ── factory ───────────────────────────────────────────────────────────────────


def test_factory_memory_returns_inmemory_instance() -> None:
    """make_event_queue with QUEUE_BACKEND=memory returns InMemoryEventQueue."""
    settings = Settings(QUEUE_BACKEND="memory")
    queue = make_event_queue(settings)
    assert isinstance(queue, InMemoryEventQueue)


def test_factory_azure_raises_not_implemented() -> None:
    """make_event_queue with azure_service_bus raises NotImplementedError."""
    settings = Settings(QUEUE_BACKEND="azure_service_bus")
    with pytest.raises(NotImplementedError) as exc_info:
        make_event_queue(settings)
    assert "AzureServiceBusEventQueue" in str(
        exc_info.value
    ), "Error message must mention AzureServiceBusEventQueue"
