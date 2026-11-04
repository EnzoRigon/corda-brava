"""Host password check and JWT session tokens."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

import jwt

from app.core.settings import Settings

_ALG = "HS256"


def check_password(candidate: str, settings: Settings) -> bool:
    """Constant-time comparison against HOST_PASSWORD."""
    return secrets.compare_digest(candidate.encode(), settings.HOST_PASSWORD.encode())


def issue_host_token(settings: Settings) -> tuple[str, datetime]:
    """Return a signed host JWT and its expiry."""
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.HOST_TOKEN_TTL_SECONDS)
    token = jwt.encode({"role": "host", "exp": expires_at}, settings.SECRET_KEY, algorithm=_ALG)
    return token, expires_at


def verify_host_token(token: str, settings: Settings) -> bool:
    """True only for a valid, unexpired token with role=host. Never raises."""
    try:
        claims = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[_ALG], options={"require": ["exp"]}
        )
    except Exception:  # noqa: BLE001 - any failure means invalid
        return False
    return claims.get("role") == "host"
