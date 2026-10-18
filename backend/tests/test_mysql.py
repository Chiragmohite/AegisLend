import os
import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.mark.mysql
@pytest.mark.skipif(os.getenv("RUN_MYSQL_TESTS") != "1", reason="Set RUN_MYSQL_TESTS=1 with migrated MySQL")
def test_real_mysql_readiness():
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        assert response.json()["database"] == "ready"
