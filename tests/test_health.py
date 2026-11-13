import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add backend directory to python path for testing import resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "FinGuard AI" in data["service"]
    assert data["active_policy_version"] == "1.1.0"
    assert "Zero AI" in data["engine_mode"]


def test_root_health_alias():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
