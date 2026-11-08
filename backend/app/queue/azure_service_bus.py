"""Azure Service Bus implementation of ``EventQueue`` (one queue, peek-lock).

How the broker-shaped contract maps onto Service Bus
----------------------------------------------------
* ``enqueue``       -> send.  Messages are group-committed: a single task owns the sender and
                       ships everything that piled up while the previous send was in flight as
                       one ``ServiceBusMessageBatch`` (see ``_pump``).
* ``receive_batch`` -> one ``receive_messages`` in PEEK_LOCK mode with ``prefetch_count=0``,
                       shared by every caller that arrives while it is in flight (see
                       ``_fetch``), then up to ``max_messages`` from the local pool.
* ``ack``           -> ``complete_message``, settled in parallel.
* ``abandon``       -> the message, still locked, goes back to a local pool that the next
                       ``receive_batch`` (from any caller) serves.  The broker is not told, so the
                       delivery count does not grow, as the contract requires.
                       ``abandon_message`` would count as a delivery attempt: with one queue
                       shared by all matches every loop abandons the other matches' pulls each
                       tick, and with a few matches running those pulls would reach
                       ``MaxDeliveryCount`` and be dead-lettered without ever being applied.
* lease timeout     -> the queue's ``LockDuration``, which ``python -m app.queue.provision`` sets
                       from ``QUEUE_LEASE_TIMEOUT_S`` (the in-memory queue's lease).  The adapter
                       gets the same value as ``lock_duration_s`` and lets a pooled message go
                       when its lock is about to run out (timed on the local monotonic clock, so
                       a drifting wall clock cannot discard fresh messages); the broker then
                       redelivers it.
* redelivery        -> the broker makes an unsettled message visible again when its lock expires.
* poison payloads   -> dead-lettered with reason ``invalid-payload``; they never reach the
                       consumer.

The pool lives in this process, which matches the single-worker deployment (the dedup map and
the match registry are per-process too).  With several processes on one queue, a message one
process abandoned is only served to that process until its lock expires.

Why the SDK is driven this carefully (measured against a Standard namespace, ~54 ms RTT)
----------------------------------------------------------------------------------------
* 50 concurrent ``send_messages`` on one sender: 49 failed.  One send per message would also
  cap throughput at ~1/RTT (~18 msg/s), while batches of 100-500 reach 285-800 msg/s.
* Two concurrent ``receive_messages`` on one receiver interfere (one got nothing although
  messages were available).  Callers that arrive during a receive therefore join it instead of
  queueing their own, so N match loops cost one broker round trip per poll, not N.
* ``complete_message`` waits for the broker's outcome: 50 sequential completes took 7.4 s,
  100 in parallel took 0.26 s.  Settles therefore run in parallel and may overlap other
  settles, but never a receive (the SDK receiver is not coroutine-safe; see ``_ReceiveGate``).
* ``receive_messages`` rejects ``max_wait_time <= 0`` and, with the queue empty, takes ~0.2 s
  however small the wait is (internal polling granularity); the consumer asks for ``0``.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from functools import partial

from azure.servicebus import ServiceBusMessage, ServiceBusReceivedMessage, ServiceBusReceiveMode
from azure.servicebus.aio import ServiceBusClient, ServiceBusReceiver, ServiceBusSender
from azure.servicebus.exceptions import MessageSizeExceededError

from app.domain.entities import PullEvent
from app.queue.interfaces import QueueMessage

log = logging.getLogger(__name__)

MAX_SEND_BATCH = 500  # messages per send; the SDK also splits on the broker's size limit
SEND_TIMEOUT_S = 10.0  # total budget (retries included) before a send fails with a 503
MAX_PARALLEL_SETTLES = 100  # complete/dead-letter calls in flight at once
MIN_RECEIVE_WAIT_S = 0.1  # the SDK rejects a zero wait, but the consumer polls with 0
DEFAULT_LOCK_DURATION_S = 10.0  # QUEUE_LEASE_TIMEOUT_S's default; provision sets the queue to it
LOCK_MARGIN_S = 2.0  # a pooled message this close to losing its lock is let go
DEAD_LETTER_REASON = "invalid-payload"
MAX_IDS_IN_LOG = 5


@dataclass
class _Outgoing:
    """A message waiting in the outbox plus the future its ``enqueue`` caller awaits."""

    message: ServiceBusMessage
    done: asyncio.Future[None]


@dataclass(eq=False)
class _Locked:
    """``QueueMessage.raw`` for this adapter: the SDK message and when its lock runs out."""

    message: ServiceBusReceivedMessage
    expires_at: float  # on the adapter's ``time_fn`` clock


# (message id for logs, zero-argument settle call)
_Settle = tuple[str, Callable[[], Awaitable[None]]]


def _resolve(items: list[_Outgoing], exc: BaseException | None = None) -> None:
    """Complete the callers' futures (success when ``exc`` is None); skips cancelled ones."""
    for item in items:
        if item.done.done():
            continue
        if exc is None:
            item.done.set_result(None)
        else:
            item.done.set_exception(exc)


