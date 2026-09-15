import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify that root endpoint returns project metadata and routes."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "health" in data


def test_health_endpoint():
    """Verify that health check endpoint returns 200 and expected schema."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "app_name" in data
    assert "version" in data
    assert "database_connected" in data
    assert "database_status" in data
    assert "timestamp" in data
