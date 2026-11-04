import asyncio

from app.services import registry as reg_mod
from app.services.registry import MatchRegistry


async def test_slow_listener_dropped_on_timeout(monkeypatch) -> None:
    monkeypatch.setattr(reg_mod, "BROADCAST_TIMEOUT_S", 0.05)
    r, got = MatchRegistry(), []

    async def slow(_):
        await asyncio.sleep(5)

    async def ok(p):
        got.append(p)

    r.add_listener("m", slow)
    r.add_listener("m", ok)
    await r.broadcast("m", {"a": 1})
    assert got == [{"a": 1}] and r._listeners["m"] == {ok}
