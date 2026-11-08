"""AzureServiceBusEventQueue against a fake broker: contract, lease/redelivery, DLQ, batching.

The fake (``fake_servicebus.py``) mimics the SDK behaviours measured on a real namespace, so
these tests also fail if the adapter ever drives a sender/receiver concurrently.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator

import pytest
from azure.servicebus.exceptions import ServiceBusError

from app.domain.entities import PullEvent
from app.domain.enums import Team
from app.queue.azure_service_bus import MAX_PARALLEL_SETTLES, AzureServiceBusEventQueue
from tests.queue.fake_servicebus import FakeBroker


def _event(batch_id: str = "b1", match_id: str = "m1", team: Team = Team.INTER) -> PullEvent:
    return PullEvent(
        id=f"evt-{batch_id}",
        match_id=match_id,
        player_id="p1",
        team=team,
        count=3,
        client_ts=time.time(),
        batch_id=batch_id,
    )


def _make(broker: FakeBroker) -> AzureServiceBusEventQueue:
    return AzureServiceBusEventQueue(
        "conn",
        "pulls",
        lock_duration_s=broker.lock_duration_s,
        client_factory=broker.client,
        time_fn=broker.clock,
    )


@pytest.fixture()
def broker() -> FakeBroker:
    return FakeBroker()


@pytest.fixture()
async def queue(broker: FakeBroker) -> AsyncIterator[AzureServiceBusEventQueue]:
    q = _make(broker)
    await q.start()
    yield q
    await q.close()


# ── lifecycle ─────────────────────────────────────────────────────────────────


async def test_start_opens_the_links_and_close_releases_them(broker: FakeBroker) -> None:
    q = _make(broker)
    await q.start()
    assert (broker.clients_opened, broker.open_links) == (1, 2)  # sender + receiver
    await q.start()  # idempotent
    assert broker.clients_opened == 1
    await q.close()
    assert (broker.clients_closed, broker.open_links) == (1, 0)
    await q.close()  # idempotent


async def test_start_failure_names_the_queue_and_leaves_nothing_open(broker: FakeBroker) -> None:
    broker.fail_open = ServiceBusError("The messaging entity could not be found.")
    q = _make(broker)
    with pytest.raises(RuntimeError, match="Cannot open Azure Service Bus queue 'pulls'"):
        await q.start()
    assert broker.clients_closed == broker.clients_opened
    with pytest.raises(RuntimeError, match="not started"):
        await q.enqueue(_event())


async def test_using_the_queue_before_start_or_after_close_is_a_clear_error(
    broker: FakeBroker,
) -> None:
    q = _make(broker)
    for call in (
        lambda: q.enqueue(_event()),
        lambda: q.receive_batch(10, 0),
        lambda: q.ack([]),
        lambda: q.abandon([]),
    ):
        with pytest.raises(RuntimeError, match="not started"):
            await call()
    await q.start()
    await q.close()
    with pytest.raises(RuntimeError, match="not started"):
        await q.enqueue(_event())


# ── enqueue / receive / ack ───────────────────────────────────────────────────


async def test_enqueue_sets_scoped_message_id_and_properties(
    queue: AzureServiceBusEventQueue, broker: FakeBroker
) -> None:
    await queue.enqueue(_event(team=Team.GREMIO))
    (sent,) = broker.sent_messages
    assert sent.message_id == "m1:b1"  # match-scoped, like the pull route's dedup key
    assert sent.content_type == "application/json"
    assert sent.subject == "pull"
    assert sent.application_properties == {"match_id": "m1", "team": "gremio"}


async def test_receive_wraps_the_broker_message_in_the_envelope(
    queue: AzureServiceBusEventQueue,
) -> None:
    event = _event()
    await queue.enqueue(event)
    (msg,) = await queue.receive_batch(max_messages=10, max_wait_s=0)
    assert msg.payload == event
    assert msg.id == "m1:b1"
    assert msg.delivery_count == 1  # the broker counts from 0, the contract from 1
    assert msg.raw is not None


async def test_receive_respects_max_messages(queue: AzureServiceBusEventQueue) -> None:
    for i in range(5):
        await queue.enqueue(_event(batch_id=f"b{i}"))
    assert len(await queue.receive_batch(3, 0)) == 3
    assert len(await queue.receive_batch(3, 0)) == 2


async def test_receive_never_asks_the_sdk_for_a_zero_wait(
    queue: AzureServiceBusEventQueue, broker: FakeBroker
) -> None:
    assert await queue.receive_batch(0, 1.0) == []  # nothing to ask for: no broker call
    assert broker.receive_waits == []
    await queue.receive_batch(10, 0)  # the consumer polls with 0
    await queue.receive_batch(10, 2.5)
    assert broker.receive_waits[0] > 0
    assert broker.receive_waits[1] == 2.5


async def test_concurrent_receives_share_one_broker_call(
    queue: AzureServiceBusEventQueue, broker: FakeBroker
) -> None:
    for i in range(10):
        await queue.enqueue(_event(f"b{i}"))
    # five match loops polling at once: one broker receive, never two overlapping (the fake
    # receiver fails on overlap, like the SDK), and no loop queues behind the others' receives
    batches = await asyncio.gather(*(queue.receive_batch(4, 0) for _ in range(5)))
    assert len(broker.receive_waits) == 1
    rest = await queue.receive_batch(10, 0)
    ids = [m.payload.batch_id for m in [*(m for b in batches for m in b), *rest]]
    assert sorted(ids) == sorted(f"b{i}" for i in range(10))  # nothing lost or duplicated


async def test_a_cancelled_caller_does_not_lose_the_shared_receive(
    queue: AzureServiceBusEventQueue,
) -> None:
    await queue.enqueue(_event())
    first = asyncio.create_task(queue.receive_batch(10, 0))
    await asyncio.sleep(0)  # the receive is in flight
    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first
    (msg,) = await queue.receive_batch(10, 0)  # it landed in the pool, still locked
    assert (msg.payload.batch_id, msg.delivery_count) == ("b1", 1)


async def test_ack_completes_and_the_message_never_returns(
    queue: AzureServiceBusEventQueue, broker: FakeBroker
) -> None:
    await queue.enqueue(_event())
    msgs = await queue.receive_batch(10, 0)
    await queue.ack(msgs)
    assert broker.depth == 0
    broker.advance(broker.lock_duration_s * 2)
    assert await queue.receive_batch(10, 0) == []


async def test_a_leased_message_is_invisible_until_its_lock_expires(
    queue: AzureServiceBusEventQueue, broker: FakeBroker
) -> None:
    await queue.enqueue(_event())
    await queue.receive_batch(10, 0)
    assert await queue.receive_batch(10, 0) == []
    broker.advance(broker.lock_duration_s + 1)
    (again,) = await queue.receive_batch(10, 0)
    assert again.payload.batch_id == "b1"
    assert again.delivery_count == 2


async def test_abandon_makes_the_message_visible_at_once_without_counting_a_delivery(
    queue: AzureServiceBusEventQueue, broker: FakeBroker
) -> None:
    await queue.enqueue(_event())
    first = await queue.receive_batch(10, 0)
    await queue.abandon(first)
    (again,) = await queue.receive_batch(10, 0)
    assert again.payload.batch_id == "b1"
    assert again.delivery_count == 1  # as the contract says (and the in-memory queue does)
    assert broker.abandons == 0  # Service Bus would count abandon_message as a delivery
    await queue.ack([again])
    assert broker.depth == 0  # the original lock still settles it


async def test_messages_abandoned_by_other_loops_are_never_dead_lettered(
    queue: AzureServiceBusEventQueue, broker: FakeBroker
) -> None:
    # three matches share the queue; loops A and C keep handing back B's pull
    await queue.enqueue(_event("theirs", match_id="B"))
    for _ in range(30):  # far more than the queue's MaxDeliveryCount of 10
        msgs = await queue.receive_batch(500, 0)
        assert [m.payload.batch_id for m in msgs] == ["theirs"]  # there on every poll
        await queue.abandon(msgs)  # "not my match"
    (mine,) = await queue.receive_batch(500, 0)
    assert (mine.payload.batch_id, mine.delivery_count) == ("theirs", 1)
    assert broker.dead_letters == [] and broker.abandons == 0


async def test_a_pooled_message_about_to_lose_its_lock_is_left_to_the_broker(
    queue: AzureServiceBusEventQueue, broker: FakeBroker
) -> None:
    await queue.enqueue(_event())
    await queue.abandon(await queue.receive_batch(10, 0))
    broker.advance(broker.lock_duration_s - 1)  # inside the safety margin, not yet expired
    assert await queue.receive_batch(10, 0) == []  # not handed out with a dying lock
    broker.advance(2)  # the lock expires: the broker redelivers it
    (again,) = await queue.receive_batch(10, 0)
    assert (again.payload.batch_id, again.delivery_count) == ("b1", 2)


async def test_abandon_twice_does_not_duplicate(queue: AzureServiceBusEventQueue) -> None:
    await queue.enqueue(_event())
    msgs = await queue.receive_batch(10, 0)
    await queue.abandon(msgs)
    await queue.abandon(msgs)
    assert len(await queue.receive_batch(10, 0)) == 1


async def test_close_drops_the_pool(broker: FakeBroker) -> None:
    q = _make(broker)
    await q.start()
    await q.enqueue(_event())
    await q.abandon(await q.receive_batch(10, 0))
    await q.close()
    await q.start()
    assert await q.receive_batch(10, 0) == []  # still locked by the closed receiver
    broker.advance(broker.lock_duration_s + 1)
    (again,) = await q.receive_batch(10, 0)
    assert again.delivery_count == 2
    await q.close()


async def test_ack_after_the_lock_expired_is_logged_not_raised(
    queue: AzureServiceBusEventQueue, broker: FakeBroker, caplog: pytest.LogCaptureFixture
) -> None:
    await queue.enqueue(_event())
    first = await queue.receive_batch(10, 0)
    broker.advance(broker.lock_duration_s + 1)
    with caplog.at_level(logging.WARNING, logger="app.queue.azure_service_bus"):
        await queue.ack(first)  # must not raise: the consumer's tick would otherwise abort
    assert "complete failed for 1 of 1 message(s) [m1:b1]" in caplog.text
    (again,) = await queue.receive_batch(10, 0)  # redelivered; the consumer dedups by batchId
    assert again.delivery_count == 2


async def test_one_lost_lock_does_not_stop_the_rest_of_the_acks(
    queue: AzureServiceBusEventQueue, broker: FakeBroker
) -> None:
    await queue.enqueue(_event("old"))
    stale = await queue.receive_batch(10, 0)
    broker.advance(broker.lock_duration_s + 1)  # the lock behind "stale" ran out
    await queue.enqueue(_event("new"))
    fresh = [m for m in await queue.receive_batch(10, 0) if m.payload.batch_id == "new"]
    await queue.ack([*stale, *fresh])  # completing the stale one fails, "new" must still complete
    (left,) = broker.locked  # only the redelivered copy of "old" remains, still leased
    assert left.message_id == "m1:old"


async def test_any_settle_error_is_logged_and_the_rest_still_settle(
    queue: AzureServiceBusEventQueue,
    broker: FakeBroker,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    for i in range(3):
        await queue.enqueue(_event(f"b{i}"))
    msgs = await queue.receive_batch(10, 0)
    receiver = queue._receiver
    real_complete = receiver.complete_message

    async def complete(message) -> None:
        if message.message_id == "m1:b0":
            raise ValueError("The handler has already been shutdown.")  # not a ServiceBusError
        await real_complete(message)

    monkeypatch.setattr(receiver, "complete_message", complete)
    with caplog.at_level(logging.WARNING, logger="app.queue.azure_service_bus"):
        await queue.ack(msgs)  # must not raise
    assert "complete failed for 1 of 3 message(s) [m1:b0]" in caplog.text
    (left,) = broker.locked
    assert left.message_id == "m1:b0"


async def test_settles_never_overlap_a_receive(
    queue: AzureServiceBusEventQueue, broker: FakeBroker
) -> None:
    for i in range(20):
        await queue.enqueue(_event(f"b{i}"))
    first = await queue.receive_batch(10, 0)
    for i in range(20, 30):
        await queue.enqueue(_event(f"b{i}"))
    # one loop acks while another polls: the settles wait for the receive, or vice versa
    _, second = await asyncio.gather(queue.ack(first), queue.receive_batch(10, 0))
    await queue.ack(second)
    assert broker.settles_during_receive == 0
    assert broker.depth == 10


async def test_settles_run_in_parallel_but_bounded(
    queue: AzureServiceBusEventQueue, broker: FakeBroker
) -> None:
    await asyncio.gather(*(queue.enqueue(_event(f"b{i}")) for i in range(300)))
    msgs = await queue.receive_batch(500, 0)
    assert len(msgs) == 300
    await queue.ack(msgs)
    assert broker.depth == 0
    assert 1 < broker.max_concurrent_settles <= MAX_PARALLEL_SETTLES


# ── poison messages ───────────────────────────────────────────────────────────


async def test_unparseable_messages_are_dead_lettered_and_skipped(
    queue: AzureServiceBusEventQueue, broker: FakeBroker
) -> None:
    broker.publish_raw("this is not json", message_id="junk-1")
    broker.publish_raw('{"match_id": "m1"}', message_id="junk-2")  # JSON, wrong shape
    await queue.enqueue(_event())
    msgs = await queue.receive_batch(10, 0)
    assert [m.payload.batch_id for m in msgs] == ["b1"]
    assert {d.message_id: d.dead_letter_reason for d in broker.dead_letters} == {
        "junk-1": "invalid-payload",
        "junk-2": "invalid-payload",
    }
    assert all(d.dead_letter_error_description for d in broker.dead_letters)
    assert broker.depth == 1  # only the good message is still leased


# ── send side: group commit ───────────────────────────────────────────────────


async def test_concurrent_enqueues_are_grouped_and_never_overlap_on_the_sender(
    queue: AzureServiceBusEventQueue, broker: FakeBroker
) -> None:
    events = [_event(f"b{i}") for i in range(50)]
    # the fake sender fails on overlap, so a second concurrent send would raise here
    await asyncio.gather(*(queue.enqueue(e) for e in events))
    assert sum(broker.sent_batches) == 50
    assert max(broker.sent_batches) > 1
    got = await queue.receive_batch(100, 0)
    assert {m.payload.batch_id for m in got} == {e.batch_id for e in events}


async def test_a_full_batch_is_split_across_sends(broker: FakeBroker) -> None:
    broker.batch_capacity = 10
    q = _make(broker)
    await q.start()
    await asyncio.gather(*(q.enqueue(_event(f"b{i}")) for i in range(25)))
    assert broker.sent_batches == [10, 10, 5]
    await q.close()


async def test_a_failed_send_raises_for_every_caller_in_the_batch_and_the_pump_survives(
    queue: AzureServiceBusEventQueue, broker: FakeBroker
) -> None:
    broker.fail_next_send = ServiceBusError("broker unreachable")
    results = await asyncio.gather(
        *(queue.enqueue(_event(f"b{i}")) for i in range(3)), return_exceptions=True
    )
    assert all(isinstance(r, ServiceBusError) for r in results)
    assert broker.depth == 0
    await queue.enqueue(_event("after"))  # the pump is still alive
    assert broker.depth == 1
