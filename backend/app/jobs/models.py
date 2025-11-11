"""Pydantic models for job management endpoints"""

import datetime as dt
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job processing status"""

    QUEUED = "queued"
    RUNNING = "running"
    NORMALIZING = "normalizing"
    NORMALIZED = "normalized"
    SCORING = "scoring"
    SCORED = "scored"
    AGGREGATING = "aggregating"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobResponse(BaseModel):
    """Detailed job information response"""

    job_id: UUID = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    class_id: str = Field(..., description="Class identifier")
    date: dt.date = Field(..., description="Date of classroom session")
    input_keys: list[str] = Field(..., description="S3 keys for input files")
    output_keys: list[str] = Field(
        default_factory=list, description="S3 keys for output files"
    )
    error: str = Field(default="", description="Error message if failed")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional job metadata"
    )
    started_at: dt.datetime = Field(..., description="Job start time")
    ended_at: dt.datetime | None = Field(None, description="Job end time")
    created_at: dt.datetime = Field(..., description="Job creation time")
    duration_seconds: float | None = Field(
        None, description="Job duration in seconds (if completed)"
    )


class JobSummary(BaseModel):
    """Summary job information for list views"""

    job_id: UUID = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    class_id: str = Field(..., description="Class identifier")
    date: dt.date = Field(..., description="Date of classroom session")
    started_at: dt.datetime = Field(..., description="Job start time")
    ended_at: dt.datetime | None = Field(None, description="Job end time")
    error: str = Field(default="", description="Error message if failed")


class JobListResponse(BaseModel):
    """Response for job listing endpoint"""

    jobs: list[JobSummary] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of jobs per page")
