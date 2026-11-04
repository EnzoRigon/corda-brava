"""Consumer loop tests: real SQLite (tmp), in-memory queue, fake clock, no sleeping."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.core.settings import Settings
from app.domain.entities import Player, PullEvent
from app.domain.enums import EndReason, MatchResult, MatchStatus, Team
from app.queue.memory import InMemoryEventQueue
from app.repositories.sqlite.bootstrap import bootstrap_db
from app.repositories.sqlite.connection import close_connection
from app.repositories.sqlite.event_repo import SQLiteEventRepository
from app.repositories.sqlite.match_repo import SQLiteMatchRepository
from app.repositories.sqlite.player_repo import SQLitePlayerRepository
from app.services.consumer import ConsumerLoop
from app.services.match_service import MatchService
from app.services.registry import MatchRegistry

T0 = datetime(2025, 1, 1, tzinfo=UTC)


class Env:
    def __init__(self, tmp_path: Path) -> None:
        self.db = tmp_path / "t.db"
        bootstrap_db(self.db)
        self.now = T0
        self.settings = Settings(
            ROPE_TARGET=5,
            TEAM_BALANCE_MODE="raw",
            TICK_INTERVAL_MS=1,
            MAX_PULLS_PER_PLAYER_PER_S=10**6,
        )
        self.matches = SQLiteMatchRepository(self.db)
        self.players = SQLitePlayerRepository(self.db)
        self.events = SQLiteEventRepository(self.db)
        self.queue = InMemoryEventQueue(lease_timeout_s=0.01)
        self.registry = MatchRegistry()
        self.svc = MatchService(
            matches=self.matches,
            players=self.players,
            events=self.events,
            queue=self.queue,
            registry=self.registry,
            settings=self.settings,
            clock=lambda: self.now,
        )
        self.sent: list[dict] = []
        self.match = self.svc.create_match(duration_s=60)
        self.p = {}
        for team in Team:
            p = Player(
                id=str(uuid.uuid4()),
                match_id=self.match.id,
                device_id=team.value,
                name=team.value,
                team=team,
                token="t",
            )
            self.players.add_player(p)
            self.p[team] = p

    def force_running(self) -> ConsumerLoop:
        """Mark RUNNING in the repo only (no background task); tests drive tick()."""
        m = self.matches.get_match(self.match.id)
        m.status = MatchStatus.RUNNING
        m.started_at, m.ends_at = T0, T0 + timedelta(seconds=60)
        self.matches.update_match(m)

        async def bc(payload: dict) -> None:
            self.sent.append(payload)

        return ConsumerLoop(
            self.match.id,
            matches=self.matches,
            players=self.players,
            events=self.events,
            queue=self.queue,
            settings=self.settings,
            broadcast=bc,
            clock=lambda: self.now,
        )

    async def pull(self, team: Team, count: int, batch_id: str) -> None:
        await self.queue.enqueue(
            PullEvent(
                id=str(uuid.uuid4()),
                match_id=self.match.id,
                player_id=self.p[team].id,
                team=team,
                count=count,
                client_ts=0.0,
                batch_id=batch_id,
            )
        )


@pytest.fixture()
def env(tmp_path: Path):
    e = Env(tmp_path)
    yield e
    close_connection(e.db)


async def test_tick_persists_moves_rope_and_acks(env: Env) -> None:
    loop = env.force_running()
    await env.pull(Team.GREMIO, 3, "b1")
    assert await loop.tick() is False
    assert env.matches.get_match(env.match.id).rope_position == 3
    assert len(env.events.list_events(env.match.id)) == 1
    await asyncio.sleep(0.03)  # past the lease: an acked message must not return
    assert await env.queue.receive_batch(10, 0) == []
    tick = env.sent[-1]
    assert tick["type"] == "tick" and tick["rope"] == 3
    assert tick["delta"] == {"inter": 0, "gremio": 3}
    assert tick["scores"]["gremio"]["pulls"] == 3 and tick["remainingS"] == 60


async def test_per_player_cap_limits_one_tick(env: Env) -> None:
    env.settings.MAX_PULLS_PER_PLAYER_PER_S = 10  # tick 1ms -> floor of 1 pull
    env.settings.TICK_INTERVAL_MS = 500  # cap = 5
    loop = env.force_running()
    await env.pull(Team.INTER, 200, "f1")
    await env.pull(Team.INTER, 200, "f2")  # same player, same tick: shares the cap
    await loop.tick()
    assert env.matches.get_match(env.match.id).rope_position == -5
    assert sum(e.count for e in env.events.list_events(env.match.id)) == 5


async def test_fully_capped_batch_is_acked_but_not_recorded(env: Env) -> None:
    env.settings.MAX_PULLS_PER_PLAYER_PER_S = 10
    env.settings.TICK_INTERVAL_MS = 500  # cap = 5
    loop = env.force_running()
    await env.pull(Team.INTER, 5, "c1")
    await env.pull(Team.INTER, 9, "c2")  # no room left -> count 0
    await loop.tick()
    assert [e.batch_id for e in env.events.list_events(env.match.id)] == ["c1"]
    assert [e["count"] for e in env.sent[0]["events"]] == [
        5
    ]  # sent[0] is the tick (win ends after)
    await asyncio.sleep(0.03)  # past the lease: both must have been acked
    assert await env.queue.receive_batch(10, 0) == []


async def test_duplicate_batch_id_has_no_extra_effect(env: Env) -> None:
    loop = env.force_running()
    await env.pull(Team.GREMIO, 2, "dup")
    await loop.tick()
    await env.pull(Team.GREMIO, 2, "dup")  # redelivery
    await loop.tick()
    assert env.matches.get_match(env.match.id).rope_position == 2
    assert len(env.events.list_events(env.match.id)) == 1


async def test_tick_events_list_names_teams_counts(env: Env) -> None:
    loop = env.force_running()
    await env.pull(Team.GREMIO, 2, "e1")
    await env.pull(Team.INTER, 1, "e2")
    await loop.tick()
    evs = env.sent[-1]["events"]
    assert sorted((e["name"], e["team"], e["count"]) for e in evs) == [
        ("gremio", "gremio", 2),
        ("inter", "inter", 1),
    ]
    assert set(evs[0]) == {"playerId", "name", "team", "count"}
    await env.pull(Team.GREMIO, 2, "e1")  # redelivery: not listed
    await loop.tick()
    assert env.sent[-1]["events"] == []


async def test_tick_events_capped_at_20_most_recent(env: Env) -> None:
    loop = env.force_running()
    for i in range(25):
        await env.pull(Team.INTER if i % 2 else Team.GREMIO, 1, f"c{i}")  # net rope stays < 5
    await loop.tick()
    assert len(env.sent[-1]["events"]) == 20


async def test_win_finishes_and_run_stops(env: Env) -> None:
    loop = env.force_running()
    await env.pull(Team.GREMIO, 5, "w")
    await loop.run()  # returns because the match finished
    m = env.matches.get_match(env.match.id)
    assert (m.status, m.result, m.end_reason) == (
        MatchStatus.FINISHED,
        MatchResult.GREMIO,
        EndReason.WIN,
    )
    assert env.sent[-1]["type"] == "ended" and env.sent[-1]["result"] == "GREMIO"


async def test_timeout_is_draw(env: Env) -> None:
    loop = env.force_running()
    await env.pull(Team.INTER, 1, "x")
    env.now = T0 + timedelta(seconds=61)
    assert await loop.tick() is True
    m = env.matches.get_match(env.match.id)
    assert (m.result, m.end_reason) == (MatchResult.DRAW, EndReason.TIMEOUT)
    assert env.sent[-1]["endReason"] == "timeout"


async def test_unknown_player_is_acked_and_match_keeps_ticking(env: Env) -> None:
    loop = env.force_running()
    await env.queue.enqueue(
        PullEvent(
            id="e",
            match_id=env.match.id,
            player_id="ghost",
            team=Team.INTER,
            count=1,
            client_ts=0.0,
            batch_id="g",
        )
    )
    assert await loop.tick() is False
    await asyncio.sleep(0.03)
    assert await env.queue.receive_batch(10, 0) == []  # acked, not redelivered
    env.now = T0 + timedelta(seconds=61)
    assert await loop.tick() is True


async def test_run_survives_a_failing_tick(env: Env) -> None:
    loop = env.force_running()
    real, calls = loop.tick, []

    async def flaky() -> bool:
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("boom")
        return await real()

    loop.tick = flaky
    env.now = T0 + timedelta(seconds=61)
    await loop.run()
    assert len(calls) == 2
    assert env.matches.get_match(env.match.id).status is MatchStatus.FINISHED


async def test_failed_apply_then_redelivery_applies_once(env: Env, monkeypatch) -> None:
    from app.repositories.sqlite import match_repo

    loop = env.force_running()
    await env.pull(Team.GREMIO, 3, "r1")
    good = match_repo._UPDATE_MATCH
    monkeypatch.setattr(match_repo, "_UPDATE_MATCH", "UPDATE nope SET x=1")
    with pytest.raises(Exception):
        await loop.tick()
    monkeypatch.setattr(match_repo, "_UPDATE_MATCH", good)
    assert env.events.list_events(env.match.id) == []  # rolled back
    await asyncio.sleep(0.03)  # lease expires -> redelivered
    await loop.tick()
    assert env.matches.get_match(env.match.id).rope_position == 3
    assert len(env.events.list_events(env.match.id)) == 1
    assert env.sent[-1]["scores"]["gremio"]["pulls"] == 3


async def test_stale_finished_match_message_is_acked(env: Env) -> None:
    loop = env.force_running()
    other = env.svc.create_match(duration_s=60)
    m = env.matches.get_match(other.id)
    m.status = MatchStatus.FINISHED
    env.matches.update_match(m)
    await env.queue.enqueue(
        PullEvent(
            id="s",
            match_id=other.id,
            player_id="p",
            team=Team.INTER,
            count=1,
            client_ts=0.0,
            batch_id="stale",
        )
    )
    await loop.tick()
    await asyncio.sleep(0.03)
    assert await env.queue.receive_batch(10, 0) == []
