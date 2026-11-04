"""Public player routes: match info and join (one player per device, idempotent)."""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import ContainerDep
from app.domain.entities import Match, Player, PullEvent
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
from app.schemas.pulls import MeResponse, PullAccepted, PullRequest
from app.services.match_service import ConflictError, MatchNotFoundError
from app.services.player_session import issue_player_token, verify_player_token

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


NOT_RUNNING_DETAIL = "A partida não está em andamento"
_SCREEN = {MatchStatus.LOBBY: "wait", MatchStatus.RUNNING: "play", MatchStatus.FINISHED: "end"}


def _authed_player(c: ContainerDep, match_id: str, player_id: str, token: str) -> Player:
    """401 for an invalid token; 403 if it is valid but for another match/player."""
    claims = verify_player_token(token, c.settings)
    if claims is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    if claims["match_id"] != match_id or claims["player_id"] != player_id:
        raise HTTPException(status_code=403, detail="Token não pertence a este jogador")
    player = c.players.get_player(player_id)
    if player is None or player.match_id != match_id:
        raise HTTPException(status_code=403, detail="Jogador não pertence a esta partida")
    return player


@router.post("/{match_id}/pulls", response_model=PullAccepted, status_code=202)
async def pulls(match_id: str, body: PullRequest, c: ContainerDep) -> PullAccepted:
    player = _authed_player(c, match_id, body.playerId, body.playerToken)
    m = _match(c, match_id)
    if m.status is not MatchStatus.RUNNING:
        raise ConflictError(NOT_RUNNING_DETAIL)
    if body.count < 1:
        raise HTTPException(status_code=422, detail="count deve ser >= 1")
    count = min(body.count, c.settings.MAX_PULLS_PER_BATCH)
    now = time.monotonic()
    for k in [k for k, exp in c.seen_batches.items() if exp <= now]:
        del c.seen_batches[k]
    key = f"{match_id}:{body.batchId}"
    if key not in c.seen_batches:
        c.seen_batches[key] = now + c.settings.BATCH_DEDUP_TTL_S
        await c.queue.enqueue(
            PullEvent(
                id=str(uuid.uuid4()),
                match_id=match_id,
                player_id=player.id,
                team=player.team,
                count=count,
                client_ts=body.clientTs,
                batch_id=body.batchId,
            )
        )
    return PullAccepted(accepted=count)


@router.get("/{match_id}/me", response_model=MeResponse, response_model_exclude_none=True)
def me(match_id: str, playerId: str, token: str, c: ContainerDep) -> MeResponse:  # noqa: N803
    player = _authed_player(c, match_id, playerId, token)
    m = _match(c, match_id)
    result = m.result.value.upper() if m.status is MatchStatus.FINISHED and m.result else None
    return MeResponse(
        screen=_SCREEN[m.status], team=player.team, matchStatus=m.status, result=result
    )
