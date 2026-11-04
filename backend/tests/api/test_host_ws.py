"""Host WebSocket tests. Every receive is bounded: the 1 s match timer always ends the match."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.app_factory import create_app
from app.core.settings import Settings
from app.repositories.sqlite.connection import close_connection

PASSWORD = "pw-test"


@pytest.fixture()
def client(tmp_path: Path):
    db = tmp_path / "t.db"
    settings = Settings(
        DATABASE_URL=f"sqlite:///{db.as_posix()}",
        SECRET_KEY="s" * 32,
        HOST_PASSWORD=PASSWORD,
        TICK_INTERVAL_MS=20,
        MATCH_DURATION_MIN_S=1,
    )
    with TestClient(create_app(settings)) as c:
        yield c
    close_connection(db)


@pytest.fixture()
def host(client):
    tok = client.post("/api/host/login", json={"password": PASSWORD}).json()["token"]
    h = {"Authorization": f"Bearer {tok}"}
    mid = client.post("/api/host/matches", json={"durationS": 1}, headers=h).json()["matchId"]
    return h, tok, mid


def _url(mid, tok=None):
    return f"/api/host/matches/{mid}/ws" + (f"?token={tok}" if tok else "")


def _join(client, mid, device="d1", name="Ana", team="inter"):
    return client.post(
        f"/api/matches/{mid}/players", json={"name": name, "team": team, "deviceId": device}
    )


def test_ws_without_token_closed_1008(client, host) -> None:
    _, _, mid = host
    with client.websocket_connect(_url(mid)) as ws, pytest.raises(WebSocketDisconnect) as e:
        ws.receive_json()
    assert e.value.code == 1008


def test_ws_bad_token_closed_1008(client, host) -> None:
    _, _, mid = host
    with client.websocket_connect(_url(mid, "garbage")) as ws:
        with pytest.raises(WebSocketDisconnect) as e:
            ws.receive_json()
    assert e.value.code == 1008


def test_ws_first_message_is_snapshot(client, host) -> None:
    _, tok, mid = host
    _join(client, mid, name="Ana")
    with client.websocket_connect(_url(mid, tok)) as ws:
        msg = ws.receive_json()
    m = msg["match"]
    assert msg["type"] == "snapshot" and m["id"] == mid and m["status"] == "LOBBY"
    assert m["config"]["durationS"] == 1 and m["rope"] == 0 and m["remainingS"] == 1
    assert [p["name"] for p in m["roster"]["inter"]] == ["Ana"] and m["roster"]["gremio"] == []
    assert m["scores"] == {"inter": {"pulls": 0}, "gremio": {"pulls": 0}}
    assert m["result"] is None and m["endReason"] is None


def test_player_joined_pushed_once(client, host) -> None:
    _, tok, mid = host
    with client.websocket_connect(_url(mid, tok)) as ws:
        ws.receive_json()
        r = _join(client, mid, name="Bia", team="gremio")
        _join(client, mid, name="Bia", team="gremio")  # idempotent re-join: no second event
        _join(client, mid, device="d2", name="Caio", team="inter")
        assert ws.receive_json() == {
            "type": "player_joined",
            "team": "GREMIO",
            "player": {"id": r.json()["playerId"], "name": "Bia"},
        }
        assert ws.receive_json()["player"]["name"] == "Caio"


def test_tick_then_ended_with_analytics(client, host) -> None:
    h, tok, mid = host
    j = _join(client, mid).json()
    with client.websocket_connect(_url(mid, tok)) as ws:
        ws.receive_json()
        client.post(f"/api/host/matches/{mid}/start", headers=h)
        body = {
            "playerId": j["playerId"],
            "playerToken": j["playerToken"],
            "count": 3,
            "clientTs": 1.0,
            "batchId": "b1",
        }
        client.post(f"/api/matches/{mid}/pulls", json=body)
        ticks, ended = [], None
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            msg = ws.receive_json()
            if msg["type"] == "tick":
                ticks.append(msg)
            elif msg["type"] == "ended":
                ended = msg
                break
    assert ticks and set(ticks[0]) == {"type", "rope", "remainingS", "delta", "scores"}
    assert ended["result"] in {"INTER", "GREMIO", "DRAW"}
    assert ended["endReason"] in {"win", "timeout"}
    assert ended["analytics"]["totalPulls"]["inter"] == 3
    assert ended["analytics"]["result"] == ended["result"]  # same casing everywhere


def test_reset_notifies_ws(client, host) -> None:
    h, tok, mid = host
    with client.websocket_connect(_url(mid, tok)) as ws:
        ws.receive_json()
        new = client.post(f"/api/host/matches/{mid}/reset", headers=h).json()["matchId"]
        assert ws.receive_json() == {"type": "reset", "newMatchId": new}


def test_cancel_notifies_ws(client, host) -> None:
    h, tok, mid = host
    with client.websocket_connect(_url(mid, tok)) as ws:
        ws.receive_json()
        client.post(f"/api/host/matches/{mid}/cancel", headers=h)
        assert ws.receive_json() == {"type": "cancelled"}
