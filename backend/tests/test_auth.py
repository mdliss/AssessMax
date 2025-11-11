"""Tests for authentication module"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.auth.models import TokenData, UserRole
from app.main import app

client = TestClient(app)


def test_health_check_no_auth():
    """Health check should work without authentication"""
    response = client.get("/healthz")
    assert response.status_code == 200


def test_root_endpoint_no_auth():
    """Root endpoint should work without authentication"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["auth"] == "AWS Cognito"


def test_user_info_requires_auth():
    """User info endpoint should require authentication"""
    response = client.get("/auth/me")
    assert response.status_code == 403  # No Authorization header


def test_educator_endpoint_requires_auth():
    """Educator endpoint should require authentication"""
    response = client.get("/auth/educator-only")
    assert response.status_code == 403


def test_admin_endpoint_requires_auth():
    """Admin endpoint should require authentication"""
    response = client.get("/auth/admin-only")
    assert response.status_code == 403


def test_invalid_token_format():
    """Invalid token format should return 403"""
    headers = {"Authorization": "Bearer invalid-token"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 403


def test_token_data_model():
    """Test TokenData model properties"""
    token_data = TokenData(
        sub="123e4567-e89b-12d3-a456-426614174000",
        email="educator@example.com",
        username="educator",
        roles=[UserRole.EDUCATOR],
        cognito_groups=["educator"],
    )

    assert token_data.is_educator
    assert not token_data.is_admin
    assert not token_data.is_read_only
    assert token_data.display_name == "educator"


def test_token_data_display_name_truncation():
    """Test display name truncation for long usernames"""
    long_username = "a" * 50
    token_data = TokenData(
        sub="123e4567-e89b-12d3-a456-426614174000",
        email="user@example.com",
        username=long_username,
        roles=[UserRole.EDUCATOR],
    )

    assert len(token_data.display_name) == 40
    assert token_data.display_name.endswith("...")


def test_token_data_admin_role():
    """Test TokenData with admin role"""
    token_data = TokenData(
        sub="123e4567-e89b-12d3-a456-426614174000",
        email="admin@example.com",
        username="admin",
        roles=[UserRole.ADMIN],
        cognito_groups=["admin"],
    )

    assert token_data.is_admin
    assert not token_data.is_educator
    assert not token_data.is_read_only


def test_token_data_multiple_roles():
    """Test TokenData with multiple roles"""
    token_data = TokenData(
        sub="123e4567-e89b-12d3-a456-426614174000",
        email="superuser@example.com",
        username="superuser",
        roles=[UserRole.ADMIN, UserRole.EDUCATOR],
        cognito_groups=["admin", "educator"],
    )

    assert token_data.is_admin
    assert token_data.is_educator
    assert not token_data.is_read_only
