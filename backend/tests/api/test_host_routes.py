"""Host HTTP route tests (TestClient as context manager so the app lifespan + loop run)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

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
        PUBLIC_BASE_URL="http://lan:5173/",
    )
    with TestClient(create_app(settings)) as c:
        yield c
    close_connection(db)


@pytest.fixture()
def auth(client):
    tok = client.post("/api/host/login", json={"password": PASSWORD}).json()["token"]
    return {"Authorization": f"Bearer {tok}"}


def _create(client, auth, **body):
    return client.post("/api/host/matches", json=body, headers=auth)


def test_login_wrong_password_401_ptbr(client) -> None:
    r = client.post("/api/host/login", json={"password": "nope"})
    assert r.status_code == 401 and r.json()["detail"] == "Senha incorreta"


def test_login_rate_limited_after_failures(client) -> None:
    for _ in range(5):
        assert client.post("/api/host/login", json={"password": "x"}).status_code == 401
    r = client.post("/api/host/login", json={"password": PASSWORD})
    assert r.status_code == 429 and "tentativas" in r.json()["detail"]


def test_login_window_expires(client, monkeypatch) -> None:
    import app.api.host as host

    for _ in range(5):
        client.post("/api/host/login", json={"password": "x"})
    monkeypatch.setattr(host, "LOGIN_WINDOW_S", 0.0)
    assert client.post("/api/host/login", json={"password": PASSWORD}).status_code == 200


def test_login_returns_token_and_expiry(client) -> None:
    r = client.post("/api/host/login", json={"password": PASSWORD})
    assert r.status_code == 200 and r.json()["token"] and r.json()["expiresAt"]


@pytest.mark.parametrize(
    "method,path",
    [
        ("post", "/api/host/matches"),
        ("get", "/api/host/matches/X"),
        ("patch", "/api/host/matches/X"),
        ("post", "/api/host/matches/X/start"),
        ("post", "/api/host/matches/X/reset"),
        ("post", "/api/host/matches/X/cancel"),
        ("get", "/api/host/matches/X/analytics"),
    ],
)
def test_unauthenticated_is_401(client, method, path) -> None:
    kwargs = {} if method == "get" else {"json": {}}
    assert getattr(client, method)(path, **kwargs).status_code == 401


def test_create_match(client, auth) -> None:
    r = _create(client, auth, durationS=45, balanceMode="raw")
    assert r.status_code == 201
    b = r.json()
    assert b["joinUrl"] == f"http://lan:5173/j/{b['matchId']}" == b["qrPayload"]
    assert b["config"]["durationS"] == 45 and b["config"]["balanceMode"] == "raw"
    assert b["config"]["teams"]["inter"]["name"] == "Inter"


def test_create_match_out_of_range_422(client, auth) -> None:
    assert _create(client, auth, durationS=99999).status_code == 422


def test_get_match_view(client, auth) -> None:
    mid = _create(client, auth).json()["matchId"]
    b = client.get(f"/api/host/matches/{mid}", headers=auth).json()
    assert b["status"] == "LOBBY" and b["rope"] == 0 and b["result"] is None
    assert b["roster"] == {"inter": [], "gremio": []}
    assert b["joinUrl"] == f"http://lan:5173/j/{mid}"
    assert client.get("/api/host/matches/NOPE", headers=auth).status_code == 404


def test_patch_duration(client, auth) -> None:
    mid = _create(client, auth).json()["matchId"]
    url = f"/api/host/matches/{mid}"
    r = client.patch(url, json={"durationS": 50}, headers=auth)
    assert r.status_code == 200 and r.json()["durationS"] == 50
    assert client.patch(url, json={"durationS": 9999}, headers=auth).status_code == 422


def test_start_then_patch_409(client, auth) -> None:
    mid = _create(client, auth, durationS=30).json()["matchId"]
    r = client.post(f"/api/host/matches/{mid}/start", headers=auth)
    assert r.status_code == 200 and r.json()["status"] == "RUNNING"
    r = client.patch(f"/api/host/matches/{mid}", json={"durationS": 40}, headers=auth)
    assert r.status_code == 409
    assert client.post(f"/api/host/matches/{mid}/start", headers=auth).status_code == 409


def test_cancel_finishes_match(client, auth) -> None:
    mid = _create(client, auth, durationS=30).json()["matchId"]
    client.post(f"/api/host/matches/{mid}/start", headers=auth)
    r = client.post(f"/api/host/matches/{mid}/cancel", headers=auth)
    assert r.status_code == 200 and r.json()["status"] == "FINISHED" and r.json()["result"] is None


def test_reset_returns_new_lobby_match(client, auth) -> None:
    mid = _create(client, auth, durationS=40, balanceMode="raw").json()["matchId"]
    client.post(f"/api/host/matches/{mid}/start", headers=auth)
    r = client.post(f"/api/host/matches/{mid}/reset", headers=auth)
    assert r.status_code == 201
    new = r.json()
    assert new["matchId"] != mid and new["config"]["durationS"] == 40
    assert new["config"]["balanceMode"] == "raw" and new["joinUrl"].endswith(new["matchId"])
    view = client.get(f"/api/host/matches/{new['matchId']}", headers=auth)
    assert view.json()["status"] == "LOBBY"
    assert client.get(f"/api/host/matches/{mid}", headers=auth).json()["status"] == "FINISHED"


def test_analytics_after_finish(client, auth) -> None:
    mid = _create(client, auth, durationS=30).json()["matchId"]
    assert client.get(f"/api/host/matches/{mid}/analytics", headers=auth).status_code == 409
    client.post(f"/api/host/matches/{mid}/start", headers=auth)
    client.post(f"/api/host/matches/{mid}/cancel", headers=auth)
    r = client.get(f"/api/host/matches/{mid}/analytics", headers=auth)
    assert r.status_code == 200
    assert r.json()["totalPlayers"] == 0 and r.json()["result"] is None
