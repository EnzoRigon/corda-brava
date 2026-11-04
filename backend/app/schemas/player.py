"""Player API models (camelCase JSON on the wire)."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.domain.enums import MatchStatus, Team

NAME_MAX = 24

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=NAME_MAX)]


class JoinRequest(BaseModel):
    name: Name
    team: Team
    deviceId: Annotated[str, StringConstraints(min_length=1, max_length=128)]  # noqa: N815


class JoinResponse(BaseModel):
    playerId: str  # noqa: N815
    playerToken: str  # noqa: N815
    team: Team


class TeamColors(BaseModel):
    primary: str
    secondary: str


class PublicTeam(BaseModel):
    name: str
    colors: TeamColors


class PublicTeams(BaseModel):
    inter: PublicTeam
    gremio: PublicTeam


class Counts(BaseModel):
    inter: int
    gremio: int


class PublicMatch(BaseModel):
    status: MatchStatus
    teams: PublicTeams
    counts: Counts
    durationS: int  # noqa: N815