def _retrieve_exception(task: asyncio.Task[None]) -> None:
    """Mark a shared task's failure as seen even if every caller awaiting it was cancelled."""
    if not task.cancelled():
        task.exception()


class _ReceiveGate:
    """A receive runs alone; settles may overlap one another but never a receive.

    A receive that is waiting holds back new settles, so a steady stream of acks from several
    match loops cannot starve it.
    """

    def __init__(self) -> None:
        self._cond = asyncio.Condition()
        self._receiving = False
        self._receives_waiting = 0
        self._settling = 0

    @asynccontextmanager
    async def receiving(self) -> AsyncGenerator[None, None]:
        async with self._cond:
            self._receives_waiting += 1
            try:
                await self._cond.wait_for(lambda: not self._receiving and self._settling == 0)
            finally:
                self._receives_waiting -= 1
                self._cond.notify_all()
            self._receiving = True
        try:
            yield
        finally:
            async with self._cond:
                self._receiving = False
                self._cond.notify_all()

    @asynccontextmanager
    async def settling(self) -> AsyncGenerator[None, None]:
        async with self._cond:
            await self._cond.wait_for(lambda: not self._receiving and self._receives_waiting == 0)
            self._settling += 1
        try:
            yield
        finally:
            async with self._cond:
                self._settling -= 1
                self._cond.notify_all()


