"""Match lifecycle state machine: LOBBY -> RUNNING -> FINISHED."""

from __future__ import annotations

import secrets
import string
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from app.core.settings import Settings
from app.domain.entities import Match, MatchConfig, MatchState, TeamConfig
from app.domain.enums import BalanceMode, MatchStatus
from app.queue.interfaces import EventQueue
from app.repositories.interfaces import EventRepository, MatchRepository, PlayerRepository
from app.services.consumer import ConsumerLoop, utcnow
from app.services.registry import MatchRegistry

_ALPHABET = string.ascii_uppercase + string.digits


class ConflictError(Exception):
    """Illegal state transition; the API layer maps this to HTTP 409."""


class MatchNotFoundError(Exception):
    """Unknown match id; the API layer maps this to HTTP 404."""


class MatchService:
    def __init__(
        self,
        *,
        matches: MatchRepository,
        players: PlayerRepository,
        events: EventRepository,
        queue: EventQueue,
        registry: MatchRegistry,
        settings: Settings,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        self._matches, self._players, self._events = matches, players, events
        self._queue, self._registry, self._settings = queue, registry, settings
        self._clock = clock

    def _get(self, match_id: str) -> Match:
        match = self._matches.get_match(match_id)
        if match is None:
            raise MatchNotFoundError(match_id)
        return match

    def _check_duration(self, duration_s: int) -> int:
        s = self._settings
        if not s.MATCH_DURATION_MIN_S <= duration_s <= s.MATCH_DURATION_MAX_S:
            raise ValueError(
                f"duration_s must be in [{s.MATCH_DURATION_MIN_S}, {s.MATCH_DURATION_MAX_S}]"
            )
        return duration_s

    def create_match(
        self, duration_s: int | None = None, balance_mode: BalanceMode | None = None
    ) -> Match:
        s = self._settings
        config = MatchConfig(
            duration_s=self._check_duration(duration_s or s.DEFAULT_MATCH_DURATION_S),
            rope_target=s.ROPE_TARGET,
            balance_mode=balance_mode or BalanceMode(s.TEAM_BALANCE_MODE),
            inter=TeamConfig(
                id="inter", name="Inter", primary_color="#E5050F", secondary_color="#FFFFFF"
            ),
            gremio=TeamConfig(
                id="gremio", name="Grêmio", primary_color="#0D80BF", secondary_color="#000000"
            ),
        )
        match_id = "".join(secrets.choice(_ALPHABET) for _ in range(6))
        return self._matches.create_match(Match(id=match_id, config=config))

    def get_match_view(self, match_id: str) -> MatchState:
        m = self._get(match_id)
        remaining = float(m.config.duration_s)
        if m.status is MatchStatus.RUNNING and m.ends_at:
            remaining = max(0.0, (m.ends_at - self._clock()).total_seconds())
        elif m.status is MatchStatus.FINISHED:
            remaining = 0.0
        return MatchState(
            match_id=m.id,
            status=m.status,
            rope_position=m.rope_position,
            started_at=m.started_at,
            ends_at=m.ends_at,
            remaining_s=remaining,
            result=m.result,
            end_reason=m.end_reason,
        )

    def update_duration(self, match_id: str, duration_s: int) -> Match:
        m = self._get(match_id)
        if m.status is not MatchStatus.LOBBY:
            raise ConflictError("A duração só pode ser alterada no lobby")
        m.config.duration_s = self._check_duration(duration_s)
        return self._matches.update_match(m)

    def start(self, match_id: str) -> Match:
        """LOBBY -> RUNNING and spin up the consumer task (needs a running event loop)."""
        m = self._get(match_id)
        if m.status is not MatchStatus.LOBBY:
            raise ConflictError("A partida já foi iniciada ou encerrada")
        m.status = MatchStatus.RUNNING
        m.started_at = self._clock().astimezone(UTC)
        m.ends_at = m.started_at + timedelta(seconds=m.config.duration_s)
        m = self._matches.update_match(m)
        self._spawn_loop(match_id)
        return m

    def resume_running(self) -> None:
        """Restart recovery: re-launch loops for RUNNING matches (expired ones end on tick 1)."""
        for m in self._matches.list_running():
            if not self._registry.is_running(m.id):
                self._spawn_loop(m.id)

    def _spawn_loop(self, match_id: str) -> None:
        loop = ConsumerLoop(
            match_id,
            matches=self._matches,
            players=self._players,
            events=self._events,
            queue=self._queue,
            settings=self._settings,
            broadcast=lambda payload: self._registry.broadcast(match_id, payload),
            clock=self._clock,
        )
        self._registry.start_loop(match_id, loop.run())

    async def cancel(self, match_id: str) -> Match:
        """Tear down the loop; an unfinished match becomes FINISHED with no result."""
        m = self._get(match_id)
        await self._registry.stop_loop(match_id)
        if m.status is not MatchStatus.FINISHED:
            m.status = MatchStatus.FINISHED
            m = self._matches.update_match(m)
        return m
