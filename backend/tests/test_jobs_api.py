"""Tests for jobs API endpoints"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_jwt_token() -> str:
    """Mock JWT token for authenticated user"""
    return "Bearer mock_token"


@pytest.fixture
def mock_admin_token() -> str:
    """Mock JWT token for admin user"""
    return "Bearer mock_admin_token"


@pytest.fixture
def mock_user() -> dict:
    """Mock regular user data"""
    from app.auth.models import UserRole

    return {
        "sub": "user-123",
        "email": "user@school.edu",
        "username": "user",
        "display_name": "Test User",
        "roles": [UserRole.READ_ONLY],
        "is_admin": False,
        "is_educator": False,
    }


@pytest.fixture
def mock_admin_user() -> dict:
    """Mock admin user data"""
    from app.auth.models import UserRole

    return {
        "sub": "admin-123",
        "email": "admin@school.edu",
        "username": "admin",
        "display_name": "Test Admin",
        "roles": [UserRole.ADMIN],
        "is_admin": True,
        "is_educator": True,
    }


@pytest.fixture
def mock_job() -> dict:
    """Mock job record"""
    job_id = uuid4()
    return {
        "job_id": str(job_id),
        "status": "queued",
        "class_id": "class123",
        "date": "2024-01-15",
        "input_keys": ["raw/dev/class123/2024-01-15/transcripts/file.jsonl"],
        "output_keys": [],
        "error": "",
        "metadata": {"source": "Zoom", "uploader_id": "user-123"},
        "started_at": "2024-01-15T10:00:00Z",
        "ended_at": "",
        "created_at": "2024-01-15T10:00:00Z",
    }


class TestGetJobStatus:
    """Test GET /v1/admin/jobs/{job_id} endpoint"""

    @patch("app.jobs.router.dynamodb_client")
    @patch("app.auth.dependencies.verify_jwt_token")
    def test_get_job_success(
        self,
        mock_verify: MagicMock,
        mock_dynamo: MagicMock,
        mock_jwt_token: str,
        mock_user: dict,
        mock_job: dict,
    ) -> None:
        """Test successful job retrieval"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_user)
        mock_dynamo.get_job_record.return_value = mock_job

        job_id = mock_job["job_id"]
        response = client.get(
            f"/v1/admin/jobs/{job_id}",
            headers={"Authorization": mock_jwt_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "queued"
        assert data["class_id"] == "class123"
        assert len(data["input_keys"]) == 1

    @patch("app.jobs.router.dynamodb_client")
    @patch("app.auth.dependencies.verify_jwt_token")
    def test_get_job_not_found(
        self,
        mock_verify: MagicMock,
        mock_dynamo: MagicMock,
        mock_jwt_token: str,
        mock_user: dict,
    ) -> None:
        """Test job not found"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_user)
        mock_dynamo.get_job_record.return_value = None

        job_id = uuid4()
        response = client.get(
            f"/v1/admin/jobs/{job_id}",
            headers={"Authorization": mock_jwt_token},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_job_no_auth(self) -> None:
        """Test without authentication"""
        job_id = uuid4()
        response = client.get(f"/v1/admin/jobs/{job_id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestListJobs:
    """Test GET /v1/admin/jobs endpoint"""

    @patch("app.jobs.router.dynamodb_client")
    @patch("app.auth.dependencies.verify_jwt_token")
    def test_list_jobs_success(
        self,
        mock_verify: MagicMock,
        mock_dynamo: MagicMock,
        mock_admin_token: str,
        mock_admin_user: dict,
        mock_job: dict,
    ) -> None:
        """Test successful job listing"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_admin_user)

        # Mock DynamoDB table scan
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": [mock_job]}
        mock_dynamo.jobs_table = mock_table

        response = client.get(
            "/v1/admin/jobs",
            headers={"Authorization": mock_admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert data["total"] == 1
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["job_id"] == mock_job["job_id"]

    @patch("app.jobs.router.dynamodb_client")
    @patch("app.auth.dependencies.verify_jwt_token")
    def test_list_jobs_with_filters(
        self,
        mock_verify: MagicMock,
        mock_dynamo: MagicMock,
        mock_admin_token: str,
        mock_admin_user: dict,
        mock_job: dict,
    ) -> None:
        """Test job listing with class_id filter"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_admin_user)

        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": [mock_job]}
        mock_dynamo.jobs_table = mock_table

        response = client.get(
            "/v1/admin/jobs?class_id=class123&status=queued",
            headers={"Authorization": mock_admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1

    @patch("app.auth.dependencies.verify_jwt_token")
    def test_list_jobs_not_admin(
        self,
        mock_verify: MagicMock,
        mock_jwt_token: str,
        mock_user: dict,
    ) -> None:
        """Test non-admin cannot list jobs"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_user)

        response = client.get(
            "/v1/admin/jobs",
            headers={"Authorization": mock_jwt_token},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_jobs_no_auth(self) -> None:
        """Test without authentication"""
        response = client.get("/v1/admin/jobs")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestJobPagination:
    """Test job listing pagination"""

    @patch("app.jobs.router.dynamodb_client")
    @patch("app.auth.dependencies.verify_jwt_token")
    def test_pagination(
        self,
        mock_verify: MagicMock,
        mock_dynamo: MagicMock,
        mock_admin_token: str,
        mock_admin_user: dict,
    ) -> None:
        """Test pagination parameters"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_admin_user)

        # Create multiple mock jobs
        jobs = []
        for i in range(25):
            jobs.append({
                "job_id": str(uuid4()),
                "status": "queued",
                "class_id": f"class{i}",
                "date": "2024-01-15",
                "input_keys": [],
                "output_keys": [],
                "error": "",
                "metadata": {},
                "started_at": f"2024-01-15T10:{i:02d}:00Z",
                "ended_at": "",
                "created_at": f"2024-01-15T10:{i:02d}:00Z",
            })

        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": jobs}
        mock_dynamo.jobs_table = mock_table

        # Request page 2 with 10 items per page
        response = client.get(
            "/v1/admin/jobs?page=2&page_size=10",
            headers={"Authorization": mock_admin_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10
        assert data["total"] == 25
        assert len(data["jobs"]) == 10
