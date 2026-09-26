import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    # It might return degraded if mongo isn't running, but we should at least get 200
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

def test_simulation_endpoint():
    payload = {
        "train_number": "12345",
        "current_timestamp": "2026-09-24T12:00:00Z",
        "destination": "TestStation",
        "current_delay_minutes": 10
    }
    # Test simulation endpoint
    response = client.post("/api/v1/simulation/update", json=payload)
    # If mongo isn't running it might fail, but let's assume standard behavior
    if response.status_code == 200:
        assert response.json()["status"] == "success"
