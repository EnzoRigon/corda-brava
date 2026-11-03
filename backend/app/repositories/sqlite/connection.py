"""SQLite connection factory for Corda Brava.

Design notes
------------
WAL mode:  Every connection immediately executes ``PRAGMA journal_mode=WAL``
           so readers do not block writers and vice versa.

check_same_thread=False:
           SQLite's default is to raise if a connection is used from a
           different thread than the one that created it.  We disable that
           check here and instead enforce single-writer semantics via a
           module-level threading.Lock (_WRITE_LOCK).  Readers are safe to
           run concurrently in WAL mode; all write operations must acquire
           the lock before executing.

Usage:
    conn = get_connection(db_path)
    # reads: no lock needed
    rows = conn.execute("SELECT ...").fetchall()
    # writes: acquire the lock
    with write_lock():
        conn.execute("INSERT INTO ...")
        conn.commit()
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

_WRITE_LOCK: threading.Lock = threading.Lock()

# Cache one open connection per db_path string to avoid opening/closing
# on every repo call.  For production (one path) this is effectively a
# module-level singleton.
_CONNECTIONS: dict[str, sqlite3.Connection] = {}


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Return (and cache) a WAL-mode sqlite3 connection for *db_path*.

    The connection is opened with ``check_same_thread=False``; callers must
    use :func:`write_lock` around any mutating statements.
    """
    key = str(db_path)
    if key not in _CONNECTIONS:
        conn = sqlite3.connect(key, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.commit()
        _CONNECTIONS[key] = conn
    return _CONNECTIONS[key]


@contextmanager
def write_lock() -> object:
    """Context manager that acquires the module-level write lock.

    Example::

        with write_lock():
            conn.execute("INSERT INTO matches ...")
            conn.commit()
    """
    with _WRITE_LOCK:
        yield


def close_connection(db_path: str | Path) -> None:
    """Close and remove the cached connection for *db_path* (useful in tests)."""
    key = str(db_path)
    conn = _CONNECTIONS.pop(key, None)
    if conn is not None:
        conn.close()
