"""Single-writer consumer loop: the only code that mutates a running match."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime

from app.core.settings import Settings
from app.domain.entities import MatchState, TickInput
from app.domain.enums import MatchStatus, Team
from app.domain.rules import apply_pulls, check_win, resolve_result
from app.queue.interfaces import EventQueue
from app.repositories.interfaces import EventRepository, MatchRepository, PlayerRepository
from app.services.registry import Broadcast

MAX_BATCH_MESSAGES = 500


def utcnow() -> datetime:
    return datetime.now(UTC)


class ConsumerLoop:
    def __init__(
        self,
        match_id: str,
        *,
        matches: MatchRepository,
        players: PlayerRepository,
        events: EventRepository,
        queue: EventQueue,
        settings: Settings,
        broadcast: Broadcast,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        self.match_id = match_id
        self._matches, self._players, self._events = matches, players, events
        self._queue, self._settings = queue, settings
        self._broadcast, self._clock = broadcast, clock
        self._scores = {Team.INTER: 0, Team.GREMIO: 0}
        for e in events.list_events(match_id):  # resume totals after a restart
            self._scores[e.team] += e.count

    async def run(self) -> None:
        """Tick until the match finishes; cancel the task to stop early."""
        while not await self.tick():
            await asyncio.sleep(self._settings.TICK_INTERVAL_MS / 1000)

    async def tick(self) -> bool:
        """One tick. Returns True once the match is FINISHED."""
        match = self._matches.get_match(self.match_id)
        if match is None or match.status is not MatchStatus.RUNNING:
            return True
        cfg, now = match.config, self._clock()

        msgs = await self._queue.receive_batch(MAX_BATCH_MESSAGES, 0)
        foreign = [m for m in msgs if m.payload.match_id != self.match_id]
        if foreign:
            await self._queue.abandon(foreign)
        mine = [m for m in msgs if m.payload.match_id == self.match_id]

        delta = {Team.INTER: 0, Team.GREMIO: 0}
        for m in mine:
            ev = m.payload
            # dedup: a redelivered/repeated batch_id has no effect (but is still acked)
            if self._events.event_exists(self.match_id, ev.batch_id):
                continue
            self._events.add_event(ev)
            delta[ev.team] += ev.count
        for t, n in delta.items():
            self._scores[t] += n

        roster = self._players.list_players(self.match_id)
        tick_in = TickInput(
            pulls_inter=delta[Team.INTER],
            pulls_gremio=delta[Team.GREMIO],
            players_inter=sum(p.team is Team.INTER for p in roster),
            players_gremio=sum(p.team is Team.GREMIO for p in roster),
        )
        state = MatchState(
            match_id=match.id,
            status=match.status,
            rope_position=match.rope_position,
            started_at=match.started_at,
            ends_at=match.ends_at,
        )
        state = apply_pulls(
            state,
            tick_in,
            balance_mode=cfg.balance_mode,
            pull_unit=self._settings.PULL_UNIT,
            rope_target=cfg.rope_target,
        )
        timed_out = match.ends_at is not None and now >= match.ends_at
        won = check_win(state.rope_position, cfg.rope_target) is not None
        match.rope_position = state.rope_position
        finished = won or timed_out
        if finished:
            match.result, match.end_reason = resolve_result(
                state, timed_out=timed_out, rope_target=cfg.rope_target
            )
            match.status = MatchStatus.FINISHED
        self._matches.update_match(match)  # durable before ack
        if mine:
            await self._queue.ack(mine)

        remaining = max(0.0, (match.ends_at - now).total_seconds()) if match.ends_at else 0.0
        await self._broadcast(
            {
                "type": "tick",
                "rope": match.rope_position,
                "remainingS": remaining,
                "delta": {"inter": delta[Team.INTER], "gremio": delta[Team.GREMIO]},
                "scores": {
                    "inter": {"pulls": self._scores[Team.INTER]},
                    "gremio": {"pulls": self._scores[Team.GREMIO]},
                },
            }
        )
        if finished:
            await self._broadcast(
                {
                    "type": "ended",
                    "result": match.result.value.upper(),
                    "endReason": match.end_reason.value,
                    "finalRope": match.rope_position,
                }
            )
        return finished
