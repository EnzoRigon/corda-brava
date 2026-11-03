# Task 4 Report — EventQueue abstraction + in-memory broker-shaped implementation

**Date:** 2026-11-03
**Status:** DONE

---

## 1. Files Created

| File | Purpose |
|------|---------|
| `backend/app/queue/__init__.py` | Package marker |
| `backend/app/queue/interfaces.py` | `QueueMessage` dataclass + `EventQueue` Protocol |
| `backend/app/queue/memory.py` | `InMemoryEventQueue` (async, lease, ack, redelivery) |
| `backend/app/queue/factory.py` | `make_event_queue(settings)` factory |
| `backend/tests/queue/__init__.py` | Test package marker |
| `backend/tests/queue/test_memory_queue.py` | 11 async tests |

---

## 2. QueueMessage / EventQueue signatures (verbatim)

```python
@dataclass
class QueueMessage:
    id: str                 # broker message id (uses batch_id for in-memory)
    payload: PullEvent
    delivery_count: int = field(default=1)

class EventQueue(Protocol):
    async def start(self) -> None: ...                 # connect (no-op in memory)
    async def close(self) -> None: ...
    async def enqueue(self, event: PullEvent) -> None: ...
    async def receive_batch(self, max_messages: int, max_wait_s: float) -> list[QueueMessage]: ...  # leased, not deleted
    async def ack(self, messages: list[QueueMessage]) -> None: ...      # complete/remove
    async def abandon(self, messages: list[QueueMessage]) -> None: ...  # release lease early
```

---

## 3. InMemoryEventQueue constructor — injectable lease/clock

```python
class InMemoryEventQueue:
    def __init__(
        self,
        *,
        lease_timeout_s: float | None = None,
        time_fn: Callable[[], float] | object = _SENTINEL,
    ) -> None:
```

- `lease_timeout_s`: overrides `settings.QUEUE_LEASE_TIMEOUT_S` (default 10 s). Tests pass `0.05` so redelivery can be forced without real-time waiting.
- `time_fn`: monotonic clock (defaults to `time.monotonic`). Can be overridden in tests to simulate time passage; currently tests just use `asyncio.sleep` with the tiny timeout.

---

## 4. Lease-expiry reclaim mechanism

Inside `receive_batch`, before serving any new messages, the method calls `_reclaim_expired_leases()` (lock held). This iterates the `_inflight` dict and moves any entry whose `expires_at <= now()` back to the `_pending` deque, with `delivery_count` incremented by 1. The reclaimed message is a new `QueueMessage` object (same `id` and `payload`) so the redelivery is transparent to consumers.

```
receive_batch() flow:
  1. acquire lock
  2. _reclaim_expired_leases()       # check inflight for expires_at <= now
  3. if pending: _take_messages()    # move from pending → inflight with new expiry
  4. release lock
  5. if none found: sleep 10ms, retry until deadline
```

---

## 5. Factory behavior

```python
def make_event_queue(settings: Settings) -> EventQueue:
    if backend == "memory":
        return InMemoryEventQueue()
    if backend == "azure_service_bus":
        raise NotImplementedError(
            "...Create AzureServiceBusEventQueue in app/queue/azure_service_bus.py..."
        )
```

- `QUEUE_BACKEND=memory` → returns `InMemoryEventQueue()` (default lease from settings)
- `QUEUE_BACKEND=azure_service_bus` → `NotImplementedError` explicitly naming `AzureServiceBusEventQueue`
- Azure settings (`AZURE_SERVICEBUS_CONNECTION_STRING` / `_QUEUE_NAME`) are never accessed for the memory backend

---

## 6. Test results

```
71 passed in 0.72s  (60 prior + 11 new queue tests)
ruff: All checks passed
black: 6 files would be left unchanged
```

### Queue-specific tests (11)

| Test | What it verifies |
|------|-----------------|
| `test_start_is_noop` | `start()` and `close()` complete without error |
| `test_enqueue_then_receive_returns_message` | `enqueue` + `receive_batch` returns leased `QueueMessage` |
| `test_received_message_is_leased_not_deleted` | Second receive while lease active returns empty |
| `test_ack_removes_message_permanently` | After `ack`, never redelivered |
| **`test_redelivery_after_lease_expiry`** | Core at-least-once proof: 0.05s lease, sleep past expiry, assert `delivery_count >= 2` |
| `test_abandon_returns_message_to_pending_immediately` | `abandon` makes message visible on next receive |
| `test_receive_batch_waits_and_returns_empty_when_queue_empty` | Returns `[]` and waits ~`max_wait_s` |
| `test_receive_batch_returns_quickly_when_message_available` | Returns in <1s when message ready |
| `test_receive_batch_respects_max_messages` | Returns at most `max_messages` items |
| `test_factory_memory_returns_inmemory_instance` | Factory → `isinstance(InMemoryEventQueue)` |
| `test_factory_azure_raises_not_implemented` | Factory raises `NotImplementedError` mentioning `AzureServiceBusEventQueue` |

### Redelivery test output (key excerpt)

```
tests/queue/test_memory_queue.py::test_redelivery_after_lease_expiry PASSED
```

Lease set to 0.05 s; after `asyncio.sleep(0.1)`, the second `receive_batch` returned the same message with `delivery_count=2`, proving genuine at-least-once redelivery.

---

## 7. Future Azure Service Bus adapter

To implement the Azure backend:
1. Create `backend/app/queue/azure_service_bus.py` with `AzureServiceBusEventQueue` using `azure-servicebus` async SDK (`ServiceBusClient.from_connection_string`, `receive_messages`, `complete_message`).
2. Add one import + `elif` branch in `factory.py`.
3. Set `QUEUE_BACKEND=azure_service_bus` in env.

No other file changes are needed (zero consumer-loop changes).
