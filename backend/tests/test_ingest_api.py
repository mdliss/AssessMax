"""Tests for ingestion API endpoints"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_jwt_token() -> str:
    """Mock JWT token for educator"""
    return "Bearer mock_token_educator"


@pytest.fixture
def mock_user_educator() -> dict:
    """Mock educator user data"""
    from app.auth.models import UserRole

    return {
        "sub": "user-123",
        "email": "educator@school.edu",
        "username": "educator",
        "display_name": "Test Educator",
        "roles": [UserRole.EDUCATOR],
        "is_admin": False,
        "is_educator": True,
    }


class TestPresignedUploadEndpoint:
    """Test presigned upload endpoint"""

    @patch("app.ingest.router.s3_client")
    @patch("app.ingest.router.dynamodb_client")
    @patch("app.auth.dependencies.verify_jwt_token")
    def test_presigned_upload_success(
        self,
        mock_verify: MagicMock,
        mock_dynamo: MagicMock,
        mock_s3: MagicMock,
        mock_jwt_token: str,
        mock_user_educator: dict,
    ) -> None:
        """Test successful presigned upload URL generation"""
        # Mock auth
        from app.auth.models import TokenData, UserRole

        mock_verify.return_value = TokenData(**mock_user_educator)

        # Mock S3 and DynamoDB
        test_artifact_id = uuid4()
        mock_s3.generate_s3_key.return_value = "raw/dev/class123/2024-01-15/transcripts/file.jsonl"
        mock_s3.generate_presigned_upload_url.return_value = "https://s3.amazonaws.com/presigned-url"
        mock_dynamo.create_artifact_record.return_value = {"artifact_id": str(test_artifact_id)}

        # Make request
        response = client.post(
            "/v1/ingest/presigned-upload",
            json={
                "file_name": "transcript.jsonl",
                "file_format": "jsonl",
                "file_size_bytes": 1024,
                "class_id": "class123",
                "date": "2024-01-15",
                "content_type": "application/jsonl",
            },
            headers={"Authorization": mock_jwt_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "upload_url" in data
        assert "artifact_id" in data
        assert "s3_key" in data
        assert "expires_at" in data
        assert data["upload_method"] == "PUT"

    @patch("app.auth.dependencies.verify_jwt_token")
    def test_presigned_upload_file_too_large(
        self,
        mock_verify: MagicMock,
        mock_jwt_token: str,
        mock_user_educator: dict,
    ) -> None:
        """Test presigned upload with file too large"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_user_educator)

        # File larger than 50MB
        response = client.post(
            "/v1/ingest/presigned-upload",
            json={
                "file_name": "large.jsonl",
                "file_format": "jsonl",
                "file_size_bytes": 100 * 1024 * 1024,  # 100MB
                "class_id": "class123",
                "date": "2024-01-15",
            },
            headers={"Authorization": mock_jwt_token},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_presigned_upload_no_auth(self) -> None:
        """Test presigned upload without authentication"""
        response = client.post(
            "/v1/ingest/presigned-upload",
            json={
                "file_name": "transcript.jsonl",
                "file_format": "jsonl",
                "file_size_bytes": 1024,
                "class_id": "class123",
                "date": "2024-01-15",
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestTranscriptIngestEndpoint:
    """Test transcript ingestion endpoint"""

    @patch("app.ingest.router.s3_client")
    @patch("app.ingest.router.dynamodb_client")
    @patch("app.auth.dependencies.verify_jwt_token")
    def test_transcript_ingest_success(
        self,
        mock_verify: MagicMock,
        mock_dynamo: MagicMock,
        mock_s3: MagicMock,
        mock_jwt_token: str,
        mock_user_educator: dict,
    ) -> None:
        """Test successful transcript ingestion"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_user_educator)

        # Mock artifact exists
        test_artifact_id = uuid4()
        mock_dynamo.get_artifact_record.return_value = {
            "artifact_id": str(test_artifact_id),
            "artifact_key": "raw/dev/class123/2024-01-15/transcripts/file.jsonl",
            "class_id": "class123",
            "status": "pending_upload",
        }

        # Mock S3 file exists
        mock_s3.check_object_exists.return_value = True

        # Mock job creation
        test_job_id = uuid4()
        mock_dynamo.create_job_record.return_value = {
            "job_id": str(test_job_id),
            "status": "queued",
        }

        # Make request
        response = client.post(
            "/v1/ingest/transcripts",
            json={
                "artifact_id": str(test_artifact_id),
                "metadata": {
                    "class_id": "class123",
                    "date": "2024-01-15",
                    "student_roster": ["student1", "student2"],
                    "source": "Zoom",
                },
            },
            headers={"Authorization": mock_jwt_token},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "job_id" in data
        assert data["artifact_id"] == str(test_artifact_id)
        assert data["status"] == "queued"
        assert data["class_id"] == "class123"

    @patch("app.ingest.router.dynamodb_client")
    @patch("app.auth.dependencies.verify_jwt_token")
    def test_transcript_ingest_artifact_not_found(
        self,
        mock_verify: MagicMock,
        mock_dynamo: MagicMock,
        mock_jwt_token: str,
        mock_user_educator: dict,
    ) -> None:
        """Test transcript ingestion with non-existent artifact"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_user_educator)

        # Mock artifact doesn't exist
        mock_dynamo.get_artifact_record.return_value = None

        test_artifact_id = uuid4()
        response = client.post(
            "/v1/ingest/transcripts",
            json={
                "artifact_id": str(test_artifact_id),
                "metadata": {
                    "class_id": "class123",
                    "date": "2024-01-15",
                    "student_roster": ["student1"],
                    "source": "Zoom",
                },
            },
            headers={"Authorization": mock_jwt_token},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("app.ingest.router.s3_client")
    @patch("app.ingest.router.dynamodb_client")
    @patch("app.auth.dependencies.verify_jwt_token")
    def test_transcript_ingest_file_not_uploaded(
        self,
        mock_verify: MagicMock,
        mock_dynamo: MagicMock,
        mock_s3: MagicMock,
        mock_jwt_token: str,
        mock_user_educator: dict,
    ) -> None:
        """Test transcript ingestion when file not yet uploaded to S3"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_user_educator)

        # Mock artifact exists
        test_artifact_id = uuid4()
        mock_dynamo.get_artifact_record.return_value = {
            "artifact_id": str(test_artifact_id),
            "artifact_key": "raw/dev/class123/2024-01-15/transcripts/file.jsonl",
            "class_id": "class123",
        }

        # Mock S3 file doesn't exist
        mock_s3.check_object_exists.return_value = False

        response = client.post(
            "/v1/ingest/transcripts",
            json={
                "artifact_id": str(test_artifact_id),
                "metadata": {
                    "class_id": "class123",
                    "date": "2024-01-15",
                    "student_roster": ["student1"],
                    "source": "Zoom",
                },
            },
            headers={"Authorization": mock_jwt_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not found in S3" in response.json()["detail"]


class TestArtifactStatusEndpoint:
    """Test artifact status endpoint"""

    @patch("app.ingest.router.dynamodb_client")
    @patch("app.auth.dependencies.verify_jwt_token")
    def test_get_artifact_status_success(
        self,
        mock_verify: MagicMock,
        mock_dynamo: MagicMock,
        mock_jwt_token: str,
        mock_user_educator: dict,
    ) -> None:
        """Test successful artifact status retrieval"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_user_educator)

        # Mock artifact exists
        test_artifact_id = uuid4()
        mock_dynamo.get_artifact_record.return_value = {
            "artifact_id": str(test_artifact_id),
            "status": "uploaded",
            "class_id": "class123",
            "created_at": "2024-01-15T10:00:00Z",
            "artifact_key": "raw/dev/class123/2024-01-15/transcripts/file.jsonl",
        }

        response = client.get(
            f"/v1/ingest/artifacts/{test_artifact_id}",
            headers={"Authorization": mock_jwt_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["artifact_id"] == str(test_artifact_id)
        assert data["status"] == "uploaded"
        assert data["class_id"] == "class123"

    @patch("app.ingest.router.dynamodb_client")
    @patch("app.auth.dependencies.verify_jwt_token")
    def test_get_artifact_status_not_found(
        self,
        mock_verify: MagicMock,
        mock_dynamo: MagicMock,
        mock_jwt_token: str,
        mock_user_educator: dict,
    ) -> None:
        """Test artifact status with non-existent artifact"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_user_educator)

        mock_dynamo.get_artifact_record.return_value = None

        test_artifact_id = uuid4()
        response = client.get(
            f"/v1/ingest/artifacts/{test_artifact_id}",
            headers={"Authorization": mock_jwt_token},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("app.auth.dependencies.verify_jwt_token")
    def test_get_artifact_status_invalid_uuid(
        self,
        mock_verify: MagicMock,
        mock_jwt_token: str,
        mock_user_educator: dict,
    ) -> None:
        """Test artifact status with invalid UUID"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_user_educator)

        response = client.get(
            "/v1/ingest/artifacts/invalid-uuid",
            headers={"Authorization": mock_jwt_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestArtifactIngestEndpoint:
    """Test artifact ingestion endpoint"""

    @patch("app.ingest.router.s3_client")
    @patch("app.ingest.router.dynamodb_client")
    @patch("app.auth.dependencies.verify_jwt_token")
    def test_artifact_ingest_success(
        self,
        mock_verify: MagicMock,
        mock_dynamo: MagicMock,
        mock_s3: MagicMock,
        mock_jwt_token: str,
        mock_user_educator: dict,
    ) -> None:
        """Test successful artifact ingestion"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_user_educator)

        # Mock artifact exists
        test_artifact_id = uuid4()
        mock_dynamo.get_artifact_record.return_value = {
            "artifact_id": str(test_artifact_id),
            "artifact_key": "raw/dev/class123/2024-01-15/artifacts/essay.pdf",
            "class_id": "class123",
            "status": "pending_upload",
        }

        # Mock S3 file exists
        mock_s3.check_object_exists.return_value = True

        # Mock job creation
        test_job_id = uuid4()
        mock_dynamo.create_job_record.return_value = {
            "job_id": str(test_job_id),
            "status": "queued",
        }

        # Make request
        response = client.post(
            "/v1/ingest/artifacts",
            json={
                "artifact_id": str(test_artifact_id),
                "metadata": {
                    "class_id": "class123",
                    "date": "2024-01-15",
                    "student_id": "student1",
                    "artifact_type": "essay",
                },
            },
            headers={"Authorization": mock_jwt_token},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "job_id" in data
        assert data["artifact_id"] == str(test_artifact_id)
        assert data["status"] == "queued"
        assert data["class_id"] == "class123"
        assert data["student_id"] == "student1"

    @patch("app.ingest.router.dynamodb_client")
    @patch("app.auth.dependencies.verify_jwt_token")
    def test_artifact_ingest_artifact_not_found(
        self,
        mock_verify: MagicMock,
        mock_dynamo: MagicMock,
        mock_jwt_token: str,
        mock_user_educator: dict,
    ) -> None:
        """Test artifact ingestion with non-existent artifact"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_user_educator)

        # Mock artifact doesn't exist
        mock_dynamo.get_artifact_record.return_value = None

        test_artifact_id = uuid4()
        response = client.post(
            "/v1/ingest/artifacts",
            json={
                "artifact_id": str(test_artifact_id),
                "metadata": {
                    "class_id": "class123",
                    "date": "2024-01-15",
                    "student_id": "student1",
                    "artifact_type": "essay",
                },
            },
            headers={"Authorization": mock_jwt_token},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("app.ingest.router.s3_client")
    @patch("app.ingest.router.dynamodb_client")
    @patch("app.auth.dependencies.verify_jwt_token")
    def test_artifact_ingest_file_not_uploaded(
        self,
        mock_verify: MagicMock,
        mock_dynamo: MagicMock,
        mock_s3: MagicMock,
        mock_jwt_token: str,
        mock_user_educator: dict,
    ) -> None:
        """Test artifact ingestion when file not yet uploaded to S3"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_user_educator)

        # Mock artifact exists
        test_artifact_id = uuid4()
        mock_dynamo.get_artifact_record.return_value = {
            "artifact_id": str(test_artifact_id),
            "artifact_key": "raw/dev/class123/2024-01-15/artifacts/essay.pdf",
            "class_id": "class123",
        }

        # Mock S3 file doesn't exist
        mock_s3.check_object_exists.return_value = False

        response = client.post(
            "/v1/ingest/artifacts",
            json={
                "artifact_id": str(test_artifact_id),
                "metadata": {
                    "class_id": "class123",
                    "date": "2024-01-15",
                    "student_id": "student1",
                    "artifact_type": "essay",
                },
            },
            headers={"Authorization": mock_jwt_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not found in S3" in response.json()["detail"]

    @patch("app.ingest.router.s3_client")
    @patch("app.ingest.router.dynamodb_client")
    @patch("app.auth.dependencies.verify_jwt_token")
    def test_artifact_ingest_class_id_mismatch(
        self,
        mock_verify: MagicMock,
        mock_dynamo: MagicMock,
        mock_s3: MagicMock,
        mock_jwt_token: str,
        mock_user_educator: dict,
    ) -> None:
        """Test artifact ingestion with class_id mismatch"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_user_educator)

        # Mock artifact exists with different class_id
        test_artifact_id = uuid4()
        mock_dynamo.get_artifact_record.return_value = {
            "artifact_id": str(test_artifact_id),
            "artifact_key": "raw/dev/class456/2024-01-15/artifacts/essay.pdf",
            "class_id": "class456",
        }

        response = client.post(
            "/v1/ingest/artifacts",
            json={
                "artifact_id": str(test_artifact_id),
                "metadata": {
                    "class_id": "class123",  # Different from artifact's class_id
                    "date": "2024-01-15",
                    "student_id": "student1",
                    "artifact_type": "essay",
                },
            },
            headers={"Authorization": mock_jwt_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "class_id mismatch" in response.json()["detail"]

    def test_artifact_ingest_no_auth(self) -> None:
        """Test artifact ingestion without authentication"""
        response = client.post(
            "/v1/ingest/artifacts",
            json={
                "artifact_id": str(uuid4()),
                "metadata": {
                    "class_id": "class123",
                    "date": "2024-01-15",
                    "student_id": "student1",
                    "artifact_type": "essay",
                },
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
