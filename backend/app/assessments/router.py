"""FastAPI router for assessment endpoints"""

import datetime as dt
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.assessments.models import (
    AssessmentHistoryResponse,
    AssessmentResponse,
    ClassDashboardResponse,
    ClassMetrics,
    EvidenceResponse,
    EvidenceSpan,
    SkillScore,
    StudentSummary,
)
from app.auth import TokenData, get_current_user
from app.database import get_db
from app.models.assessment import Assessment
from app.models.evidence import Evidence
from app.models.student import Student

router = APIRouter(tags=["Assessments"])

# Skill names from the Assessment model
SKILLS = ["empathy", "adaptability", "collaboration", "communication", "self_regulation"]


def assessment_to_response(assessment: Assessment) -> AssessmentResponse:
    """
    Convert Assessment ORM model to AssessmentResponse.

    Args:
        assessment: Assessment ORM instance

    Returns:
        AssessmentResponse model
    """
    skills = []
    for skill in SKILLS:
        score_value = getattr(assessment, skill)
        confidence_value = getattr(assessment, f"confidence_{skill}")

        if score_value is not None and confidence_value is not None:
            # Convert 0-10 scale to 0-100 for API response
            skills.append(
                SkillScore(
                    skill=skill,
                    score=float(score_value) * 10,
                    confidence=float(confidence_value),
                )
            )

    return AssessmentResponse(
        assessment_id=assessment.assessment_id,
        student_id=assessment.student_id,
        class_id=assessment.class_id,
        assessed_on=assessment.assessed_on,
        model_version=assessment.model_version,
        skills=skills,
        created_at=assessment.created_at,
    )


@router.get("/v1/assessments/{student_id}", response_model=AssessmentResponse)
async def get_latest_assessment(
    student_id: UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> AssessmentResponse:
    """
    Get the latest assessment for a student with skill scores and confidence levels.

    Returns the most recent assessment based on assessed_on date.

    Requires: Valid authentication

    Args:
        student_id: Student UUID
        user: Authenticated user
        db: Database session

    Returns:
        AssessmentResponse with latest skill scores

    Raises:
        HTTPException: 404 if student or assessment not found
    """
    try:
        # Check if student exists
        student_result = await db.execute(
            select(Student).where(Student.student_id == student_id)
        )
        student = student_result.scalar_one_or_none()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {student_id} not found",
            )

        # Get latest assessment
        assessment_result = await db.execute(
            select(Assessment)
            .where(Assessment.student_id == student_id)
            .order_by(Assessment.assessed_on.desc(), Assessment.created_at.desc())
            .limit(1)
        )
        assessment = assessment_result.scalar_one_or_none()

        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No assessments found for student {student_id}",
            )

        return assessment_to_response(assessment)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve assessment: {str(e)}",
        ) from e


