"""FastAPI router for job management endpoints"""

import datetime as dt
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import TokenData, get_current_user, require_admin
from app.ingest.storage import dynamodb_client
from app.jobs.models import JobListResponse, JobResponse, JobStatus, JobSummary

router = APIRouter(prefix="/v1/admin/jobs", tags=["Jobs"])


def parse_job_record(job: dict) -> JobResponse:
    """
    Parse DynamoDB job record into JobResponse.

    Args:
        job: Raw job record from DynamoDB

    Returns:
        JobResponse model
    """
    started_at = dt.datetime.fromisoformat(job["started_at"])
    ended_at = None
    duration_seconds = None

    if job.get("ended_at"):
        ended_at = dt.datetime.fromisoformat(job["ended_at"])
        duration_seconds = (ended_at - started_at).total_seconds()

    # Handle created_at which can be either timestamp (int/Decimal) or ISO string
    from decimal import Decimal

    created_at_raw = job.get("created_at", job["started_at"])
    if isinstance(created_at_raw, (int, float, Decimal)):
        # It's a timestamp
        created_at = dt.datetime.fromtimestamp(float(created_at_raw), tz=dt.timezone.utc)
    else:
        # It's an ISO string
        created_at = dt.datetime.fromisoformat(created_at_raw)

    return JobResponse(
        job_id=UUID(job["job_id"]),
        status=JobStatus(job["status"]),
        class_id=job["class_id"],
        date=dt.date.fromisoformat(job["date"]),
        input_keys=job.get("input_keys", []),
        output_keys=job.get("output_keys", []),
        error=job.get("error", ""),
        metadata=job.get("metadata", {}),
        started_at=started_at,
        ended_at=ended_at,
        created_at=created_at,
        duration_seconds=duration_seconds,
    )


def parse_job_summary(job: dict) -> JobSummary:
    """
    Parse DynamoDB job record into JobSummary.

    Args:
        job: Raw job record from DynamoDB

    Returns:
        JobSummary model
    """
    started_at = dt.datetime.fromisoformat(job["started_at"])
    ended_at = None

    if job.get("ended_at"):
        ended_at = dt.datetime.fromisoformat(job["ended_at"])

    return JobSummary(
        job_id=UUID(job["job_id"]),
        status=JobStatus(job["status"]),
        class_id=job["class_id"],
        date=dt.date.fromisoformat(job["date"]),
        started_at=started_at,
        ended_at=ended_at,
        error=job.get("error", ""),
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> JobResponse:
    """
    Get detailed status and information for a specific job.

    Returns comprehensive job details including:
    - Current processing status
    - Input and output S3 keys
    - Timestamps and duration
    - Error messages if failed
    - Additional metadata

    Requires: Valid authentication

    Args:
        job_id: Job UUID
        user: Authenticated user

    Returns:
        JobResponse with detailed job information

    Raises:
        HTTPException: 404 if job not found, 500 if DynamoDB error
    """
    try:
        job = dynamodb_client.get_job_record(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        return parse_job_record(job)

    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job: {str(e)}",
        ) from e


@router.get("", response_model=JobListResponse)
async def list_jobs(
    user: Annotated[TokenData, Depends(require_admin)],
    class_id: str | None = Query(None, description="Filter by class ID"),
    status_filter: JobStatus | None = Query(None, alias="status", description="Filter by job status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Jobs per page"),
) -> JobListResponse:
    """
    List all jobs with optional filtering and pagination.

    Admin-only endpoint for job monitoring and operations.

    Supports filtering by:
    - Class ID
    - Job status

    Requires: Admin role

    Args:
        user: Authenticated admin user
        class_id: Optional class ID filter
        status_filter: Optional status filter
        page: Page number (1-indexed)
        page_size: Number of jobs per page (max 100)

    Returns:
        JobListResponse with paginated job list

    Raises:
        HTTPException: 403 if not admin, 500 if DynamoDB error
    """
    try:
        # TODO: Implement efficient DynamoDB scanning/querying with filters
        # For MVP, we'll do a simple scan (not efficient for large datasets)
        # Production should use GSI on class_id and status

        table = dynamodb_client.jobs_table
        scan_kwargs = {}

        # Build filter expression
        filter_expressions = []
        expression_values = {}

        if class_id:
            filter_expressions.append("class_id = :class_id")
            expression_values[":class_id"] = class_id

        if status_filter:
            filter_expressions.append("#status = :status")
            expression_values[":status"] = status_filter.value
            if "ExpressionAttributeNames" not in scan_kwargs:
                scan_kwargs["ExpressionAttributeNames"] = {}
            scan_kwargs["ExpressionAttributeNames"]["#status"] = "status"

        if filter_expressions:
            scan_kwargs["FilterExpression"] = " AND ".join(filter_expressions)
            scan_kwargs["ExpressionAttributeValues"] = expression_values

        # Scan table (TODO: replace with query for better performance)
        response = table.scan(**scan_kwargs)
        all_jobs = response.get("Items", [])

        # Handle pagination tokens for large datasets
        while "LastEvaluatedKey" in response:
            scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            response = table.scan(**scan_kwargs)
            all_jobs.extend(response.get("Items", []))

        # Sort by started_at descending (most recent first)
        all_jobs.sort(key=lambda x: x.get("started_at", ""), reverse=True)

        # Apply pagination
        total = len(all_jobs)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_jobs = all_jobs[start_idx:end_idx]

        # Parse jobs
        job_summaries = [parse_job_summary(job) for job in page_jobs]

        return JobListResponse(
            jobs=job_summaries,
            total=total,
            page=page,
            page_size=page_size,
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}",
        ) from e
