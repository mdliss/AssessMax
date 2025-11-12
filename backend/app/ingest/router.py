"""FastAPI router for ingestion endpoints"""

import datetime as dt
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import TokenData, get_current_user, require_educator
from app.ingest.models import (
    ArtifactIngestRequest,
    ArtifactIngestResponse,
    PresignedUploadRequest,
    PresignedUploadResponse,
    TranscriptIngestRequest,
    TranscriptIngestResponse,
)
from app.ingest.storage import dynamodb_client, s3_client
from app.ingest.validators import FileValidator
from app.ingest.workflow import WorkflowError, trigger_transcript_workflow

router = APIRouter(prefix="/v1/ingest", tags=["Ingestion"])


@router.post(
    "/presigned-upload",
    response_model=PresignedUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def request_presigned_upload(
    request: PresignedUploadRequest,
    user: Annotated[TokenData, Depends(require_educator)],
) -> PresignedUploadResponse:
    """
    Request a presigned S3 upload URL for transcript or artifact upload.

    This endpoint follows the architecture pattern:
    1. Educator requests presigned URL
    2. Educator uploads file directly to S3 using presigned URL
    3. Educator calls /transcripts or /artifacts endpoint with artifact_id

    Flow:
    - Validates file size and format
    - Generates unique artifact_id
    - Creates S3 key following convention: raw/{env}/{class_id}/{date}/{type}/{artifact_id}_{filename}
    - Creates artifact record in DynamoDB
    - Generates presigned PUT URL (1 hour expiration)

    Requires: Educator or Admin role

    Args:
        request: Upload request with file details
        user: Authenticated user from JWT

    Returns:
        PresignedUploadResponse with upload URL and metadata

    Raises:
        HTTPException: 400 if validation fails, 500 if AWS operations fail
    """
    try:
        # Generate unique artifact ID
        artifact_id = uuid4()

        # Determine file type (transcripts vs artifacts)
        file_type = (
            "transcripts"
            if FileValidator.is_transcript_format(request.file_format)
            else "artifacts"
        )

        # Generate S3 key
        s3_key = s3_client.generate_s3_key(
            file_type=file_type,
            class_id=request.class_id,
            session_date=request.date,
            file_name=request.file_name,
            artifact_id=artifact_id,
        )

        # Get appropriate content type
        content_type = request.content_type
        if content_type == "application/octet-stream":
            content_type = FileValidator.get_content_type(request.file_format)

        # Generate presigned URL (1 hour expiration)
        upload_url = s3_client.generate_presigned_upload_url(
            s3_key=s3_key,
            content_type=content_type,
            expires_in=3600,
        )

        # Create artifact record in DynamoDB
        dynamodb_client.create_artifact_record(
            artifact_id=artifact_id,
            s3_key=s3_key,
            uploader_id=user.sub,
            class_id=request.class_id,
            content_type=content_type,
            file_size_bytes=request.file_size_bytes,
        )

        return PresignedUploadResponse(
            upload_url=upload_url,
            artifact_id=artifact_id,
            s3_key=s3_key,
            expires_at=dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1),
            upload_method="PUT",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate upload URL: {str(e)}",
        ) from e


@router.post(
    "/transcripts",
    response_model=TranscriptIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_transcript(
    request: TranscriptIngestRequest,
    user: Annotated[TokenData, Depends(require_educator)],
) -> TranscriptIngestResponse:
    """
    Process an uploaded transcript and trigger scoring pipeline.

    This endpoint should be called AFTER the file has been uploaded to S3
    using the presigned URL from /presigned-upload.

    Flow:
    1. Validates artifact exists in DynamoDB
    2. Verifies file exists in S3
    3. Creates job record in DynamoDB with status 'queued'
    4. (Future) Triggers Step Functions workflow for normalization and scoring

    Requires: Educator or Admin role

    Args:
        request: Transcript ingestion request with artifact_id and metadata
        user: Authenticated user from JWT

    Returns:
        TranscriptIngestResponse with job_id and status

    Raises:
        HTTPException: 404 if artifact not found, 400 if validation fails
    """
    try:
        # Get artifact record
        artifact = dynamodb_client.get_artifact_record(request.artifact_id)
        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact {request.artifact_id} not found",
            )

        # Verify artifact belongs to the correct class
        if artifact["class_id"] != request.metadata.class_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Artifact class_id mismatch: expected {request.metadata.class_id}, got {artifact['class_id']}",
            )

        # Verify file exists in S3
        s3_key = artifact["artifact_key"]
        if not s3_client.check_object_exists(s3_key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File not found in S3 at key: {s3_key}. Please upload the file first.",
            )

        # Update artifact status to uploaded
        dynamodb_client.update_artifact_status(request.artifact_id, "uploaded")

        # Create job record
        job_id = uuid4()
        job_metadata = {
            "source": request.metadata.source,
            "student_roster": request.metadata.student_roster,
            "uploader_id": user.sub,
            "uploader_name": user.display_name,
        }

        dynamodb_client.create_job_record(
            job_id=job_id,
            class_id=request.metadata.class_id,
            session_date=request.metadata.date,
            input_keys=[s3_key],
            metadata=job_metadata,
        )

        # Trigger Step Functions workflow
        try:
            # Determine file format from artifact
            file_format = artifact.get("content_type", "text/plain")
            if "csv" in file_format:
                format_type = "csv"
            elif "json" in file_format:
                format_type = "jsonl"
            else:
                format_type = "txt"

            execution_arn = trigger_transcript_workflow(
                job_id=job_id,
                artifact_id=request.artifact_id,
                s3_key=s3_key,
                class_id=request.metadata.class_id,
                session_date=request.metadata.date,
                file_format=format_type,
                metadata=job_metadata,
            )

            # Update job with execution ARN
            dynamodb_client.update_job_status(
                job_id, "processing", execution_arn=execution_arn
            )

            return TranscriptIngestResponse(
                job_id=job_id,
                artifact_id=request.artifact_id,
                status="processing",
                message=f"Transcript processing started. Job ID: {job_id}",
                class_id=request.metadata.class_id,
                date=request.metadata.date,
            )

        except WorkflowError as e:
            # Update job status to failed
            dynamodb_client.update_job_status(job_id, "failed", error=str(e))

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start processing workflow: {str(e)}",
            ) from e

    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process transcript: {str(e)}",
        ) from e


