"""Public player routes: match info and join (one player per device, idempotent)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import ContainerDep
from app.domain.entities import Match, Player
from app.domain.enums import MatchStatus, Team
from app.repositories.interfaces import UniqueConstraintError
from app.schemas.player import (
    Counts,
    JoinRequest,
    JoinResponse,
    PublicMatch,
    PublicTeam,
    PublicTeams,
    TeamColors,
)
from app.services.match_service import ConflictError, MatchNotFoundError
from app.services.player_session import issue_player_token

router = APIRouter(prefix="/api/matches", tags=["player"])

LATE_JOIN_DETAIL = "A partida já começou"


def _match(c: ContainerDep, match_id: str) -> Match:
    m = c.matches.get_match(match_id)
    if m is None:
        raise MatchNotFoundError(match_id)
    return m


def _team(t) -> PublicTeam:
    return PublicTeam(
        name=t.name, colors=TeamColors(primary=t.primary_color, secondary=t.secondary_color)
    )


@router.get("/{match_id}/public", response_model=PublicMatch)
def public_info(match_id: str, c: ContainerDep) -> PublicMatch:
    m = _match(c, match_id)
    players = c.players.list_players(match_id)
    return PublicMatch(
        status=m.status,
        teams=PublicTeams(inter=_team(m.config.inter), gremio=_team(m.config.gremio)),
        counts=Counts(
            inter=sum(p.team is Team.INTER for p in players),
            gremio=sum(p.team is Team.GREMIO for p in players),
        ),
        durationS=m.config.duration_s,
    )


@router.post("/{match_id}/players", response_model=JoinResponse)
def join(match_id: str, body: JoinRequest, c: ContainerDep) -> JoinResponse:
    m = _match(c, match_id)
    player = c.players.get_player_by_device(match_id, body.deviceId)
    if player is None:
        if m.status is not MatchStatus.LOBBY:
            # Both policies reject new joins; spectator mode is a frontend concern (see report).
            raise ConflictError(LATE_JOIN_DETAIL)
        pid = str(uuid.uuid4())
        player = Player(
            id=pid,
            match_id=match_id,
            device_id=body.deviceId,
            name=body.name,
            team=body.team,
            token=issue_player_token(match_id, pid, body.deviceId, c.settings),
        )
        try:
            player = c.players.add_player(player)
        except UniqueConstraintError:  # lost a race with the same device
            existing = c.players.get_player_by_device(match_id, body.deviceId)
            if existing is None:
                raise HTTPException(status_code=500, detail="join failed") from None
            player = existing
    token = issue_player_token(match_id, player.id, player.device_id, c.settings)
    return JoinResponse(playerId=player.id, playerToken=token, team=player.team)
