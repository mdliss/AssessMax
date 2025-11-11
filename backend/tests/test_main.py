"""Tests for main API endpoints"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test the /healthz endpoint returns correct health status"""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert data["service"] == "assessmax-backend"


def test_root_endpoint():
    """Test the root endpoint returns API information"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "AssessMax API"
    assert "version" in data
    assert data["docs"] == "/docs"
    assert data["health"] == "/healthz"


def test_openapi_docs_accessible():
    """Test that OpenAPI documentation is accessible"""
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/redoc")
    assert response.status_code == 200

    response = client.get("/openapi.json")
    assert response.status_code == 200
