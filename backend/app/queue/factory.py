"""Factory that selects the correct EventQueue implementation at startup.

Usage
-----
    from app.queue.factory import make_event_queue
    from app.core.settings import get_settings

    queue = make_event_queue(get_settings())
    await queue.start()

Backends
--------
* ``memory`` (default): ``InMemoryEventQueue``.
* ``azure_service_bus``: ``AzureServiceBusEventQueue``; needs
  ``AZURE_SERVICEBUS_CONNECTION_STRING`` and ``AZURE_SERVICEBUS_QUEUE_NAME``.

Adding another backend means one adapter file plus one branch below.
"""

from __future__ import annotations

from app.core.settings import Settings
from app.queue.interfaces import EventQueue
from app.queue.memory import InMemoryEventQueue


def make_event_queue(settings: Settings) -> EventQueue:
    """Return the configured EventQueue implementation.

    Parameters
    ----------
    settings:
        Application settings.  ``settings.QUEUE_BACKEND`` selects the backend.

    Returns
    -------
    EventQueue
        The appropriate ``EventQueue`` implementation (not started yet; the app
        lifespan awaits ``start()``).

    Raises
    ------
    ValueError
        For an unknown backend, or ``azure_service_bus`` without its connection
        string or queue name.
    """
    backend = settings.QUEUE_BACKEND

    if backend == "memory":
        return InMemoryEventQueue()

    if backend == "azure_service_bus":
        conn = settings.AZURE_SERVICEBUS_CONNECTION_STRING
        queue_name = settings.AZURE_SERVICEBUS_QUEUE_NAME
        if not conn or not queue_name:
            raise ValueError(
                "QUEUE_BACKEND=azure_service_bus requires AZURE_SERVICEBUS_CONNECTION_STRING "
                "and AZURE_SERVICEBUS_QUEUE_NAME"
            )
        # Imported here only to keep the SDK off the memory backend's import path; it is still a
        # required dependency, because the backend is picked by an env var at runtime and the
        # same install (or Docker image) must be able to switch without a rebuild.
        from app.queue.azure_service_bus import AzureServiceBusEventQueue

        # The adapter times pooled messages' locks with the same value provision writes
        # into the queue's LockDuration.
        return AzureServiceBusEventQueue(
            conn, queue_name, lock_duration_s=float(settings.QUEUE_LEASE_TIMEOUT_S)
        )

    raise ValueError(f"Unknown QUEUE_BACKEND value: {backend!r}")
