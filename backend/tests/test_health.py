from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from app.config import Settings
from app.db import get_session
from app.main import create_app


@pytest.fixture
def client():
    app = create_app(Settings(_env_file=None, db_password="test-only"))
    with TestClient(app) as client:
        yield client


def test_live_without_database(client):
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "aegislend-api"}


def test_ready_after_migration(client):
    session = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = "1"
    client.app.dependency_overrides[get_session] = lambda: session
    assert client.get("/api/v1/health/ready").json()["database"] == "ready"


def test_database_failure_is_redacted(client):
    session = MagicMock()
    session.execute.side_effect = OperationalError("SELECT 1", {}, Exception("secret-password"))
    client.app.dependency_overrides[get_session] = lambda: session
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"
    assert "secret-password" not in response.text


def test_missing_migration_is_not_ready(client):
    session = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = None
    client.app.dependency_overrides[get_session] = lambda: session
    assert client.get("/api/v1/health/ready").status_code == 503


def test_cors_allowlist(client):
    allowed = client.get("/api/v1/health/live", headers={"Origin": "http://localhost:5173"})
    denied = client.get("/api/v1/health/live", headers={"Origin": "https://untrusted.example"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in denied.headers


def test_unknown_route(client):
    assert client.get("/api/v1/missing").status_code == 404
