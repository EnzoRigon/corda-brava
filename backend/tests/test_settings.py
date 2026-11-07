"""Tests for app settings defaults and env override."""

import pytest

from app.core import settings as settings_module
from app.core.settings import Settings, get_settings

# Captured at import, before the suite's autouse fixture hides every .env from Settings.
_APP_ENV_FILE = Settings.model_config["env_file"]


def test_the_app_reads_only_backend_env_never_the_docker_root_env() -> None:
    assert _APP_ENV_FILE == settings_module.BACKEND_ENV_FILE
    assert settings_module.BACKEND_ENV_FILE.parent.name == "backend"
    assert settings_module.ROOT_ENV_FILE == settings_module.BACKEND_ENV_FILE.parent.parent / ".env"


def test_ops_settings_add_the_root_env_and_backend_env_wins(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, backend = tmp_path / "root.env", tmp_path / "backend.env"
    root.write_text(
        "AZURE_SERVICEBUS_CONNECTION_STRING=from-root\nAZURE_SERVICEBUS_QUEUE_NAME=root-queue\n"
    )
    backend.write_text("AZURE_SERVICEBUS_QUEUE_NAME=backend-queue\n")
    monkeypatch.setattr(settings_module, "ROOT_ENV_FILE", root)
    monkeypatch.setattr(settings_module, "BACKEND_ENV_FILE", backend)
    ops = settings_module.settings_with_root_env()
    assert ops.AZURE_SERVICEBUS_CONNECTION_STRING == "from-root"
    assert ops.AZURE_SERVICEBUS_QUEUE_NAME == "backend-queue"


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
