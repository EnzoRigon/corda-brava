"""End-to-end checks of the adapter against a real Azure Service Bus namespace (opt-in).

    cd backend
    AZURE_TESTS=1 python -m pytest tests/queue/test_azure_service_bus_integration.py -v

The connection string comes from the environment or ``.env``
(AZURE_SERVICEBUS_CONNECTION_STRING, namespace-level, with Manage rights).  Each test creates
its own short-lived queue (``cb-test-<random>``, 5 s lock) and deletes it afterwards, so the
app's real queue is never touched.
"""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from collections.abc import AsyncIterator
from datetime import timedelta

import pytest
from azure.servicebus import ServiceBusMessage, ServiceBusSubQueue
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus.management import ServiceBusAdministrationClient

from app.core.settings import settings_with_root_env
from app.domain.entities import PullEvent
from app.domain.enums import Team
from app.queue.azure_service_bus import AzureServiceBusEventQueue
from app.queue.interfaces import QueueMessage

# Read at import time: the suite's autouse fixture hides ``.env`` from tests, not from collection.
CONN = settings_with_root_env().AZURE_SERVICEBUS_CONNECTION_STRING

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        os.environ.get("AZURE_TESTS") != "1" or not CONN,
        reason="opt-in: set AZURE_TESTS=1 and AZURE_SERVICEBUS_CONNECTION_STRING",
    ),
]


def _event(batch_id: str, match_id: str = "m1") -> PullEvent:
    return PullEvent(
        id=str(uuid.uuid4()),
        match_id=match_id,
        player_id="p1",
        team=Team.GREMIO,
        count=2,
        client_ts=time.time(),
        batch_id=batch_id,
    )


async def _receive(queue: AzureServiceBusEventQueue, want: int, timeout_s: float = 20) -> list:
    """Poll like the consumer does (wait 0) until ``want`` messages arrived or time ran out."""
    got: list[QueueMessage] = []
    deadline = time.monotonic() + timeout_s
    while len(got) < want and time.monotonic() < deadline:
        got += await queue.receive_batch(500, 0)
    return got


@pytest.fixture()
async def azure_queue() -> AsyncIterator[tuple[AzureServiceBusEventQueue, str]]:
    name = f"cb-test-{uuid.uuid4().hex[:8]}"
    admin = ServiceBusAdministrationClient.from_connection_string(CONN)
    await asyncio.to_thread(
        admin.create_queue,
        name,
        lock_duration=timedelta(seconds=5),  # the minimum: keeps the redelivery test short
        max_delivery_count=5,
        requires_duplicate_detection=True,
        duplicate_detection_history_time_window=timedelta(minutes=5),
        default_message_time_to_live=timedelta(minutes=10),
    )
    queue = AzureServiceBusEventQueue(CONN, name, lock_duration_s=5)
    await queue.start()
    try:
        yield queue, name
    finally:
        await queue.close()
        await asyncio.to_thread(admin.delete_queue, name)
        admin.close()


async def test_concurrent_enqueues_arrive_once_each_and_ack_drains_the_queue(azure_queue) -> None:
    queue, _ = azure_queue
    events = [_event(f"b{i}") for i in range(60)]
    await asyncio.gather(*(queue.enqueue(e) for e in events))  # real SDK, real concurrency
    got = await _receive(queue, 60)
    assert sorted(m.payload.batch_id for m in got) == sorted(e.batch_id for e in events)
    assert {m.delivery_count for m in got} == {1}
    await queue.ack(got)
    await asyncio.sleep(6)  # past the lock: an acked message must not return
    assert await queue.receive_batch(500, 0) == []


async def test_an_unacked_message_is_redelivered_after_the_lock_expires(azure_queue) -> None:
    queue, _ = azure_queue
    await queue.enqueue(_event("lease"))
    (first,) = await _receive(queue, 1)
    assert first.delivery_count == 1
    (again,) = await _receive(queue, 1, timeout_s=20)  # the 5 s lock runs out meanwhile
    assert again.payload.batch_id == "lease"
    assert again.delivery_count == 2
    await queue.ack([again])


async def test_abandon_makes_the_message_available_again_at_once(azure_queue) -> None:
    queue, _ = azure_queue
    await queue.enqueue(_event("abandon"))
    first = await _receive(queue, 1)
    for _ in range(8):  # more than the test queue's max delivery count (5)
        await queue.abandon(first)
        first = await _receive(queue, 1, timeout_s=2)
    (again,) = first
    assert again.delivery_count == 1  # abandon stays local: the broker never counts it
    await queue.ack([again])  # the original lock still settles it


async def test_duplicate_detection_drops_a_resend_of_the_same_batch(azure_queue) -> None:
    queue, _ = azure_queue
    await queue.enqueue(_event("same"))
    await queue.enqueue(_event("same"))  # same match:batch message id -> dropped by the broker
    await queue.enqueue(_event("other"))
    got = await _receive(queue, 2)
    await asyncio.sleep(1)
    got += await queue.receive_batch(500, 0)
    assert sorted(m.payload.batch_id for m in got) == ["other", "same"]
    await queue.ack(got)


async def test_a_poison_message_is_dead_lettered_and_the_good_one_still_arrives(
    azure_queue,
) -> None:
    queue, name = azure_queue
    async with ServiceBusClient.from_connection_string(CONN) as client:
        async with client.get_queue_sender(name) as sender:
            await sender.send_messages(ServiceBusMessage("not json at all", message_id="junk"))
        await queue.enqueue(_event("good"))
        (good,) = await _receive(queue, 1)
        assert good.payload.batch_id == "good"
        await queue.ack([good])
        async with client.get_queue_receiver(name, sub_queue=ServiceBusSubQueue.DEAD_LETTER) as dlq:
            dead = await dlq.receive_messages(max_message_count=5, max_wait_time=10)
            assert [(m.message_id, m.dead_letter_reason) for m in dead] == [
                ("junk", "invalid-payload")
            ]
            for m in dead:
                await dlq.complete_message(m)


async def test_start_fails_fast_for_a_queue_that_does_not_exist() -> None:
    queue = AzureServiceBusEventQueue(CONN, f"cb-test-missing-{uuid.uuid4().hex[:8]}")
    with pytest.raises(RuntimeError, match="Cannot open Azure Service Bus queue"):
        await queue.start()
