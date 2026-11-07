"""The unchanged ConsumerLoop driven through AzureServiceBusEventQueue (fake broker).

Proves the swap claim: same consumer, same scaffolding as ``tests/services/test_consumer.py``,
only the queue differs.  The fake clock replaces ``asyncio.sleep`` past the lease.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import timedelta
from pathlib import Path

import pytest

from app.domain.entities import Player, PullEvent
from app.domain.enums import MatchStatus, Team
from app.queue.azure_service_bus import AzureServiceBusEventQueue
from app.repositories.sqlite.connection import close_connection
from app.services.consumer import ConsumerLoop
from tests.queue.fake_servicebus import FakeBroker
from tests.services.test_consumer import T0, Env


class AzureEnv(Env):
    def __init__(self, tmp_path: Path, broker: FakeBroker) -> None:
        super().__init__(tmp_path)
        self.broker = broker
        self.queue = AzureServiceBusEventQueue(
            "conn",
            "pulls",
            lock_duration_s=broker.lock_duration_s,
            client_factory=broker.client,
            time_fn=broker.clock,
        )


async def _ignore(_payload: dict) -> None:
    return None


@pytest.fixture()
async def env(tmp_path: Path) -> AsyncIterator[AzureEnv]:
    e = AzureEnv(tmp_path, FakeBroker())
    await e.queue.start()
    yield e
    await e.queue.close()
    close_connection(e.db)


async def test_tick_applies_the_pull_and_acks_it(env: AzureEnv) -> None:
    loop = env.force_running()
    await env.pull(Team.GREMIO, 3, "b1")
    assert await loop.tick() is False
    assert env.matches.get_match(env.match.id).rope_position == 3
    assert len(env.events.list_events(env.match.id)) == 1
    assert env.broker.depth == 0  # completed on the broker
    env.broker.advance(env.broker.lock_duration_s * 2)
    assert await env.queue.receive_batch(10, 0) == []


async def test_a_crash_between_apply_and_ack_is_absorbed_by_idempotency(
    env: AzureEnv, monkeypatch: pytest.MonkeyPatch
) -> None:
    loop = env.force_running()
    await env.pull(Team.GREMIO, 3, "r1")

    async def lost_ack(messages) -> None:  # the process "dies" after the durable apply
        return None

    monkeypatch.setattr(env.queue, "ack", lost_ack)
    await loop.tick()
    monkeypatch.undo()
    assert env.broker.depth == 1  # still locked: never completed

    env.broker.advance(env.broker.lock_duration_s + 1)  # the lock runs out: redelivery
    await loop.tick()
    assert env.matches.get_match(env.match.id).rope_position == 3  # applied once
    assert len(env.events.list_events(env.match.id)) == 1
    assert env.broker.depth == 0  # the redelivery was acked without effect


async def test_a_failed_apply_is_redelivered_and_applied_once(
    env: AzureEnv, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.repositories.sqlite import match_repo

    loop = env.force_running()
    await env.pull(Team.GREMIO, 3, "r2")
    good = match_repo._UPDATE_MATCH
    monkeypatch.setattr(match_repo, "_UPDATE_MATCH", "UPDATE nope SET x=1")
    with pytest.raises(Exception):  # noqa: B017 - the tick aborts before the ack
        await loop.tick()
    monkeypatch.setattr(match_repo, "_UPDATE_MATCH", good)
    assert env.events.list_events(env.match.id) == []  # rolled back

    env.broker.advance(env.broker.lock_duration_s + 1)
    await loop.tick()
    assert env.matches.get_match(env.match.id).rope_position == 3
    assert len(env.events.list_events(env.match.id)) == 1


async def test_a_pull_for_another_running_match_is_left_for_its_own_loop(env: AzureEnv) -> None:
    loop = env.force_running()
    other = env.svc.create_match(duration_s=60)
    m = env.matches.get_match(other.id)
    m.status, m.started_at, m.ends_at = MatchStatus.RUNNING, T0, T0 + timedelta(seconds=60)
    env.matches.update_match(m)
    await env.queue.enqueue(
        PullEvent(
            id=str(uuid.uuid4()),
            match_id=other.id,
            player_id="p",
            team=Team.INTER,
            count=1,
            client_ts=0.0,
            batch_id="theirs",
        )
    )
    await loop.tick()
    (back,) = await env.queue.receive_batch(10, 0)  # abandoned: visible again at once
    assert (back.payload.batch_id, back.delivery_count) == ("theirs", 1)
    assert env.broker.abandons == 0  # not counted as a delivery attempt by the broker


async def test_concurrent_matches_never_dead_letter_each_others_pulls(env: AzureEnv) -> None:
    """Three RUNNING matches share the queue; each loop hands the others' pulls back."""
    loops = [env.force_running()]
    for _ in range(2):
        other = env.svc.create_match(duration_s=60)
        m = env.matches.get_match(other.id)
        m.status, m.started_at, m.ends_at = MatchStatus.RUNNING, T0, T0 + timedelta(seconds=60)
        env.matches.update_match(m)
        player = Player(
            id=str(uuid.uuid4()),
            match_id=other.id,
            device_id=f"d-{other.id}",
            name="x",
            team=Team.GREMIO,
            token="t",
        )
        env.players.add_player(player)
        loops.append(
            ConsumerLoop(
                other.id,
                matches=env.matches,
                players=env.players,
                events=env.events,
                queue=env.queue,
                settings=env.settings,
                broadcast=_ignore,
                clock=lambda: env.now,
            )
        )
        for i in range(5):
            await env.queue.enqueue(
                PullEvent(
                    id=str(uuid.uuid4()),
                    match_id=other.id,
                    player_id=player.id,
                    team=Team.GREMIO,
                    count=1,
                    client_ts=0.0,
                    batch_id=f"{other.id}-{i}",
                )
            )
    for _ in range(15):  # the first loop polls more often than MaxDeliveryCount (10) allows
        await loops[0].tick()
    for loop in loops[1:]:
        await loop.tick()
        assert len(env.events.list_events(loop.match_id)) == 5
    assert env.broker.dead_letters == [] and env.broker.abandons == 0
    assert env.broker.depth == 0


async def test_a_pull_for_a_finished_match_is_dropped(env: AzureEnv) -> None:
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
    assert env.broker.depth == 0  # acked, not left behind
