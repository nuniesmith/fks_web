"""Basic health check tests."""
import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_ready_endpoint():
    """Test readiness endpoint."""
    response = client.get("/ready")
    assert response.status_code == 200


def test_live_endpoint():
    """Test liveness endpoint."""
    response = client.get("/live")
    assert response.status_code == 200
