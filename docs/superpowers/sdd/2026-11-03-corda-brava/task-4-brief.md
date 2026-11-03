### Task 4: EventQueue abstraction + in-memory broker-shaped impl (lease/ack/redelivery)

**Files:**
- Create: `backend/app/queue/interfaces.py` (`QueueMessage`, `EventQueue` Protocol), `backend/app/queue/memory.py`, `backend/app/queue/factory.py`
- Test: `backend/tests/queue/test_memory_queue.py`

**Interfaces:**
- Produces: `QueueMessage{id:str, payload:PullEvent, delivery_count:int}`; `EventQueue` Protocol `start/close/enqueue/receive_batch(max_messages,max_wait_s)/ack(msgs)/abandon(msgs)` exactly per `prompt.md §7`. `InMemoryEventQueue` honoring async + lease (received not deleted; unacked become visible again after `QUEUE_LEASE_TIMEOUT_S`). `make_event_queue(settings) -> EventQueue` returns memory impl for `QUEUE_BACKEND=memory`.

- [ ] **Step 1:** Write tests: `enqueue` then `receive_batch` returns leased msg; `ack` removes it (not redelivered); **kill-before-ack → after lease timeout the same batch is redelivered** (assert redelivery, use a tiny lease timeout); `receive_batch` may return empty within `max_wait_s`; factory returns `InMemoryEventQueue`.
- [ ] **Step 2:** Run (pytest-asyncio) → FAIL.
- [ ] **Step 3:** Implement memory queue + factory.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(queue): broker-shaped EventQueue + in-memory lease/ack/redelivery + tests`.

