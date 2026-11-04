"""Analytics payload (camelCase JSON on the wire, per prompt.md section 15)."""

# ruff: noqa: N815 - wire format is camelCase per spec

from __future__ import annotations

from pydantic import BaseModel


class TeamCounts(BaseModel):
    inter: int = 0
    gremio: int = 0


class PullTotals(BaseModel):
    overall: int = 0
    inter: int = 0
    gremio: int = 0


class TimelinePoint(BaseModel):
    t: int
    inter: int
    gremio: int


class Peak(BaseModel):
    value: int
    t: int


class PlayerStats(BaseModel):
    playerId: str
    name: str
    team: str
    pulls: int
    pctOfTeam: float
    pctOfAll: float
    pullsPerSec: float


class TeamStats(BaseModel):
    players: int
    totalPulls: int
    avgPullsPerPlayer: float
    bestPlayer: PlayerStats | None
    worstPlayer: PlayerStats | None


class TeamsStats(BaseModel):
    inter: TeamStats
    gremio: TeamStats


class AnalyticsPayload(BaseModel):
    result: str | None
    endReason: str | None
    durationS: int
    totalPlayers: int
    playersPerTeam: TeamCounts
    totalPulls: PullTotals
    pullsPerSecond: list[TimelinePoint]
    peak: Peak
    finalRope: float
    teams: TeamsStats
    players: list[PlayerStats]
    leaderboard: list[PlayerStats]
