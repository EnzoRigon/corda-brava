"""Pure domain entities for Corda Brava.

These are framework-free Pydantic v2 models (no FastAPI / SQLite imports).
They represent the game state and events as they live in memory and flow
through the system.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from app.domain.enums import BalanceMode, EndReason, MatchResult, MatchStatus, Team


class TeamConfig(BaseModel):
    """Visual identity for a team within a match."""

    id: str  # e.g. "inter" or "gremio"
    name: str  # display name, e.g. "Inter" / "Grêmio"
    primary_color: str  # hex, e.g. "#E5050F"
    secondary_color: str  # hex, e.g. "#FFFFFF"


class MatchConfig(BaseModel):
    """Immutable match configuration set at creation time."""

    duration_s: int
    rope_target: int
    balance_mode: BalanceMode
    inter: TeamConfig
    gremio: TeamConfig


class Match(BaseModel):
    """Full match entity — combines config, status, and runtime fields."""

    id: str  # short URL-safe code, e.g. 6 alphanumeric chars
    status: MatchStatus = MatchStatus.LOBBY
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    # config
    config: MatchConfig

    # runtime (populated when match starts/finishes)
    rope_position: float = 0.0  # ∈ [-rope_target, +rope_target]
    started_at: datetime | None = None
    ends_at: datetime | None = None
    result: MatchResult | None = None
    end_reason: EndReason | None = None


class Player(BaseModel):
    """A participant in a match."""

    id: str
    match_id: str
    device_id: str  # from client localStorage UUID
    name: str
    team: Team
    token: str  # opaque player session token
    joined_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))


class PullEvent(BaseModel):
    """A single pull-batch event enqueued by a player.

    One row per processed batch — sufficient to reconstruct analytics.
    """

    id: str
    match_id: str
    player_id: str
    team: Team
    count: int  # number of pulls in this batch (already clamped)
    client_ts: float  # unix timestamp from the client
    server_ts: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    batch_id: str  # UUID from client, used for idempotency/dedup


class TickInput(BaseModel):
    """Aggregated per-team pull totals for a single consumer tick.

    Carries the raw pull counts and active player counts needed so the
    scoring engine can apply either RAW or NORMALIZED balance mode.
    """

    pulls_inter: int = 0
    pulls_gremio: int = 0
    players_inter: int = 0  # active player count — needed for normalized scoring
    players_gremio: int = 0


class MatchState(BaseModel):
    """Snapshot of all mutable runtime fields for a match.

    Produced by the consumer loop and broadcast to host WebSocket clients.
    The repo can also persist/restore this to/from the Match row.
    """

    match_id: str
    status: MatchStatus
    rope_position: float
    started_at: datetime | None = None
    ends_at: datetime | None = None
    remaining_s: float | None = None  # computed from clock each tick
    result: MatchResult | None = None
    end_reason: EndReason | None = None
