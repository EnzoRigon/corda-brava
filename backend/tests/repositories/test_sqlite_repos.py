"""Tests for SQLite repository implementations.

All tests use a tmp_path SQLite file (pytest fixture) so they are isolated
and do not touch the project's corda_brava.db.

Key assertions:
- Match round-trips (all fields, nested MatchConfig/TeamConfig, enums, tz-aware datetimes).
- update_match persists mutable fields.
- Player UNIQUE (match_id, device_id) raises UniqueConstraintError (not sqlite3.IntegrityError).
- PullEvent dedup: INSERT OR IGNORE keeps list_events length at 1.
- list_events ordered by server_ts ascending.
- All returned objects are domain model instances (no sqlite3.Row leakage).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.domain.entities import Match, MatchConfig, Player, PullEvent, TeamConfig
from app.domain.enums import BalanceMode, EndReason, MatchResult, MatchStatus, Team
from app.repositories.interfaces import UniqueConstraintError
from app.repositories.sqlite.bootstrap import bootstrap_db
from app.repositories.sqlite.connection import close_connection
from app.repositories.sqlite.event_repo import SQLiteEventRepository
from app.repositories.sqlite.match_repo import SQLiteMatchRepository
from app.repositories.sqlite.player_repo import SQLitePlayerRepository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_match(match_id: str = "ABC123") -> Match:
    inter = TeamConfig(
        id="inter",
        name="Inter",
        primary_color="#E5050F",
        secondary_color="#FFFFFF",
    )
    gremio = TeamConfig(
        id="gremio",
        name="Grêmio",
        primary_color="#0057A6",
        secondary_color="#000000",
    )
    config = MatchConfig(
        duration_s=120,
        rope_target=5,
        balance_mode=BalanceMode.NORMALIZED,
        inter=inter,
        gremio=gremio,
    )
    return Match(
        id=match_id,
        created_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC),
        config=config,
    )


def _make_player(match_id: str, device_id: str = "dev-001", pid: str | None = None) -> Player:
    return Player(
        id=pid or str(uuid.uuid4()),
        match_id=match_id,
        device_id=device_id,
        name="Alice",
        team=Team.INTER,
        token=str(uuid.uuid4()),
        joined_at=datetime(2024, 6, 1, 12, 1, 0, tzinfo=UTC),
    )


def _make_event(
    match_id: str,
    player_id: str,
    batch_id: str = "batch-001",
    ts_offset: float = 0.0,
) -> PullEvent:
    return PullEvent(
        id=str(uuid.uuid4()),
        match_id=match_id,
        player_id=player_id,
        team=Team.INTER,
        count=3,
        client_ts=1717236000.0 + ts_offset,
        server_ts=datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC) + timedelta(seconds=ts_offset),
        batch_id=batch_id,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    bootstrap_db(path)
    yield path
    close_connection(path)


@pytest.fixture()
def match_repo(db_path: Path) -> SQLiteMatchRepository:
    return SQLiteMatchRepository(db_path)


@pytest.fixture()
def player_repo(db_path: Path) -> SQLitePlayerRepository:
    return SQLitePlayerRepository(db_path)


@pytest.fixture()
def event_repo(db_path: Path) -> SQLiteEventRepository:
    return SQLiteEventRepository(db_path)


# ---------------------------------------------------------------------------
# Match tests
# ---------------------------------------------------------------------------


class TestMatchRepository:
    def test_create_and_get_round_trip(self, match_repo: SQLiteMatchRepository) -> None:
        """create_match → get_match returns an equal Match domain model."""
        original = _make_match()
        match_repo.create_match(original)

        retrieved = match_repo.get_match(original.id)

        assert retrieved is not None
        assert isinstance(retrieved, Match)
        # Top-level fields
        assert retrieved.id == original.id
        assert retrieved.status == MatchStatus.LOBBY
        assert retrieved.rope_position == 0.0
        assert retrieved.started_at is None
        assert retrieved.ends_at is None
        assert retrieved.result is None
        assert retrieved.end_reason is None
        # datetime round-trip: tz-aware
        assert retrieved.created_at.tzinfo is not None
        assert retrieved.created_at == original.created_at
        # Config round-trip
        assert retrieved.config.duration_s == 120
        assert retrieved.config.rope_target == 5
        assert retrieved.config.balance_mode == BalanceMode.NORMALIZED
        assert retrieved.config.inter.id == "inter"
        assert retrieved.config.inter.name == "Inter"
        assert retrieved.config.inter.primary_color == "#E5050F"
        assert retrieved.config.gremio.primary_color == "#0057A6"

    def test_get_match_unknown_returns_none(self, match_repo: SQLiteMatchRepository) -> None:
        assert match_repo.get_match("NOPE") is None

    def test_update_match_persists_runtime_fields(self, match_repo: SQLiteMatchRepository) -> None:
        """update_match persists rope_position, status, result, started_at."""
        match = _make_match()
        match_repo.create_match(match)

        updated = match.model_copy(
            update={
                "status": MatchStatus.RUNNING,
                "rope_position": 2.5,
                "started_at": datetime(2024, 6, 1, 12, 5, 0, tzinfo=UTC),
                "ends_at": datetime(2024, 6, 1, 12, 7, 0, tzinfo=UTC),
            }
        )
        match_repo.update_match(updated)

        retrieved = match_repo.get_match(match.id)
        assert retrieved is not None
        assert retrieved.status == MatchStatus.RUNNING
        assert retrieved.rope_position == 2.5
        assert retrieved.started_at is not None
        assert retrieved.started_at.tzinfo is not None
        assert retrieved.started_at == datetime(2024, 6, 1, 12, 5, 0, tzinfo=UTC)
        assert retrieved.ends_at == datetime(2024, 6, 1, 12, 7, 0, tzinfo=UTC)

    def test_update_match_result_and_end_reason(self, match_repo: SQLiteMatchRepository) -> None:
        match = _make_match()
        match_repo.create_match(match)

        finished = match.model_copy(
            update={
                "status": MatchStatus.FINISHED,
                "result": MatchResult.INTER,
                "end_reason": EndReason.WIN,
            }
        )
        match_repo.update_match(finished)

        retrieved = match_repo.get_match(match.id)
        assert retrieved is not None
        assert retrieved.result == MatchResult.INTER
        assert retrieved.end_reason == EndReason.WIN

    def test_returned_object_is_domain_model(self, match_repo: SQLiteMatchRepository) -> None:
        """No sqlite3.Row leaks: returned type is Match."""
        match = _make_match()
        match_repo.create_match(match)
        retrieved = match_repo.get_match(match.id)
        assert isinstance(retrieved, Match)


# ---------------------------------------------------------------------------
# Player tests
# ---------------------------------------------------------------------------


class TestPlayerRepository:
    def test_add_and_get_player(
        self,
        match_repo: SQLiteMatchRepository,
        player_repo: SQLitePlayerRepository,
    ) -> None:
        """add_player then get_player returns an equal Player domain model."""
        match = _make_match()
        match_repo.create_match(match)
        player = _make_player(match.id)
        player_repo.add_player(player)

        retrieved = player_repo.get_player(player.id)
        assert retrieved is not None
        assert isinstance(retrieved, Player)
        assert retrieved.id == player.id
        assert retrieved.match_id == player.match_id
        assert retrieved.device_id == player.device_id
        assert retrieved.team == Team.INTER
        assert retrieved.token == player.token
        assert retrieved.joined_at.tzinfo is not None
        assert retrieved.joined_at == player.joined_at

    def test_get_player_by_device(
        self,
        match_repo: SQLiteMatchRepository,
        player_repo: SQLitePlayerRepository,
    ) -> None:
        match = _make_match()
        match_repo.create_match(match)
        player = _make_player(match.id, device_id="dev-XYZ")
        player_repo.add_player(player)

        found = player_repo.get_player_by_device(match.id, "dev-XYZ")
        assert found is not None
        assert found.id == player.id

        not_found = player_repo.get_player_by_device(match.id, "unknown")
        assert not_found is None

    def test_list_players_returns_all_for_match(
        self,
        match_repo: SQLiteMatchRepository,
        player_repo: SQLitePlayerRepository,
    ) -> None:
        match = _make_match()
        match_repo.create_match(match)
        p1 = _make_player(match.id, device_id="dev-1", pid="pid-1")
        p2 = _make_player(match.id, device_id="dev-2", pid="pid-2")
        player_repo.add_player(p1)
        player_repo.add_player(p2)

        players = player_repo.list_players(match.id)
        assert len(players) == 2
        ids = {p.id for p in players}
        assert ids == {"pid-1", "pid-2"}

    def test_add_player_duplicate_device_raises_unique_constraint_error(
        self,
        match_repo: SQLiteMatchRepository,
        player_repo: SQLitePlayerRepository,
    ) -> None:
        """Second add_player with same (match_id, device_id) raises UniqueConstraintError."""
        match = _make_match()
        match_repo.create_match(match)
        p1 = _make_player(match.id, device_id="dev-dup", pid="pid-a")
        p2 = _make_player(match.id, device_id="dev-dup", pid="pid-b")
        player_repo.add_player(p1)

        with pytest.raises(UniqueConstraintError):
            player_repo.add_player(p2)

    def test_unique_constraint_error_is_not_sqlite_error(
        self,
        match_repo: SQLiteMatchRepository,
        player_repo: SQLitePlayerRepository,
    ) -> None:
        """UniqueConstraintError is NOT sqlite3.IntegrityError."""
        import sqlite3

        match = _make_match()
        match_repo.create_match(match)
        p1 = _make_player(match.id, device_id="dev-leak", pid="pid-x")
        p2 = _make_player(match.id, device_id="dev-leak", pid="pid-y")
        player_repo.add_player(p1)

        with pytest.raises(UniqueConstraintError):
            player_repo.add_player(p2)

        # Must NOT be the raw sqlite3 type leaking through
        try:
            player_repo.add_player(p2)
        except UniqueConstraintError:
            pass
        except sqlite3.IntegrityError:
            pytest.fail("sqlite3.IntegrityError leaked past the repository boundary")

    def test_returned_object_is_domain_model(
        self,
        match_repo: SQLiteMatchRepository,
        player_repo: SQLitePlayerRepository,
    ) -> None:
        match = _make_match()
        match_repo.create_match(match)
        player = _make_player(match.id)
        player_repo.add_player(player)
        retrieved = player_repo.get_player(player.id)
        assert isinstance(retrieved, Player)


# ---------------------------------------------------------------------------
# Event tests
# ---------------------------------------------------------------------------


class TestEventRepository:
    def _setup_match_and_player(
        self,
        match_repo: SQLiteMatchRepository,
        player_repo: SQLitePlayerRepository,
    ) -> tuple[Match, Player]:
        match = _make_match()
        match_repo.create_match(match)
        player = _make_player(match.id)
        player_repo.add_player(player)
        return match, player

    def test_add_event_then_event_exists_true(
        self,
        match_repo: SQLiteMatchRepository,
        player_repo: SQLitePlayerRepository,
        event_repo: SQLiteEventRepository,
    ) -> None:
        match, player = self._setup_match_and_player(match_repo, player_repo)
        event = _make_event(match.id, player.id, batch_id="b-001")
        event_repo.add_event(event)

        assert event_repo.event_exists(match.id, "b-001") is True

    def test_event_exists_false_for_unknown_batch(
        self,
        match_repo: SQLiteMatchRepository,
        player_repo: SQLitePlayerRepository,
        event_repo: SQLiteEventRepository,
    ) -> None:
        match, player = self._setup_match_and_player(match_repo, player_repo)
        assert event_repo.event_exists(match.id, "no-such-batch") is False

    def test_add_event_duplicate_does_not_create_second_row(
        self,
        match_repo: SQLiteMatchRepository,
        player_repo: SQLitePlayerRepository,
        event_repo: SQLiteEventRepository,
    ) -> None:
        """INSERT OR IGNORE: second add with same batch_id keeps list length at 1."""
        match, player = self._setup_match_and_player(match_repo, player_repo)
        event = _make_event(match.id, player.id, batch_id="b-dup")
        event_repo.add_event(event)
        event_repo.add_event(event)  # second call — must not raise or duplicate

        events = event_repo.list_events(match.id)
        assert len(events) == 1

    def test_list_events_ordered_by_server_ts(
        self,
        match_repo: SQLiteMatchRepository,
        player_repo: SQLitePlayerRepository,
        event_repo: SQLiteEventRepository,
    ) -> None:
        match, player = self._setup_match_and_player(match_repo, player_repo)
        e1 = _make_event(match.id, player.id, batch_id="b-1", ts_offset=10.0)
        e2 = _make_event(match.id, player.id, batch_id="b-2", ts_offset=0.0)
        e3 = _make_event(match.id, player.id, batch_id="b-3", ts_offset=5.0)
        event_repo.add_event(e1)
        event_repo.add_event(e2)
        event_repo.add_event(e3)

        events = event_repo.list_events(match.id)
        assert len(events) == 3
        # sorted by server_ts ascending
        assert events[0].batch_id == "b-2"
        assert events[1].batch_id == "b-3"
        assert events[2].batch_id == "b-1"

    def test_returned_objects_are_domain_models(
        self,
        match_repo: SQLiteMatchRepository,
        player_repo: SQLitePlayerRepository,
        event_repo: SQLiteEventRepository,
    ) -> None:
        match, player = self._setup_match_and_player(match_repo, player_repo)
        event = _make_event(match.id, player.id)
        event_repo.add_event(event)
        events = event_repo.list_events(match.id)
        assert all(isinstance(e, PullEvent) for e in events)

    def test_server_ts_round_trips_as_timezone_aware_datetime(
        self,
        match_repo: SQLiteMatchRepository,
        player_repo: SQLitePlayerRepository,
        event_repo: SQLiteEventRepository,
    ) -> None:
        match, player = self._setup_match_and_player(match_repo, player_repo)
        original_ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)
        event = _make_event(match.id, player.id, batch_id="b-ts")
        # override server_ts
        event = event.model_copy(update={"server_ts": original_ts})
        event_repo.add_event(event)

        events = event_repo.list_events(match.id)
        assert events[0].server_ts.tzinfo is not None
        assert events[0].server_ts == original_ts
