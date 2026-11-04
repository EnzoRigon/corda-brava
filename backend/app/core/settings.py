"""Application settings loaded from environment variables.

All tunables have sane defaults matching prompt.md §4.  Use ``get_settings()``
everywhere instead of instantiating ``Settings`` directly so the LRU cache
keeps a single instance per process.
"""

from __future__ import annotations

import secrets
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic-settings model — reads from env vars and .env file.

    All field names match the env var names exactly (case-insensitive on most
    platforms, but we document them in upper-snake-case).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Auth ──────────────────────────────────────────────────────────────────
    HOST_PASSWORD: str = "Inter>Gremio"
    HOST_TOKEN_TTL_SECONDS: int = 21_600  # 6 hours
    SECRET_KEY: str = secrets.token_hex(32)  # random dev default; override in prod

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./corda_brava.db"

    # ── API ───────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "*"  # comma-separated list or wildcard
    PUBLIC_BASE_URL: str = "http://localhost:5173"  # origin phones use; joinUrl = base/j/<id>

    # ── Game timing ───────────────────────────────────────────────────────────
    TICK_INTERVAL_MS: int = 500
    DEFAULT_MATCH_DURATION_S: int = 120
    MATCH_DURATION_MIN_S: int = 30
    MATCH_DURATION_MAX_S: int = 600

    # ── Rope mechanics ────────────────────────────────────────────────────────
    ROPE_TARGET: int = 100
    PULL_UNIT: float = 1.0
    MAX_PULLS_PER_BATCH: int = 200
    MAX_PULLS_PER_PLAYER_PER_S: int = 30  # anti-cheat: per-player cap, applied per tick

    # ── Idempotency ───────────────────────────────────────────────────────────
    BATCH_DEDUP_TTL_S: int = 30

    # ── Policies ──────────────────────────────────────────────────────────────
    LATE_JOIN_POLICY: Literal["block", "spectator"] = "block"
    TEAM_BALANCE_MODE: Literal["raw", "normalized"] = "normalized"

    # ── Queue backend ─────────────────────────────────────────────────────────
    QUEUE_BACKEND: Literal["memory", "azure_service_bus"] = "memory"
    QUEUE_LEASE_TIMEOUT_S: int = 10

    # ── Azure Service Bus (read only when QUEUE_BACKEND=azure_service_bus) ─────
    AZURE_SERVICEBUS_CONNECTION_STRING: str | None = None
    AZURE_SERVICEBUS_QUEUE_NAME: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton.

    Call ``get_settings.cache_clear()`` in tests when you need a fresh instance
    reflecting patched env vars.
    """
    return Settings()
