"""Suite-wide guard: tests never read a developer's ``.env`` and never reach a real broker."""

from __future__ import annotations

import pytest

from app.core.settings import Settings


@pytest.fixture(autouse=True)
def _hermetic_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    # A ``.env`` holding real Azure credentials would otherwise flip every
    # ``Settings(...)`` built in a test to the Azure backend.
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setenv("QUEUE_BACKEND", "memory")
