"""Tests for the health check endpoint."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test that the health endpoint returns a 200 status code."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"


def test_health_endpoint_content(client: TestClient):
    """Test that the health endpoint returns the expected content."""
    response = client.get("/health")
    data = response.json()
    assert "version" in data
    assert "uptime" in data
    assert "environment" in data


def test_health_endpoint_headers(client: TestClient):
    """Test that the health endpoint returns the expected headers."""
    response = client.get("/health")
    assert "application/json" in response.headers["content-type"]
    
    # If we're using the performance middleware, this should exist
    if "x-process-time" in response.headers:
        process_time = float(response.headers["x-process-time"])
        assert process_time > 0 