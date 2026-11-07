"""Queue provisioning: create with the app's properties, or check and fix an existing queue."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

import pytest
from azure.core.exceptions import HttpResponseError, ResourceExistsError

from app.core.settings import Settings
from app.queue import provision


def _good_properties(**over: object) -> SimpleNamespace:
    props = {
        "lock_duration": timedelta(seconds=10),
        "max_delivery_count": 10,
        "default_message_time_to_live": timedelta(hours=1),
        "duplicate_detection_history_time_window": timedelta(minutes=10),
        "requires_duplicate_detection": True,
        "requires_session": False,
    }
    return SimpleNamespace(**(props | over))


class FakeAdmin:
    def __init__(self) -> None:
        self.existing: SimpleNamespace | None = None
        self.error: Exception | None = None
        self.created: tuple[str, dict] | None = None
        self.updated: SimpleNamespace | None = None

    def __enter__(self) -> FakeAdmin:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def create_queue(self, name: str, **properties: object) -> None:
        if self.error:
            raise self.error
        if self.existing is not None:
            raise ResourceExistsError("already there")
        self.created = (name, properties)

    def get_queue(self, name: str) -> SimpleNamespace:
        return self.existing

    def update_queue(self, props: SimpleNamespace) -> None:
        self.updated = props


@pytest.fixture()
def admin(monkeypatch: pytest.MonkeyPatch) -> FakeAdmin:
    fake = FakeAdmin()
    monkeypatch.setattr(
        provision.ServiceBusAdministrationClient, "from_connection_string", lambda _conn: fake
    )
    return fake


def test_creates_the_queue_with_the_properties_the_app_relies_on(admin: FakeAdmin) -> None:
    assert provision.ensure_queue("conn", "pulls").outcome == "created"
    name, props = admin.created
    assert name == "pulls"
    assert props["lock_duration"] == timedelta(seconds=10)  # QUEUE_LEASE_TIMEOUT_S's default
    assert props["max_delivery_count"] == 10
    assert props["requires_duplicate_detection"] is True
    assert props["duplicate_detection_history_time_window"] == timedelta(minutes=10)
    assert props["default_message_time_to_live"] == timedelta(hours=1)


def test_the_lock_duration_follows_the_lease_setting(admin: FakeAdmin) -> None:
    provision.ensure_queue("conn", "pulls", timedelta(seconds=20))
    assert admin.created[1]["lock_duration"] == timedelta(seconds=20)


@pytest.mark.parametrize("seconds", [4, 301])
def test_a_lock_duration_service_bus_rejects_is_refused_up_front(
    admin: FakeAdmin, seconds: int
) -> None:
    with pytest.raises(ValueError, match="5-300 s"):
        provision.ensure_queue("conn", "pulls", timedelta(seconds=seconds))
    assert admin.created is None


def test_an_existing_queue_that_matches_is_left_alone(admin: FakeAdmin) -> None:
    admin.existing = _good_properties()
    assert provision.ensure_queue("conn", "pulls").outcome == "unchanged"
    assert admin.created is None and admin.updated is None


def test_an_existing_queue_with_other_updatable_properties_is_fixed(admin: FakeAdmin) -> None:
    admin.existing = _good_properties(lock_duration=timedelta(seconds=60), max_delivery_count=3)
    status = provision.ensure_queue("conn", "pulls")
    assert (status.outcome, status.changed) == ("updated", ["lock_duration", "max_delivery_count"])
    assert admin.updated.lock_duration == timedelta(seconds=10)
    assert admin.updated.max_delivery_count == 10


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"requires_duplicate_detection": False}, "duplicate detection is off"),
        ({"requires_session": True}, "it requires sessions"),
    ],
)
def test_an_existing_queue_that_must_be_recreated_is_an_error(
    admin: FakeAdmin, override: dict, reason: str
) -> None:
    admin.existing = _good_properties(**override)
    with pytest.raises(provision.QueueMismatchError, match=reason):
        provision.ensure_queue("conn", "pulls")
    assert admin.updated is None


def _settings(monkeypatch: pytest.MonkeyPatch, **values: object) -> None:
    monkeypatch.setattr(provision, "settings_with_root_env", lambda: Settings(**values))


_CONFIGURED = {"AZURE_SERVICEBUS_CONNECTION_STRING": "conn", "AZURE_SERVICEBUS_QUEUE_NAME": "pulls"}


def test_main_reports_created_updated_then_unchanged(
    admin: FakeAdmin, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _settings(monkeypatch, **_CONFIGURED, QUEUE_LEASE_TIMEOUT_S=15)
    assert provision.main() == 0
    assert "created" in capsys.readouterr().out
    assert admin.created[1]["lock_duration"] == timedelta(seconds=15)
    admin.existing = _good_properties()
    assert provision.main() == 0
    assert "updated (lock_duration)" in capsys.readouterr().out
    admin.existing = _good_properties(lock_duration=timedelta(seconds=15))
    assert provision.main() == 0
    assert "unchanged" in capsys.readouterr().out


def test_main_without_configuration_exits_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _settings(monkeypatch)
    assert provision.main() == 2
    assert "AZURE_SERVICEBUS_CONNECTION_STRING" in capsys.readouterr().err


def test_main_with_an_out_of_range_lease_exits_2(
    admin: FakeAdmin, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _settings(monkeypatch, **_CONFIGURED, QUEUE_LEASE_TIMEOUT_S=1)
    assert provision.main() == 2
    assert "5-300 s" in capsys.readouterr().err


def test_main_reports_a_queue_that_must_be_recreated_with_exit_1(
    admin: FakeAdmin, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    admin.existing = _good_properties(requires_duplicate_detection=False)
    _settings(monkeypatch, **_CONFIGURED)
    assert provision.main() == 1
    assert "cannot be changed after creation" in capsys.readouterr().err


def test_main_turns_an_azure_error_into_exit_1(
    admin: FakeAdmin, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    admin.error = HttpResponseError("401 Unauthorized")
    _settings(monkeypatch, **_CONFIGURED)
    assert provision.main() == 1
    assert "Could not create or update queue 'pulls'" in capsys.readouterr().err
