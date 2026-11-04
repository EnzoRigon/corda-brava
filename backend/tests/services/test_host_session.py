"""Tests for host password check, JWT issue/verify and the require_host dependency."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import jwt
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.auth import require_host, verify_ws_token
from app.api.deps import container_dep
from app.core.settings import Settings
from app.services.host_session import check_password, issue_host_token, verify_host_token

S = Settings(HOST_PASSWORD="Pässwörd", SECRET_KEY="k" * 32, HOST_TOKEN_TTL_SECONDS=60)


def test_check_password():
    assert check_password("Pässwörd", S)
    assert not check_password("wrong", S)
    assert not check_password("", S)


def test_issue_and_verify():
    token, exp = issue_host_token(S)
    assert verify_host_token(token, S)
    assert exp > datetime.now(UTC)


def test_tampered_and_garbage():
    token, _ = issue_host_token(S)
    assert not verify_host_token(token[:-2] + "xx", S)
    assert not verify_host_token("garbage", S)
    assert not verify_host_token("", S)
    other = Settings(SECRET_KEY="z" * 32)
    assert not verify_host_token(token, other)


def test_expired():
    expired = Settings(SECRET_KEY=S.SECRET_KEY, HOST_TOKEN_TTL_SECONDS=-5)
    token, _ = issue_host_token(expired)
    assert not verify_host_token(token, expired)


def test_wrong_role():
    exp = int(datetime.now(UTC).timestamp()) + 60
    token = jwt.encode({"role": "player", "exp": exp}, S.SECRET_KEY, algorithm="HS256")
    assert not verify_host_token(token, S)


def test_token_without_exp_rejected():
    token = jwt.encode({"role": "host"}, S.SECRET_KEY, algorithm="HS256")
    assert not verify_host_token(token, S)


def test_other_algorithms_rejected():
    claims = {"role": "host", "exp": int(datetime.now(UTC).timestamp()) + 60}
    assert not verify_host_token(jwt.encode(claims, None, algorithm="none"), S)
    assert not verify_host_token(jwt.encode(claims, S.SECRET_KEY, algorithm="HS512"), S)


def test_verify_ws_token():
    token, _ = issue_host_token(S)
    assert verify_ws_token(token, S)
    assert not verify_ws_token("nope", S)


def _client() -> TestClient:
    app = FastAPI()
    app.dependency_overrides[container_dep] = lambda: SimpleNamespace(settings=S)

    @app.get("/x", dependencies=[Depends(require_host)])
    def x() -> dict:
        return {"ok": True}

    return TestClient(app)


def test_require_host():
    c = _client()
    assert c.get("/x").status_code == 401
    assert c.get("/x", headers={"Authorization": "Bearer bad"}).status_code == 401
    assert c.get("/x", headers={"Authorization": "Basic abc"}).status_code == 401
    token, _ = issue_host_token(S)
    r = c.get("/x", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
