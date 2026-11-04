"""Player public + join API tests (TestClient, temp SQLite)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_container
from app.core.app_factory import create_app
from app.core.settings import Settings
from app.domain.enums import MatchStatus
from app.repositories.sqlite.connection import close_connection
from app.services.player_session import verify_player_token


@pytest.fixture()
def ctx(tmp_path: Path):
    db = tmp_path / "t.db"
    settings = Settings(DATABASE_URL=f"sqlite:///{db.as_posix()}", SECRET_KEY="s" * 32)
    app = create_app(settings)
    client = TestClient(app)
    container = get_container(app)
    match = container.service.create_match(duration_s=60)
    yield client, container, settings, match
    close_connection(db)


def _join(client, mid, device="d1", name="Ana", team="inter"):
    return client.post(
        f"/api/matches/{mid}/players", json={"name": name, "team": team, "deviceId": device}
    )


def test_join_returns_player_and_valid_token(ctx) -> None:
    client, _, settings, match = ctx
    r = _join(client, match.id)
    assert r.status_code == 200
    body = r.json()
    assert body["team"] == "inter"
    claims = verify_player_token(body["playerToken"], settings)
    assert claims == {
        "match_id": match.id,
        "player_id": body["playerId"],
        "device_id": "d1",
    }


def test_rejoin_same_device_is_idempotent(ctx) -> None:
    client, container, _, match = ctx
    a = _join(client, match.id).json()
    b = _join(client, match.id, name="Outro", team="gremio").json()
    assert a["playerId"] == b["playerId"] and b["team"] == "inter"
    assert len(container.players.list_players(match.id)) == 1


def test_invalid_team_rejected(ctx) -> None:
    client, _, _, match = ctx
    assert _join(client, match.id, team="flamengo").status_code in (400, 422)


@pytest.mark.parametrize("name", ["", "   "])
def test_empty_name_rejected(ctx, name) -> None:
    client, _, _, match = ctx
    assert _join(client, match.id, name=name).status_code in (400, 422)


def test_long_name_rejected(ctx) -> None:
    client, _, _, match = ctx
    assert _join(client, match.id, name="x" * 200).status_code in (400, 422)


def test_name_is_trimmed(ctx) -> None:
    client, container, _, match = ctx
    _join(client, match.id, name="  Ana  ")
    assert container.players.list_players(match.id)[0].name == "Ana"


def test_late_join_blocked_when_running(ctx) -> None:
    client, container, _, match = ctx
    m = container.matches.get_match(match.id)
    m.status = MatchStatus.RUNNING
    container.matches.update_match(m)
    r = _join(client, match.id, device="late")
    assert r.status_code == 409 and r.json()["detail"] == "A partida já começou"


def test_existing_player_can_rejoin_while_running(ctx) -> None:
    client, container, _, match = ctx
    first = _join(client, match.id).json()
    m = container.matches.get_match(match.id)
    m.status = MatchStatus.RUNNING
    container.matches.update_match(m)
    assert _join(client, match.id).json()["playerId"] == first["playerId"]


def test_public_shows_counts(ctx) -> None:
    client, _, _, match = ctx
    _join(client, match.id, device="a", team="inter")
    _join(client, match.id, device="b", team="inter")
    _join(client, match.id, device="c", team="gremio")
    body = client.get(f"/api/matches/{match.id}/public").json()
    assert body["status"] == "LOBBY" and body["durationS"] == 60
    assert body["counts"] == {"inter": 2, "gremio": 1}
    assert body["teams"]["inter"] == {
        "name": "Inter",
        "colors": {"primary": "#E5050F", "secondary": "#FFFFFF"},
    }


def test_unknown_match_404(ctx) -> None:
    client, *_ = ctx
    assert client.get("/api/matches/NOPE/public").status_code == 404
    assert _join(client, "NOPE").status_code == 404


def test_verify_player_token_rejects_garbage_and_wrong_role(ctx) -> None:
    import jwt

    _, _, settings, _ = ctx
    assert verify_player_token("garbage", settings) is None
    host = jwt.encode({"role": "host"}, settings.SECRET_KEY, algorithm="HS256")
    assert verify_player_token(host, settings) is None
