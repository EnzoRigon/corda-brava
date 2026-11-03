"""Tests for the /health endpoint."""

from fastapi.testclient import TestClient

from app.core.app_factory import create_app
from app.core.settings import get_settings


def test_health_ok() -> None:
    app = create_app(get_settings())
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
