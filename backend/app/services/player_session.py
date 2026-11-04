"""Player JWT session tokens (role=player), signed with SECRET_KEY."""

from __future__ import annotations

from typing import Any

import jwt

from app.core.settings import Settings

_ALG = "HS256"


def issue_player_token(match_id: str, player_id: str, device_id: str, settings: Settings) -> str:
    return jwt.encode(
        {"role": "player", "match_id": match_id, "player_id": player_id, "device_id": device_id},
        settings.SECRET_KEY,
        algorithm=_ALG,
    )


def verify_player_token(token: str, settings: Settings) -> dict[str, str] | None:
    """Return {match_id, player_id, device_id} for a valid player token, else None. Never raises."""
    try:
        claims: dict[str, Any] = jwt.decode(token, settings.SECRET_KEY, algorithms=[_ALG])
        if claims.get("role") != "player":
            return None
        return {k: str(claims[k]) for k in ("match_id", "player_id", "device_id")}
    except Exception:  # noqa: BLE001 - any failure means invalid
        return None