class AzureServiceBusEventQueue:
    """``EventQueue`` backed by a single Azure Service Bus queue.

    Parameters
    ----------
    connection_string:
        Namespace-level connection string (no ``EntityPath``).  Needs Send and Listen claims.
    queue_name:
        The queue; it must already exist (``python -m app.queue.provision`` creates it).
    min_receive_wait_s:
        Floor for ``receive_batch``'s wait; see the module docstring.
    lock_duration_s:
        The queue's ``LockDuration`` (``QUEUE_LEASE_TIMEOUT_S``).  If the queue's real value is
        longer, pooled messages are let go early (they come back when the lock expires); if it
        is shorter, an ack may hit a lost lock (logged; the redelivery is deduplicated).
    client_factory:
        Builds the SDK client from the connection string.  Tests inject a fake broker here.
    time_fn:
        Monotonic clock for lock deadlines.  Tests inject the fake broker's clock.
    """

    def __init__(
        self,
        connection_string: str,
        queue_name: str,
        *,
        lock_duration_s: float = DEFAULT_LOCK_DURATION_S,
        min_receive_wait_s: float = MIN_RECEIVE_WAIT_S,
        client_factory: Callable[[str], ServiceBusClient] = ServiceBusClient.from_connection_string,
        time_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        self._connection_string = connection_string
        self._queue_name = queue_name
        self._lock_duration_s = lock_duration_s
        self._min_receive_wait_s = min_receive_wait_s
        self._client_factory = client_factory
        self._time_fn = time_fn

        self._stack: AsyncExitStack | None = None
        self._sender: ServiceBusSender | None = None
        self._receiver: ServiceBusReceiver | None = None
        self._outbox: asyncio.Queue[_Outgoing] | None = None
        self._pump_task: asyncio.Task[None] | None = None
        self._fetch_task: asyncio.Task[None] | None = None
        self._gate = _ReceiveGate()
        # Locked messages no caller currently holds, oldest first (keyed by their ``_Locked``).
        self._pool: dict[int, QueueMessage] = {}

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Open the sender and receiver links; fails fast on a bad key or a missing queue."""
        if self._stack is not None:
            return
        stack = AsyncExitStack()
        try:
            client = await stack.enter_async_context(self._client_factory(self._connection_string))
            self._sender = await stack.enter_async_context(
                client.get_queue_sender(queue_name=self._queue_name)
            )
            self._receiver = await stack.enter_async_context(
                client.get_queue_receiver(
                    queue_name=self._queue_name,
                    receive_mode=ServiceBusReceiveMode.PEEK_LOCK,
                    prefetch_count=0,  # no locks held between polls, no delivery-count churn
                )
            )
        except Exception as exc:
            await stack.aclose()
            self._sender = self._receiver = None
            raise RuntimeError(
                f"Cannot open Azure Service Bus queue {self._queue_name!r}: {exc}. Check "
                "AZURE_SERVICEBUS_CONNECTION_STRING (namespace-level, Send+Listen), that the "
                "queue exists (python -m app.queue.provision) and that port 5671 is reachable."
            ) from exc
        self._stack = stack
        self._outbox = asyncio.Queue()
        self._pump_task = asyncio.create_task(
            self._pump(self._outbox, self._sender), name="servicebus-send-pump"
        )
        log.info(
            "Azure Service Bus queue %r ready on %s",
            self._queue_name,
            getattr(client, "fully_qualified_namespace", "?"),
        )

    async def close(self) -> None:
        """Stop the send pump (failing anything still queued) and close the connection.

        Pooled messages are dropped; their locks expire and the broker redelivers them.
        """
        stack, self._stack = self._stack, None
        if stack is None:
            return
        for task in (self._pump_task, self._fetch_task):
            if task is None:
                continue
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:  # noqa: BLE001 - still close the connection below
                log.exception("%s had crashed before close", task.get_name())
        self._pump_task = self._fetch_task = None
        outbox, self._outbox = self._outbox, None
        while outbox is not None and not outbox.empty():
            _resolve([outbox.get_nowait()], RuntimeError("queue closed"))
        self._pool.clear()
        self._sender = self._receiver = None
        await stack.aclose()

    def _started_receiver(self) -> ServiceBusReceiver:
        if self._receiver is None:
            raise RuntimeError("AzureServiceBusEventQueue is not started")
        return self._receiver

    # ── Send side ─────────────────────────────────────────────────────────────

    async def enqueue(self, event: PullEvent) -> None:
        """Publish ``event``; returns once the broker has accepted it (or raises)."""
        outbox, pump = self._outbox, self._pump_task
        if outbox is None or pump is None or pump.done():
            raise RuntimeError("AzureServiceBusEventQueue is not started")
        message = ServiceBusMessage(
            event.model_dump_json(),
            message_id=f"{event.match_id}:{event.batch_id}",
            content_type="application/json",
            subject="pull",
            application_properties={"match_id": event.match_id, "team": event.team.value},
        )
        done: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        outbox.put_nowait(_Outgoing(message, done))
        await done

    @staticmethod
    async def _pump(outbox: asyncio.Queue[_Outgoing], sender: ServiceBusSender) -> None:
        """Single sender task: ships whatever accumulated since the last send as one batch."""
        while True:
            items = [await outbox.get()]
            while len(items) < MAX_SEND_BATCH and not outbox.empty():
                items.append(outbox.get_nowait())
            try:
                await AzureServiceBusEventQueue._flush(sender, items)
            except asyncio.CancelledError:
                _resolve(items, RuntimeError("queue closed"))
                raise

    @staticmethod
    async def _flush(sender: ServiceBusSender, items: list[_Outgoing]) -> None:
        todo = list(items)
        while todo:
            chunk: list[_Outgoing] = []
            try:
                batch = await sender.create_message_batch()
                while todo:
                    try:
                        batch.add_message(todo[0].message)
                    except MessageSizeExceededError as exc:
                        if chunk:
                            break
                        _resolve([todo.pop(0)], exc)
                        continue
                    chunk.append(todo.pop(0))
                if chunk:
                    await sender.send_messages(batch, timeout=SEND_TIMEOUT_S)
            except Exception as exc:  # noqa: BLE001 - every caller must hear about the failure
                log.error(
                    "Service Bus send failed for %d message(s): %r", len(chunk) + len(todo), exc
                )
                _resolve(chunk + todo, exc)
                return
            _resolve(chunk)

    # ── Receive side ──────────────────────────────────────────────────────────

    async def receive_batch(self, max_messages: int, max_wait_s: float) -> list[QueueMessage]:
        """Lock up to ``max_messages`` messages, waiting up to ``max_wait_s`` for the first.

        A caller that arrives while another caller's receive is in flight joins that receive
        (and its wait) instead of starting a second one.
        """
        receiver = self._started_receiver()
        if max_messages <= 0:
            return []
        fetch = self._fetch_task
        if fetch is None or fetch.done():
            wait = max(max_wait_s, self._min_receive_wait_s)
            fetch = asyncio.create_task(
                self._fetch(receiver, max_messages, wait), name="servicebus-receive"
            )
            fetch.add_done_callback(_retrieve_exception)
            self._fetch_task = fetch
        # Shielded: a cancelled caller must not cancel a receive others are waiting on; whatever
        # it brings in stays in the pool for the next caller.
        await asyncio.shield(fetch)
        return self._take(max_messages)

    async def _fetch(self, receiver: ServiceBusReceiver, count: int, wait: float) -> None:
        """One broker receive into the pool; unparseable messages are dead-lettered."""
        async with self._gate.receiving():
            # The broker locks each message at or after this instant, so the deadline is safe.
            expires_at = self._time_fn() + self._lock_duration_s
            raws = await receiver.receive_messages(max_message_count=count, max_wait_time=wait)
            poison: list[tuple[ServiceBusReceivedMessage, ValueError]] = []
            for raw in raws:
                try:
                    event = PullEvent.model_validate_json(str(raw))
                except ValueError as exc:  # pydantic's ValidationError is a ValueError
                    poison.append((raw, exc))
                    continue
                handle = _Locked(raw, expires_at)
                self._pool[id(handle)] = QueueMessage(
                    id=str(raw.message_id or event.batch_id),
                    payload=event,
                    delivery_count=(raw.delivery_count or 0) + 1,  # the broker counts from 0
                    raw=handle,
                )
            if poison:
                await self._dead_letter(receiver, poison)

    def _take(self, max_messages: int) -> list[QueueMessage]:
        """Hand out up to ``max_messages`` pooled messages, oldest first."""
        horizon = self._time_fn() + LOCK_MARGIN_S
        taken: list[QueueMessage] = []
        for key in list(self._pool):
            if len(taken) >= max_messages:
                break
            message = self._pool.pop(key)
            if message.raw.expires_at <= horizon:
                log.debug("letting %s go: its lock is about to run out", message.id)
                continue  # the broker redelivers it once the lock expires
            taken.append(message)
        return taken

    async def ack(self, messages: list[QueueMessage]) -> None:
        """Complete the messages.  A failed settle is logged, not raised: the broker redelivers
        the message and the consumer's ``batchId`` dedup makes that harmless."""
        receiver = self._started_receiver()
        if not messages:
            return
        async with self._gate.settling():
            await self._settle_parallel(
                [(m.id, partial(receiver.complete_message, m.raw.message)) for m in messages],
                "complete",
            )

    async def abandon(self, messages: list[QueueMessage]) -> None:
        """Give the messages back to the pool (still locked) for the next ``receive_batch``.

        No broker call: Service Bus would count an abandon as a delivery attempt.  Abandoned
        messages go to the back of the pool so a loop does not get the same foreign messages
        first on every poll.
        """
        self._started_receiver()
        for message in messages:
            if not isinstance(message.raw, _Locked):
                continue  # not one of ours
            key = id(message.raw)
            self._pool.pop(key, None)
            self._pool[key] = message

    async def _dead_letter(
        self,
        receiver: ServiceBusReceiver,
        poison: list[tuple[ServiceBusReceivedMessage, ValueError]],
    ) -> None:
        """Dead-letter unparseable messages (called inside the receive, which runs alone)."""
        targets: list[_Settle] = []
        for raw, exc in poison:
            reason = " ".join(str(exc).split()) or type(exc).__name__  # one condensed line
            log.warning("Dead-lettering message %s: %s", raw.message_id, reason)
            targets.append(
                (
                    str(raw.message_id),
                    partial(
                        receiver.dead_letter_message,
                        raw,
                        reason=DEAD_LETTER_REASON,
                        error_description=reason[:200],
                    ),
                )
            )
        await self._settle_parallel(targets, "dead-letter")

    @staticmethod
    async def _settle_parallel(targets: list[_Settle], verb: str) -> None:
        """Run every settle (at most ``MAX_PARALLEL_SETTLES`` at once); never raises for one.

        Any failure (lost lock, closed or reconnecting receiver, ...) leaves the message to the
        broker, which redelivers it when its lock expires.
        """
        gate = asyncio.Semaphore(MAX_PARALLEL_SETTLES)
        failures: list[tuple[str, Exception]] = []

        async def one(message_id: str, action: Callable[[], Awaitable[None]]) -> None:
            async with gate:
                try:
                    await action()
                except Exception as exc:  # noqa: BLE001 - one failure must not stop the rest
                    failures.append((message_id, exc))

        await asyncio.gather(*(one(message_id, action) for message_id, action in targets))
        if failures:
            ids = ", ".join(message_id for message_id, _ in failures[:MAX_IDS_IN_LOG])
            more = ", ..." if len(failures) > MAX_IDS_IN_LOG else ""
            log.warning(
                "%s failed for %d of %d message(s) [%s%s]; the broker will redeliver them: %r",
                verb,
                len(failures),
                len(targets),
                ids,
                more,
                failures[0][1],
            )
