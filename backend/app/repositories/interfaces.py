"""Repository interface definitions for Corda Brava.

All protocols expose domain models (Match, Player, PullEvent) only.
No SQLite types (sqlite3.Row, sqlite3.Cursor, etc.) ever cross this boundary.

UniqueConstraintError is raised by SQLite implementations when an INSERT
violates a UNIQUE constraint, so callers never need to import sqlite3.
"""

from __future__ import annotations

from typing import Protocol

from app.domain.entities import Match, Player, PullEvent


class UniqueConstraintError(Exception):
    """Raised when a repository INSERT would violate a UNIQUE constraint.

    Wraps the underlying sqlite3.IntegrityError so callers do not need
    to import sqlite3 directly.  The original error is stored in __cause__.
    """


class MatchRepository(Protocol):
    """Persistence interface for Match entities.

    Implementations must guarantee:
    - create_match stores a new Match and returns it unchanged.
    - get_match returns None if the id is unknown.
    - update_match overwrites all mutable fields and returns the saved model.
    """

    def create_match(self, match: Match) -> Match:
        """Persist a new Match and return the stored model."""
        ...

    def get_match(self, match_id: str) -> Match | None:
        """Return the Match with the given id, or None if not found."""
        ...

    def update_match(self, match: Match) -> Match:
        """Overwrite all fields of an existing Match and return it."""
        ...


class PlayerRepository(Protocol):
    """Persistence interface for Player entities.

    add_player behaviour on duplicate (match_id, device_id):
        Raises UniqueConstraintError.  The service layer (Task 8) implements
        idempotent-rejoin by calling get_player_by_device first.
    """

    def add_player(self, player: Player) -> Player:
        """Persist a new Player and return the stored model.

        Raises:
            UniqueConstraintError: if (match_id, device_id) already exists.
        """
        ...

    def get_player(self, player_id: str) -> Player | None:
        """Return the Player with the given id, or None if not found."""
        ...

    def get_player_by_device(self, match_id: str, device_id: str) -> Player | None:
        """Return the Player for (match_id, device_id), or None."""
        ...

    def list_players(self, match_id: str) -> list[Player]:
        """Return all Players for the given match, unordered."""
        ...


class EventRepository(Protocol):
    """Persistence interface for PullEvent entities.

    add_event behaviour on duplicate (match_id, batch_id):
        Uses INSERT OR IGNORE — the row is silently skipped.  Callers should
        call event_exists() first when they need to detect deduplication.
        This keeps the ingest hot-path lock-free from the caller's perspective.
    """

    def add_event(self, event: PullEvent) -> None:
        """Persist a PullEvent.

        If (match_id, batch_id) already exists the INSERT is silently ignored
        (INSERT OR IGNORE semantics).  Use event_exists() to check.
        """
        ...

    def event_exists(self, match_id: str, batch_id: str) -> bool:
        """Return True if (match_id, batch_id) is already stored."""
        ...

    def list_events(self, match_id: str) -> list[PullEvent]:
        """Return all PullEvents for the match, ordered by server_ts ascending."""
        ...
