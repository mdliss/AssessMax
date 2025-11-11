"""Tests for assessments API endpoints"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.models.assessment import Assessment
from app.models.evidence import Evidence
from app.models.student import Student

client = TestClient(app)


@pytest.fixture
def mock_jwt_token() -> str:
    """Mock JWT token"""
    return "Bearer mock_token"


@pytest.fixture
def mock_user() -> dict:
    """Mock user data"""
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
def mock_student() -> Student:
    """Mock student"""
    student = Student(
        student_id=uuid4(),
        class_id="class123",
        name="Test Student",
        external_ref="student-ext-123",
    )
    student.created_at = datetime.now()
    return student


@pytest.fixture
def mock_assessment(mock_student: Student) -> Assessment:
    """Mock assessment"""
    assessment = Assessment(
        assessment_id=uuid4(),
        student_id=mock_student.student_id,
        class_id="class123",
        assessed_on=date(2024, 1, 15),
        model_version="v1.0",
        empathy=Decimal("8.5"),
        adaptability=Decimal("7.2"),
        collaboration=Decimal("9.0"),
        communication=Decimal("8.0"),
        self_regulation=Decimal("7.5"),
        confidence_empathy=Decimal("0.85"),
        confidence_adaptability=Decimal("0.72"),
        confidence_collaboration=Decimal("0.90"),
        confidence_communication=Decimal("0.80"),
        confidence_self_regulation=Decimal("0.75"),
    )
    assessment.created_at = datetime.now()
    return assessment


@pytest.fixture
def mock_evidence(mock_assessment: Assessment) -> Evidence:
    """Mock evidence"""
    evidence = Evidence(
        evidence_id=uuid4(),
        assessment_id=mock_assessment.assessment_id,
        skill="empathy",
        span_text="Student showed understanding of peer's feelings",
        span_location="line 42-45",
        rationale="Demonstrated empathetic response to classmate",
        score_contrib=Decimal("0.5"),
    )
    evidence.created_at = datetime.now()
    return evidence


class TestGetLatestAssessment:
    """Test GET /v1/assessments/{student_id} endpoint"""

    @patch("app.assessments.router.get_db")
    @patch("app.auth.dependencies.verify_jwt_token")
    def test_get_assessment_success(
        self,
        mock_verify: MagicMock,
        mock_get_db: AsyncMock,
        mock_jwt_token: str,
        mock_user: dict,
        mock_student: Student,
        mock_assessment: Assessment,
    ) -> None:
        """Test successful assessment retrieval"""
        from app.auth.models import TokenData

        mock_verify.return_value = TokenData(**mock_user)

        # Mock database session
        mock_db = AsyncMock()

        # Mock student query result
        student_result = MagicMock()
        student_result.scalar_one_or_none.return_value = mock_student

        # Mock assessment query result
        assessment_result = MagicMock()
        assessment_result.scalar_one_or_none.return_value = mock_assessment

        # Setup execute to return different results
        async def mock_execute(query):
            # Simplified - in reality would need to check query type
            if hasattr(query, '_whereclause'):
                # This is a simplification for testing
                return assessment_result if mock_assessment else student_result
            return student_result

        mock_db.execute = mock_execute
        mock_get_db.return_value = mock_db

        response = client.get(
            f"/v1/assessments/{mock_student.student_id}",
            headers={"Authorization": mock_jwt_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "assessment_id" in data
        assert "skills" in data
        assert len(data["skills"]) == 5

    @patch("app.auth.dependencies.verify_jwt_token")
    def test_get_assessment_no_auth(
        self,
        mock_verify: MagicMock,
        mock_student: Student,
    ) -> None:
        """Test without authentication"""
        response = client.get(f"/v1/assessments/{mock_student.student_id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetAssessmentHistory:
    """Test GET /v1/assessments/{student_id}/history endpoint"""

    @patch("app.auth.dependencies.verify_jwt_token")
    def test_get_history_no_auth(
        self,
        mock_verify: MagicMock,
        mock_student: Student,
    ) -> None:
        """Test without authentication"""
        response = client.get(f"/v1/assessments/{mock_student.student_id}/history")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetClassDashboard:
    """Test GET /v1/classes/{class_id}/dashboard endpoint"""

    @patch("app.auth.dependencies.verify_jwt_token")
    def test_get_dashboard_no_auth(self, mock_verify: MagicMock) -> None:
        """Test without authentication"""
        response = client.get("/v1/classes/class123/dashboard")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetEvidence:
    """Test GET /v1/evidence/{assessment_id} endpoint"""

    @patch("app.auth.dependencies.verify_jwt_token")
    def test_get_evidence_no_auth(
        self,
        mock_verify: MagicMock,
        mock_assessment: Assessment,
    ) -> None:
        """Test without authentication"""
        response = client.get(f"/v1/evidence/{mock_assessment.assessment_id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestSkillScoreConversion:
    """Test skill score conversion from 0-10 to 0-100"""

    def test_score_conversion(self) -> None:
        """Test that scores are properly converted"""
        from app.assessments.router import assessment_to_response
        from datetime import datetime

        assessment = Assessment(
            assessment_id=uuid4(),
            student_id=uuid4(),
            class_id="class123",
            assessed_on=date(2024, 1, 15),
            model_version="v1.0",
            empathy=Decimal("8.5"),  # Should become 85.0
            adaptability=None,  # Should be skipped
            collaboration=Decimal("10.0"),  # Should become 100.0
            communication=Decimal("0.0"),  # Should become 0.0
            self_regulation=Decimal("5.0"),  # Should become 50.0
            confidence_empathy=Decimal("0.85"),
            confidence_adaptability=None,
            confidence_collaboration=Decimal("1.0"),
            confidence_communication=Decimal("0.0"),
            confidence_self_regulation=Decimal("0.5"),
        )
        assessment.created_at = datetime.now()

        response = assessment_to_response(assessment)

        # Check score conversion
        skill_dict = {s.skill: s.score for s in response.skills}
        assert skill_dict["empathy"] == 85.0
        assert skill_dict["collaboration"] == 100.0
        assert skill_dict["communication"] == 0.0
        assert skill_dict["self_regulation"] == 50.0
        assert "adaptability" not in skill_dict  # Should be skipped due to None values
