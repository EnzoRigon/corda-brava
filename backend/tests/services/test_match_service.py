"""MatchService state-machine tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.domain.enums import MatchStatus
from app.repositories.sqlite.connection import close_connection
from app.services.match_service import ConflictError
from tests.services.test_consumer import T0, Env


@pytest.fixture()
def env(tmp_path: Path):
    e = Env(tmp_path)
    yield e
    close_connection(e.db)


async def test_start_sets_times_and_runs_loop(env: Env) -> None:
    m = env.svc.start(env.match.id)
    assert m.status is MatchStatus.RUNNING
    assert m.started_at == T0 and (m.ends_at - m.started_at).total_seconds() == 60
    assert env.registry.is_running(env.match.id)
    await env.svc.cancel(env.match.id)
    assert not env.registry.is_running(env.match.id)


async def test_start_twice_conflicts(env: Env) -> None:
    env.svc.start(env.match.id)
    with pytest.raises(ConflictError):
        env.svc.start(env.match.id)
    await env.svc.cancel(env.match.id)


async def test_update_duration_only_in_lobby(env: Env) -> None:
    assert env.svc.update_duration(env.match.id, 90).config.duration_s == 90
    env.svc.start(env.match.id)
    with pytest.raises(ConflictError):
        env.svc.update_duration(env.match.id, 100)
    await env.svc.cancel(env.match.id)


async def test_ptbr_conflict_messages(env: Env) -> None:
    env.svc.start(env.match.id)
    with pytest.raises(ConflictError, match="já foi iniciada"):
        env.svc.start(env.match.id)
    with pytest.raises(ConflictError, match="só pode ser alterada"):
        env.svc.update_duration(env.match.id, 100)
    await env.svc.cancel(env.match.id)


async def test_resume_running_restarts_loop_and_finishes_expired(env: Env) -> None:
    env.force_running()  # RUNNING in the repo, no loop (as after a restart)
    assert not env.registry.is_running(env.match.id)
    env.svc.resume_running()
    assert env.registry.is_running(env.match.id)
    await env.svc.cancel(env.match.id)

    env.force_running()
    env.now = T0 + __import__("datetime").timedelta(seconds=61)  # expired while down
    env.svc.resume_running()
    for _ in range(50):
        if not env.registry.is_running(env.match.id):
            break
        await __import__("asyncio").sleep(0.01)
    m = env.matches.get_match(env.match.id)
    assert m.status is MatchStatus.FINISHED and m.end_reason is not None


def test_view_lobby_remaining(env: Env) -> None:
    v = env.svc.get_match_view(env.match.id)
    assert v.status is MatchStatus.LOBBY and v.remaining_s == 60


async def test_listeners_cleared_when_loop_finishes(env: Env) -> None:
    async def cb(_: dict) -> None: ...

    env.registry.add_listener(env.match.id, cb)
    env.svc.start(env.match.id)
    env.now = T0 + __import__("datetime").timedelta(seconds=61)
    for _ in range(50):
        if not env.registry.is_running(env.match.id):
            break
        await __import__("asyncio").sleep(0.01)
    assert env.registry._listeners.get(env.match.id) is None
