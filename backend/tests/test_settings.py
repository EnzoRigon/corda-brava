"""Tests for app settings defaults and env override."""

import pytest

from app.core.settings import Settings, get_settings


def test_default_host_password() -> None:
    s = Settings()
    assert s.HOST_PASSWORD == "Inter>Gremio"


def test_default_match_duration() -> None:
    s = Settings()
    assert s.DEFAULT_MATCH_DURATION_S == 120


def test_default_rope_target() -> None:
    s = Settings()
    assert s.ROPE_TARGET == 100


def test_default_team_balance_mode() -> None:
    s = Settings()
    assert s.TEAM_BALANCE_MODE == "normalized"


def test_default_queue_backend() -> None:
    s = Settings()
    assert s.QUEUE_BACKEND == "memory"


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEFAULT_MATCH_DURATION_S", "90")
    # Must bypass lru_cache by constructing a new Settings directly.
    s = Settings()
    assert s.DEFAULT_MATCH_DURATION_S == 90


def test_get_settings_returns_settings_instance() -> None:
    settings = get_settings()
    assert isinstance(settings, Settings)
