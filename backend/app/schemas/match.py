"""Host match models shared by the HTTP routes and the WS snapshot (camelCase on the wire)."""

# ruff: noqa: N815 - wire format is camelCase per spec

from __future__ import annotations

from pydantic import BaseModel

from app.domain.entities import MatchConfig, TeamConfig
from app.domain.enums import BalanceMode
from app.schemas.player import TeamColors


class CreateMatchRequest(BaseModel):
    durationS: int | None = None
    balanceMode: BalanceMode | None = None


class UpdateMatchRequest(BaseModel):
    durationS: int


class TeamOut(BaseModel):
    id: str
    name: str
    colors: TeamColors


class TeamsOut(BaseModel):
    inter: TeamOut
    gremio: TeamOut


class ConfigOut(BaseModel):
    durationS: int
    ropeTarget: int
    balanceMode: BalanceMode
    teams: TeamsOut


class RosterPlayer(BaseModel):
    id: str
    name: str


class Roster(BaseModel):
    inter: list[RosterPlayer]
    gremio: list[RosterPlayer]


class TeamScore(BaseModel):
    pulls: int


class Scores(BaseModel):
    inter: TeamScore
    gremio: TeamScore


class MatchView(BaseModel):
    """Full host view; also the ``match`` body of the WS ``snapshot`` message."""

    id: str
    status: str  # "LOBBY" | "RUNNING" | "FINISHED"
    config: ConfigOut
    roster: Roster
    rope: float
    remainingS: float
    scores: Scores
    result: str | None  # "INTER" | "GREMIO" | "DRAW" | null
    endReason: str | None  # "win" | "timeout" | null


class CreateMatchResponse(BaseModel):
    matchId: str
    joinUrl: str
    qrPayload: str
    config: ConfigOut


def _team(t: TeamConfig) -> TeamOut:
    return TeamOut(
        id=t.id,
        name=t.name,
        colors=TeamColors(primary=t.primary_color, secondary=t.secondary_color),
    )


def config_out(c: MatchConfig) -> ConfigOut:
    return ConfigOut(
        durationS=c.duration_s,
        ropeTarget=c.rope_target,
        balanceMode=c.balance_mode,
        teams=TeamsOut(inter=_team(c.inter), gremio=_team(c.gremio)),
    )
