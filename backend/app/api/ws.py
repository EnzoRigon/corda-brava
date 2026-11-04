"""Host WebSocket: snapshot on connect, then player_joined / tick / ended / cancelled / reset."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.auth import verify_ws_token
from app.api.deps import get_container
from app.api.host import match_view
from app.services.analytics import compute_analytics

router = APIRouter()

CLOSE_POLICY = 1008
_CLOSING = {"cancelled", "reset"}  # terminal for this socket


@router.websocket("/api/host/matches/{match_id}/ws")
async def host_ws(websocket: WebSocket, match_id: str, token: str | None = None) -> None:
    c = get_container(websocket.app)
    await websocket.accept()
    if not verify_ws_token(token, c.settings) or c.matches.get_match(match_id) is None:
        await websocket.close(code=CLOSE_POLICY)
        return

    async def listener(payload: dict[str, Any]) -> None:
        if payload.get("type") == "ended" and "analytics" not in payload:
            m = c.matches.get_match(match_id)
            analytics = compute_analytics(
                m, c.players.list_players(match_id), c.events.list_events(match_id)
            )
            payload = {**payload, "analytics": analytics.model_dump(mode="json")}
        await websocket.send_json(payload)
        if payload.get("type") in _CLOSING:
            await websocket.close()

    c.registry.add_listener(match_id, listener)
    try:
        await websocket.send_json(
            {"type": "snapshot", "match": match_view(c, match_id).model_dump(mode="json")}
        )
        while True:
            await websocket.receive_text()  # ignore client chatter; raises on disconnect
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        c.registry.remove_listener(match_id, listener)
