"""Pull ingest + /me tests. Status is set via the repo so no consumer drains the queue."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_container
from app.core.app_factory import create_app
from app.core.settings import Settings
from app.domain.enums import EndReason, MatchResult, MatchStatus
from app.repositories.sqlite.connection import close_connection


@pytest.fixture()
def ctx(tmp_path: Path):
    db = tmp_path / "t.db"
    settings = Settings(DATABASE_URL=f"sqlite:///{db.as_posix()}", SECRET_KEY="s" * 32)
    app = create_app(settings)
    client = TestClient(app)
    c = get_container(app)
    match = c.service.create_match(duration_s=60)
    j = client.post(
        f"/api/matches/{match.id}/players",
        json={"name": "Ana", "team": "gremio", "deviceId": "d1"},
    ).json()
    yield client, c, match.id, j
    close_connection(db)


def _set(c, mid, status, result=None):
    m = c.matches.get_match(mid)
    m.status = status
    if result:
        m.result, m.end_reason = result, EndReason.TIMEOUT
    c.matches.update_match(m)


def _pull(client, mid, j, **over):
    body = {
        "playerId": j["playerId"],
        "playerToken": j["playerToken"],
        "count": 5,
        "clientTs": 1.0,
        "batchId": "b1",
    } | over
    return client.post(f"/api/matches/{mid}/pulls", json=body)


async def _drain(c):
    return await c.queue.receive_batch(100, 0)


@pytest.mark.asyncio
async def test_pull_running_enqueues_one(ctx) -> None:
    client, c, mid, j = ctx
    _set(c, mid, MatchStatus.RUNNING)
    assert _pull(client, mid, j).status_code == 202
    msgs = await _drain(c)
    assert len(msgs) == 1
    ev = msgs[0].payload
    assert (ev.match_id, ev.player_id, ev.team.value, ev.count, ev.batch_id) == (
        mid,
        j["playerId"],
        "gremio",
        5,
        "b1",
    )


@pytest.mark.asyncio
async def test_same_batch_not_requeued(ctx) -> None:
    client, c, mid, j = ctx
    _set(c, mid, MatchStatus.RUNNING)
    assert _pull(client, mid, j).status_code == 202
    assert _pull(client, mid, j).status_code == 202
    assert len(await _drain(c)) == 1


@pytest.mark.asyncio
async def test_count_clamped(ctx) -> None:
    client, c, mid, j = ctx
    _set(c, mid, MatchStatus.RUNNING)
    assert _pull(client, mid, j, count=10_000).status_code == 202
    assert (await _drain(c))[0].payload.count == c.settings.MAX_PULLS_PER_BATCH


def test_bad_count_422(ctx) -> None:
    client, c, mid, j = ctx
    _set(c, mid, MatchStatus.RUNNING)
    assert _pull(client, mid, j, count=0).status_code == 422


@pytest.mark.parametrize("status", [MatchStatus.LOBBY, MatchStatus.FINISHED])
def test_pull_not_running_409(ctx, status) -> None:
    client, c, mid, j = ctx
    _set(c, mid, status, MatchResult.DRAW if status is MatchStatus.FINISHED else None)
    r = _pull(client, mid, j)
    assert r.status_code == 409 and "partida" in r.json()["detail"]


def test_bad_token_401_and_mismatch_403(ctx) -> None:
    client, c, mid, j = ctx
    _set(c, mid, MatchStatus.RUNNING)
    assert _pull(client, mid, j, playerToken="junk").status_code == 401
    assert _pull(client, mid, j, playerId="someone-else").status_code == 403
    other = c.service.create_match(duration_s=60)
    assert _pull(client, other.id, j).status_code == 403


def test_me_screens(ctx) -> None:
    client, c, mid, j = ctx
    q = {"playerId": j["playerId"], "token": j["playerToken"]}
    get = lambda: client.get(f"/api/matches/{mid}/me", params=q)  # noqa: E731
    assert get().json() == {"screen": "wait", "team": "gremio", "matchStatus": "LOBBY"}
    _set(c, mid, MatchStatus.RUNNING)
    assert get().json()["screen"] == "play"
    _set(c, mid, MatchStatus.FINISHED, MatchResult.GREMIO)
    assert get().json() == {
        "screen": "end",
        "team": "gremio",
        "matchStatus": "FINISHED",
        "result": "GREMIO",
    }


def test_me_bad_token_401(ctx) -> None:
    client, _, mid, j = ctx
    r = client.get(f"/api/matches/{mid}/me", params={"playerId": j["playerId"], "token": "x"})
    assert r.status_code == 401