@router.get("/v1/assessments/{student_id}/history", response_model=AssessmentHistoryResponse)
async def get_assessment_history(
    student_id: UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of assessments"),
    offset: int = Query(0, ge=0, description="Number of assessments to skip"),
) -> AssessmentHistoryResponse:
    """
    Get historical assessments for a student showing skill progression over time.

    Returns assessments ordered by date (most recent first).

    Requires: Valid authentication

    Args:
        student_id: Student UUID
        user: Authenticated user
        db: Database session
        limit: Maximum number of assessments to return
        offset: Number of assessments to skip (for pagination)

    Returns:
        AssessmentHistoryResponse with time-series data

    Raises:
        HTTPException: 404 if student not found
    """
    try:
        # Check if student exists
        student_result = await db.execute(
            select(Student).where(Student.student_id == student_id)
        )
        student = student_result.scalar_one_or_none()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {student_id} not found",
            )

        # Get total count
        count_result = await db.execute(
            select(func.count(Assessment.assessment_id)).where(
                Assessment.student_id == student_id
            )
        )
        total = count_result.scalar_one()

        # Get assessments with pagination
        assessments_result = await db.execute(
            select(Assessment)
            .where(Assessment.student_id == student_id)
            .order_by(Assessment.assessed_on.desc(), Assessment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        assessments = assessments_result.scalars().all()

        return AssessmentHistoryResponse(
            student_id=student_id,
            assessments=[assessment_to_response(a) for a in assessments],
            total=total,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve assessment history: {str(e)}",
        ) from e


@router.get("/v1/classes/{class_id}/dashboard", response_model=ClassDashboardResponse)
async def get_class_dashboard(
    class_id: str,
    user: Annotated[TokenData, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ClassDashboardResponse:
    """
    Get class dashboard with aggregated metrics and student summaries.

    Provides:
    - Class-level average scores by skill
    - Student count and assessment statistics
    - Individual student summaries with latest assessments

    Requires: Valid authentication

    Args:
        class_id: Class identifier
        user: Authenticated user
        db: Database session

    Returns:
        ClassDashboardResponse with class metrics and student data

    Raises:
        HTTPException: 404 if class not found, 500 if database error
    """
    try:
        # Get all students in class
        students_result = await db.execute(
            select(Student).where(Student.class_id == class_id)
        )
        students = students_result.scalars().all()

        if not students:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class {class_id} not found or has no students",
            )

        # Get all assessments for this class
        assessments_result = await db.execute(
            select(Assessment)
            .where(Assessment.class_id == class_id)
            .order_by(Assessment.assessed_on.desc())
        )
        all_assessments = assessments_result.scalars().all()

        # Calculate class metrics
        total_assessments = len(all_assessments)
        date_range = None
        if all_assessments:
            dates = [a.assessed_on for a in all_assessments]
            date_range = (min(dates), max(dates))

        # Calculate class averages
        class_averages = {}
        for skill in SKILLS:
            skill_scores = [
                float(getattr(a, skill)) * 10
                for a in all_assessments
                if getattr(a, skill) is not None
            ]
            if skill_scores:
                class_averages[skill] = sum(skill_scores) / len(skill_scores)

        metrics = ClassMetrics(
            class_id=class_id,
            student_count=len(students),
            total_assessments=total_assessments,
            date_range=date_range,
            class_averages=class_averages,
        )

        # Build student summaries
        student_summaries = []
        for student in students:
            # Get assessments for this student
            student_assessments = [
                a for a in all_assessments if a.student_id == student.student_id
            ]

            latest = None
            if student_assessments:
                latest = assessment_to_response(student_assessments[0])

            # Calculate average scores for this student
            avg_scores = {}
            for skill in SKILLS:
                skill_scores = [
                    float(getattr(a, skill)) * 10
                    for a in student_assessments
                    if getattr(a, skill) is not None
                ]
                if skill_scores:
                    avg_scores[skill] = sum(skill_scores) / len(skill_scores)

            student_summaries.append(
                StudentSummary(
                    student_id=student.student_id,
                    name=student.name,
                    latest_assessment=latest,
                    assessment_count=len(student_assessments),
                    average_scores=avg_scores,
                )
            )

        return ClassDashboardResponse(
            class_id=class_id,
            metrics=metrics,
            students=student_summaries,
            last_updated=dt.datetime.now(dt.timezone.utc),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve class dashboard: {str(e)}",
        ) from e


@router.get("/v1/evidence/{assessment_id}", response_model=EvidenceResponse)
async def get_assessment_evidence(
    assessment_id: UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> EvidenceResponse:
    """
    Get evidence spans, rationales, and citations for an assessment.

    Returns all evidence used to support skill scores, including:
    - Text spans from transcripts/artifacts
    - Location references (line numbers, page numbers)
    - Rationales explaining the evidence
    - Score contributions

    Requires: Valid authentication

    Args:
        assessment_id: Assessment UUID
        user: Authenticated user
        db: Database session

    Returns:
        EvidenceResponse with evidence spans and details

    Raises:
        HTTPException: 404 if assessment not found
    """
    try:
        # Check if assessment exists
        assessment_result = await db.execute(
            select(Assessment).where(Assessment.assessment_id == assessment_id)
        )
        assessment = assessment_result.scalar_one_or_none()

        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assessment {assessment_id} not found",
            )

        # Get all evidence for this assessment
        evidence_result = await db.execute(
            select(Evidence)
            .where(Evidence.assessment_id == assessment_id)
            .order_by(Evidence.skill, Evidence.score_contrib.desc())
        )
        evidence_list = evidence_result.scalars().all()

        evidence_spans = [
            EvidenceSpan(
                evidence_id=e.evidence_id,
                skill=e.skill,
                span_text=e.span_text,
                span_location=e.span_location,
                rationale=e.rationale,
                score_contribution=float(e.score_contrib) if e.score_contrib else None,
            )
            for e in evidence_list
        ]

        return EvidenceResponse(
            assessment_id=assessment_id,
            evidence_spans=evidence_spans,
            total=len(evidence_spans),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve evidence: {str(e)}",
        ) from e
