"""Factory that selects the correct EventQueue implementation at startup.

Usage
-----
    from app.queue.factory import make_event_queue
    from app.core.settings import get_settings

    queue = make_event_queue(get_settings())
    await queue.start()

Adding a new backend
--------------------
1. Create ``app/queue/azure_service_bus.py`` with
   ``AzureServiceBusEventQueue(EventQueue)``.
2. Add the import and ``elif`` branch below.
3. Set ``QUEUE_BACKEND=azure_service_bus`` in the environment.

No other file changes are needed.
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
        The appropriate ``EventQueue`` implementation.  For ``memory``, this is
        ``InMemoryEventQueue``.  For ``azure_service_bus``, a
        ``NotImplementedError`` is raised until the adapter is implemented.
    """
    backend = settings.QUEUE_BACKEND

    if backend == "memory":
        return InMemoryEventQueue()

    if backend == "azure_service_bus":
        raise NotImplementedError(
            "Azure Service Bus backend is not yet implemented.  "
            "Create AzureServiceBusEventQueue in app/queue/azure_service_bus.py "
            "using the azure-servicebus async SDK, then wire it here."
        )

    raise ValueError(f"Unknown QUEUE_BACKEND value: {backend!r}")
