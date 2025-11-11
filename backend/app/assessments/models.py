"""Pydantic models for assessment endpoints"""

import datetime as dt
from uuid import UUID

from pydantic import BaseModel, Field


class SkillScore(BaseModel):
    """Individual skill score with confidence"""

    skill: str = Field(..., description="Skill name")
    score: float = Field(..., description="Skill score (0-100)", ge=0, le=100)
    confidence: float = Field(..., description="Confidence level (0-1)", ge=0, le=1)


class AssessmentResponse(BaseModel):
    """Student assessment response with skill scores"""

    assessment_id: UUID = Field(..., description="Unique assessment identifier")
    student_id: UUID = Field(..., description="Student identifier")
    class_id: str = Field(..., description="Class identifier")
    assessed_on: dt.date = Field(..., description="Assessment date")
    model_version: str = Field(..., description="NLP model version used")
    skills: list[SkillScore] = Field(..., description="Skill scores and confidences")
    created_at: dt.datetime = Field(..., description="Record creation timestamp")


class AssessmentHistoryResponse(BaseModel):
    """Historical assessments for a student"""

    student_id: UUID = Field(..., description="Student identifier")
    assessments: list[AssessmentResponse] = Field(..., description="List of assessments")
    total: int = Field(..., description="Total number of assessments")


class EvidenceSpan(BaseModel):
    """Evidence span with location and rationale"""

    evidence_id: UUID = Field(..., description="Evidence identifier")
    skill: str = Field(..., description="Skill this evidence supports")
    span_text: str = Field(..., description="Text span from transcript/artifact")
    span_location: str = Field(
        ..., description="Location reference (e.g., 'line 42', 'page 3')"
    )
    rationale: str = Field(..., description="Explanation of why this is evidence")
    score_contribution: float | None = Field(
        None, description="Contribution to overall score"
    )


class EvidenceResponse(BaseModel):
    """Evidence details for an assessment"""

    assessment_id: UUID = Field(..., description="Assessment identifier")
    evidence_spans: list[EvidenceSpan] = Field(..., description="List of evidence spans")
    total: int = Field(..., description="Total number of evidence spans")


class StudentSummary(BaseModel):
    """Student summary for class dashboard"""

    student_id: UUID = Field(..., description="Student identifier")
    name: str | None = Field(None, description="Student name (if available)")
    latest_assessment: AssessmentResponse | None = Field(
        None, description="Most recent assessment"
    )
    assessment_count: int = Field(0, description="Total number of assessments")
    average_scores: dict[str, float] = Field(
        default_factory=dict, description="Average scores by skill"
    )


class ClassMetrics(BaseModel):
    """Aggregated metrics for a class"""

    class_id: str = Field(..., description="Class identifier")
    student_count: int = Field(..., description="Number of students")
    total_assessments: int = Field(..., description="Total assessments across all students")
    date_range: tuple[dt.date, dt.date] | None = Field(
        None, description="Date range of assessments (start, end)"
    )
    class_averages: dict[str, float] = Field(
        default_factory=dict, description="Class average scores by skill"
    )


class ClassDashboardResponse(BaseModel):
    """Class dashboard with student summaries and metrics"""

    class_id: str = Field(..., description="Class identifier")
    metrics: ClassMetrics = Field(..., description="Class-level metrics")
    students: list[StudentSummary] = Field(..., description="Student summaries")
    last_updated: dt.datetime = Field(..., description="Last data update timestamp")