@router.post(
    "/artifacts",
    response_model=ArtifactIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_artifact(
    request: ArtifactIngestRequest,
    user: Annotated[TokenData, Depends(require_educator)],
) -> ArtifactIngestResponse:
    """
    Process an uploaded artifact and trigger scoring pipeline.

    This endpoint should be called AFTER the file has been uploaded to S3
    using the presigned URL from /presigned-upload.

    Flow:
    1. Validates artifact exists in DynamoDB
    2. Verifies file exists in S3
    3. Creates job record in DynamoDB with status 'queued'
    4. (Future) Triggers Step Functions workflow for artifact processing

    Requires: Educator or Admin role

    Args:
        request: Artifact ingestion request with artifact_id and metadata
        user: Authenticated user from JWT

    Returns:
        ArtifactIngestResponse with job_id and status

    Raises:
        HTTPException: 404 if artifact not found, 400 if validation fails
    """
    try:
        # Get artifact record
        artifact = dynamodb_client.get_artifact_record(request.artifact_id)
        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact {request.artifact_id} not found",
            )

        # Verify artifact belongs to the correct class
        if artifact["class_id"] != request.metadata.class_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Artifact class_id mismatch: expected {request.metadata.class_id}, got {artifact['class_id']}",
            )

        # Verify file exists in S3
        s3_key = artifact["artifact_key"]
        if not s3_client.check_object_exists(s3_key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File not found in S3 at key: {s3_key}. Please upload the file first.",
            )

        # Update artifact status to uploaded
        dynamodb_client.update_artifact_status(request.artifact_id, "uploaded")

        # Create job record
        job_id = uuid4()
        job_metadata = {
            "student_id": request.metadata.student_id,
            "artifact_type": request.metadata.artifact_type,
            "uploader_id": user.sub,
            "uploader_name": user.display_name,
        }

        dynamodb_client.create_job_record(
            job_id=job_id,
            class_id=request.metadata.class_id,
            session_date=request.metadata.date,
            input_keys=[s3_key],
            metadata=job_metadata,
        )

        # TODO: Trigger Step Functions workflow for artifact processing
        # await trigger_artifact_workflow(job_id)

        return ArtifactIngestResponse(
            job_id=job_id,
            artifact_id=request.artifact_id,
            status="queued",
            message=f"Artifact ingestion queued successfully. Job ID: {job_id}",
            class_id=request.metadata.class_id,
            student_id=request.metadata.student_id,
            date=request.metadata.date,
        )

    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process artifact: {str(e)}",
        ) from e


@router.get("/artifacts/{artifact_id}", tags=["Ingestion"])
async def get_artifact_status(
    artifact_id: str,
    user: Annotated[TokenData, Depends(get_current_user)],
) -> dict[str, str]:
    """
    Get status of an uploaded artifact.

    Requires: Valid authentication

    Args:
        artifact_id: Artifact UUID
        user: Authenticated user

    Returns:
        Artifact status information

    Raises:
        HTTPException: 404 if artifact not found
    """
    try:
        from uuid import UUID

        artifact_uuid = UUID(artifact_id)
        artifact = dynamodb_client.get_artifact_record(artifact_uuid)

        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact {artifact_id} not found",
            )

        return {
            "artifact_id": artifact["artifact_id"],
            "status": artifact["status"],
            "class_id": artifact["class_id"],
            "created_at": artifact["created_at"],
            "s3_key": artifact["artifact_key"],
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid artifact_id format",
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get artifact status: {str(e)}",
        ) from e
