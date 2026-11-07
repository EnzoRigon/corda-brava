"""In-process stand-in for the azure-servicebus async SDK (one peek-lock queue).

It reproduces the behaviours the adapter has to cope with, as measured against a real
Standard namespace:

* two coroutines on one sender (or on one receiver) at the same time fail, as in the SDK;
* ``receive_messages`` rejects ``max_wait_time <= 0``;
* ``delivery_count`` is 0 on the first delivery and grows on abandon and on lock expiry;
* settling a message whose lock expired raises ``MessageLockLostError``;
* a settle that overlaps a receive on the same receiver fails (the SDK receiver is not
  coroutine-safe; the adapter must never do this, and ``settles_during_receive`` counts it);
* a batch has a capacity; ``add_message`` raises ``MessageSizeExceededError`` beyond it.

Time is a manual clock: ``broker.advance(seconds)`` expires locks without sleeping, and
``broker.clock`` is that clock for the adapter's ``time_fn``.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from azure.servicebus import ServiceBusMessage
from azure.servicebus.exceptions import (
    MessageAlreadySettled,
    MessageLockLostError,
    MessageSizeExceededError,
    ServiceBusError,
)


@dataclass
class FakeReceivedMessage:
    """What the SDK's ``ServiceBusReceivedMessage`` exposes that the adapter reads."""

    message_id: str | None
    delivery_count: int
    body: str
    lock_expires_at: float
    settled: bool = False
    dead_letter_reason: str | None = None
    dead_letter_error_description: str | None = None

    def __str__(self) -> str:
        return self.body


@dataclass
class _Stored:
    message_id: str | None
    body: str
    delivery_count: int = 0
    lock: FakeReceivedMessage | None = None


@dataclass
class FakeBroker:
    lock_duration_s: float = 30.0
    batch_capacity: int = 10_000  # messages per batch
    now: float = 0.0
    ready: list[_Stored] = field(default_factory=list)
    locked: list[_Stored] = field(default_factory=list)
    dead_letters: list[FakeReceivedMessage] = field(default_factory=list)
    sent_batches: list[int] = field(default_factory=list)  # size of every send_messages call
    sent_messages: list[ServiceBusMessage] = field(default_factory=list)
    receive_waits: list[float] = field(default_factory=list)  # max_wait_time of every receive
    open_links: int = 0
    clients_opened: int = 0
    clients_closed: int = 0
    fail_open: Exception | None = None  # raised when a sender/receiver link opens
    fail_next_send: Exception | None = None
    max_concurrent_settles: int = 0
    abandons: int = 0  # abandon_message calls that reached the broker
    settles_during_receive: int = 0
    receiving: bool = False
    _settling: int = 0

    # ── test helpers ──────────────────────────────────────────────────────────

    def client(self, _connection_string: str) -> FakeClient:
        """``client_factory`` for the adapter."""
        return FakeClient(self)

    def publish_raw(self, body: str, message_id: str | None = None) -> None:
        """Put a message on the queue as some other producer would."""
        self.ready.append(_Stored(message_id, body))

    def clock(self) -> float:
        """The manual clock (``time_fn`` for the adapter)."""
        return self.now

    def advance(self, seconds: float) -> None:
        """Move the clock; messages whose lock ran out become visible again."""
        self.now += seconds
        for stored in [s for s in self.locked if s.lock and s.lock.lock_expires_at <= self.now]:
            self.locked.remove(stored)
            stored.delivery_count += 1
            stored.lock = None
            self.ready.append(stored)

    @property
    def depth(self) -> int:
        """Messages still on the queue (visible or locked), excluding the dead-letter queue."""
        return len(self.ready) + len(self.locked)

    # ── used by the fake sender/receiver ──────────────────────────────────────

    def _lock_up_to(self, count: int) -> list[FakeReceivedMessage]:
        out = []
        while self.ready and len(out) < count:
            stored = self.ready.pop(0)
            stored.lock = FakeReceivedMessage(
                stored.message_id,
                stored.delivery_count,
                stored.body,
                self.now + self.lock_duration_s,
            )
            self.locked.append(stored)
            out.append(stored.lock)
        return out

    def _find_locked(self, message: FakeReceivedMessage, action: str) -> _Stored:
        if message.settled:
            raise MessageAlreadySettled(action=action)
        if message.lock_expires_at <= self.now:
            raise MessageLockLostError(message="The lock on the message has expired.")
        for stored in self.locked:
            if stored.lock is message:
                return stored
        raise MessageLockLostError(message="The lock on the message has expired.")

    async def _settle(self, message: FakeReceivedMessage, action: str, **details: str) -> None:
        if self.receiving:
            self.settles_during_receive += 1
            raise ServiceBusError(f"{action} overlapped a receive on the same receiver")
        if action == "abandon":
            self.abandons += 1
        self._settling += 1
        self.max_concurrent_settles = max(self.max_concurrent_settles, self._settling)
        try:
            await asyncio.sleep(0)  # a broker round trip: lets other settles overlap
            if self.receiving:
                self.settles_during_receive += 1
                raise ServiceBusError(f"{action} overlapped a receive on the same receiver")
            stored = self._find_locked(message, action)
            self.locked.remove(stored)
            message.settled = True
            if action == "abandon":
                stored.delivery_count += 1
                stored.lock = None
                self.ready.append(stored)
            elif action == "dead-letter":
                message.dead_letter_reason = details.get("reason")
                message.dead_letter_error_description = details.get("error_description")
                self.dead_letters.append(message)
        finally:
            self._settling -= 1


