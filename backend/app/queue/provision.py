"""Create or fix the Service Bus queue Corda Brava expects (safe to run repeatedly).

    cd backend && python -m app.queue.provision

Reads ``AZURE_SERVICEBUS_CONNECTION_STRING``, ``AZURE_SERVICEBUS_QUEUE_NAME`` and
``QUEUE_LEASE_TIMEOUT_S`` from the environment, ``backend/.env`` or the repo-root ``.env``.
Creating or updating an entity needs Manage rights (``RootManageSharedAccessKey``); the running
app itself only needs Send + Listen.

An existing queue is checked, not trusted: properties Service Bus can change in place are
updated, and a queue without duplicate detection (or with sessions) is reported as an error,
because neither can be changed after creation; that queue has to be deleted and created again.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Literal

from azure.core.exceptions import AzureError, ResourceExistsError
from azure.servicebus.management import ServiceBusAdministrationClient

from app.core.settings import settings_with_root_env

# Queue properties chosen for this app (they are entity settings, not client settings).
DEFAULT_LOCK_DURATION = timedelta(seconds=10)  # QUEUE_LEASE_TIMEOUT_S's default
MIN_LOCK_DURATION, MAX_LOCK_DURATION = timedelta(seconds=5), timedelta(minutes=5)  # broker limits
MAX_DELIVERY_COUNT = 10  # lock expiries before a message is dead-lettered (abandon is local)
MESSAGE_TTL = timedelta(hours=1)  # a pull is worthless once its match is over
DUPLICATE_DETECTION_WINDOW = timedelta(minutes=10)  # broker-side dedup on message_id


class QueueMismatchError(Exception):
    """The queue exists with a property that cannot be changed in place."""


@dataclass
class QueueStatus:
    outcome: Literal["created", "updated", "unchanged"]
    changed: list[str] = field(default_factory=list)  # property names, for "updated"


def _wanted(lock_duration: timedelta) -> dict[str, object]:
    """Properties ``update_queue`` can set on an existing queue."""
    return {
        "lock_duration": lock_duration,
        "max_delivery_count": MAX_DELIVERY_COUNT,
        "default_message_time_to_live": MESSAGE_TTL,
        "duplicate_detection_history_time_window": DUPLICATE_DETECTION_WINDOW,
    }


def ensure_queue(
    connection_string: str, queue_name: str, lock_duration: timedelta = DEFAULT_LOCK_DURATION
) -> QueueStatus:
    """Create the queue, or bring an existing one in line with what the app relies on.

    Raises ``QueueMismatchError`` for an existing queue that would need to be recreated.
    """
    if not MIN_LOCK_DURATION <= lock_duration <= MAX_LOCK_DURATION:
        raise ValueError(
            f"lock duration {lock_duration.total_seconds():g} s is outside Service Bus's "
            "5-300 s range (QUEUE_LEASE_TIMEOUT_S)"
        )
    wanted = _wanted(lock_duration)
    with ServiceBusAdministrationClient.from_connection_string(connection_string) as admin:
        try:
            admin.create_queue(queue_name, requires_duplicate_detection=True, **wanted)
        except ResourceExistsError:
            pass
        else:
            return QueueStatus("created")

        props = admin.get_queue(queue_name)
        fatal = []
        if not props.requires_duplicate_detection:
            fatal.append("duplicate detection is off")
        if props.requires_session:
            fatal.append("it requires sessions")
        if fatal:
            raise QueueMismatchError(
                f"Queue {queue_name!r} exists but {' and '.join(fatal)}, which cannot be changed "
                "after creation. Delete it (portal: Service Bus namespace > Queues, or "
                "`az servicebus queue delete`) while no match is running, then run this again."
            )
        changed = [name for name, value in wanted.items() if getattr(props, name) != value]
        if not changed:
            return QueueStatus("unchanged")
        for name in changed:
            setattr(props, name, wanted[name])
        admin.update_queue(props)
        return QueueStatus("updated", changed)


def main() -> int:
    settings = settings_with_root_env()
    conn, name = settings.AZURE_SERVICEBUS_CONNECTION_STRING, settings.AZURE_SERVICEBUS_QUEUE_NAME
    if not conn or not name:
        print(
            "Set AZURE_SERVICEBUS_CONNECTION_STRING and AZURE_SERVICEBUS_QUEUE_NAME "
            "(environment, backend/.env or the repo-root .env).",
            file=sys.stderr,
        )
        return 2
    lock_duration = timedelta(seconds=settings.QUEUE_LEASE_TIMEOUT_S)
    try:
        status = ensure_queue(conn, name, lock_duration)
    except ValueError as exc:
        print(f"Cannot provision queue {name!r}: {exc}", file=sys.stderr)
        return 2
    except QueueMismatchError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except AzureError as exc:
        print(
            f"Could not create or update queue {name!r}: {exc.message or exc}\n"
            "Use the namespace-level RootManageSharedAccessKey connection string "
            "(no EntityPath).",
            file=sys.stderr,
        )
        return 1
    if status.outcome == "updated":
        print(f"Queue {name!r}: updated ({', '.join(status.changed)})")
    else:
        print(f"Queue {name!r}: {status.outcome}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