class FakeBatch:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.messages: list[ServiceBusMessage] = []

    def add_message(self, message: ServiceBusMessage) -> None:
        if len(self.messages) >= self.capacity:
            raise MessageSizeExceededError(message="batch is full")
        self.messages.append(message)

    def __len__(self) -> int:
        return len(self.messages)


class _SingleUser:
    """Fails like the SDK when two coroutines use the same sender/receiver at once."""

    def __init__(self) -> None:
        self._busy = False

    def _enter(self, what: str) -> None:
        if self._busy:
            raise ServiceBusError(f"concurrent {what} on the same link")
        self._busy = True

    def _leave(self) -> None:
        self._busy = False


class FakeSender(_SingleUser):
    def __init__(self, broker: FakeBroker) -> None:
        super().__init__()
        self.broker = broker

    async def __aenter__(self) -> FakeSender:
        if self.broker.fail_open is not None:
            raise self.broker.fail_open
        self.broker.open_links += 1
        return self

    async def __aexit__(self, *exc: object) -> None:
        self.broker.open_links -= 1

    async def create_message_batch(self) -> FakeBatch:
        return FakeBatch(self.broker.batch_capacity)

    async def send_messages(self, batch: FakeBatch, timeout: float | None = None) -> None:
        self._enter("send")
        try:
            await asyncio.sleep(0)  # a broker round trip: a second sender would overlap here
            if self.broker.fail_next_send is not None:
                exc, self.broker.fail_next_send = self.broker.fail_next_send, None
                raise exc
            self.broker.sent_batches.append(len(batch))
            for message in batch.messages:
                self.broker.sent_messages.append(message)
                self.broker.ready.append(_Stored(message.message_id, str(message)))
        finally:
            self._leave()


class FakeReceiver(_SingleUser):
    def __init__(self, broker: FakeBroker) -> None:
        super().__init__()
        self.broker = broker

    async def __aenter__(self) -> FakeReceiver:
        if self.broker.fail_open is not None:
            raise self.broker.fail_open
        self.broker.open_links += 1
        return self

    async def __aexit__(self, *exc: object) -> None:
        self.broker.open_links -= 1

    async def receive_messages(
        self, max_message_count: int = 1, max_wait_time: float | None = None
    ) -> list[FakeReceivedMessage]:
        if max_wait_time is not None and max_wait_time <= 0:
            raise ValueError("The max_wait_time must be greater than 0.")
        self._enter("receive")
        if self.broker._settling:
            self.broker.settles_during_receive += 1
            self._leave()
            raise ServiceBusError("receive overlapped a settle on the same receiver")
        self.broker.receiving = True
        try:
            self.broker.receive_waits.append(max_wait_time or 0.0)
            await asyncio.sleep(0)  # a second receiver call (or a settle) would overlap here
            return self.broker._lock_up_to(max_message_count)
        finally:
            self.broker.receiving = False
            self._leave()

    async def complete_message(self, message: FakeReceivedMessage) -> None:
        await self.broker._settle(message, "complete")

    async def abandon_message(self, message: FakeReceivedMessage) -> None:
        await self.broker._settle(message, "abandon")

    async def dead_letter_message(
        self,
        message: FakeReceivedMessage,
        reason: str | None = None,
        error_description: str | None = None,
    ) -> None:
        await self.broker._settle(
            message, "dead-letter", reason=reason or "", error_description=error_description or ""
        )


class FakeClient:
    fully_qualified_namespace = "fake.servicebus.local"

    def __init__(self, broker: FakeBroker) -> None:
        self.broker = broker

    async def __aenter__(self) -> FakeClient:
        self.broker.clients_opened += 1
        return self

    async def __aexit__(self, *exc: object) -> None:
        self.broker.clients_closed += 1

    def get_queue_sender(self, queue_name: str) -> FakeSender:
        return FakeSender(self.broker)

    def get_queue_receiver(self, queue_name: str, **kwargs: object) -> FakeReceiver:
        return FakeReceiver(self.broker)
