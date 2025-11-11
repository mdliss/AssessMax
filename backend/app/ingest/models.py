"""Pydantic models for ingestion endpoints"""

import datetime as dt
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class FileFormat(str, Enum):
    """Supported file formats for transcript ingestion"""

    JSONL = "jsonl"
    CSV = "csv"
    TXT = "txt"
    PDF = "pdf"
    DOCX = "docx"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"


class IngestMetadata(BaseModel):
    """Metadata required for transcript ingestion"""

    class_id: str = Field(
        ...,
        description="Unique identifier for the class",
        min_length=1,
        max_length=100,
    )
    date: dt.date = Field(
        ...,
        description="Date of the classroom session",
    )
    student_roster: list[str] = Field(
        ...,
        description="List of student identifiers",
        min_length=1,
    )
    source: str = Field(
        ...,
        description="Source of the transcript (e.g., 'Zoom', 'Google Meet', 'manual')",
        min_length=1,
        max_length=100,
    )


class PresignedUploadRequest(BaseModel):
    """Request for presigned S3 upload URL"""

    file_name: str = Field(
        ...,
        description="Name of the file to upload",
        min_length=1,
        max_length=255,
    )
    file_format: FileFormat = Field(
        ...,
        description="Format of the file",
    )
    file_size_bytes: int = Field(
        ...,
        description="Size of file in bytes",
        ge=1,
    )
    class_id: str = Field(
        ...,
        description="Class identifier",
        min_length=1,
        max_length=100,
    )
    date: dt.date = Field(
        ...,
        description="Date of the classroom session",
    )
    content_type: str = Field(
        default="application/octet-stream",
        description="MIME type of the file",
    )

    @field_validator("file_size_bytes")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        """Validate file size is within limits (50MB for MVP)"""
        max_size = 50 * 1024 * 1024  # 50MB in bytes
        if v > max_size:
            raise ValueError(f"File size {v} bytes exceeds maximum of {max_size} bytes (50MB)")
        return v

    @field_validator("file_format")
    @classmethod
    def validate_file_format_matches_name(cls, v: FileFormat, info: Any) -> FileFormat:
        """Ensure file format matches file extension"""
        if info.data.get("file_name"):
            file_name = info.data["file_name"]
            ext = file_name.rsplit(".", 1)[-1].lower()
            if ext != v.value and not (v in [FileFormat.JPG, FileFormat.JPEG] and ext in ["jpg", "jpeg"]):
                raise ValueError(
                    f"File extension '.{ext}' does not match format '{v.value}'"
                )
        return v


class PresignedUploadResponse(BaseModel):
    """Response containing presigned upload URL and metadata"""

    upload_url: str = Field(
        ...,
        description="Presigned S3 URL for file upload (PUT request)",
    )
    artifact_id: UUID = Field(
        ...,
        description="Unique identifier for this artifact",
    )
    s3_key: str = Field(
        ...,
        description="S3 object key where file will be stored",
    )
    expires_at: dt.datetime = Field(
        ...,
        description="Expiration time for the presigned URL",
    )
    upload_method: str = Field(
        default="PUT",
        description="HTTP method to use for upload",
    )


class TranscriptIngestRequest(BaseModel):
    """Request to process an uploaded transcript"""

    artifact_id: UUID = Field(
        ...,
        description="Artifact ID from presigned upload",
    )
    metadata: IngestMetadata = Field(
        ...,
        description="Required metadata for transcript processing",
    )


class TranscriptIngestResponse(BaseModel):
    """Response from transcript ingestion"""

    job_id: UUID = Field(
        ...,
        description="Unique identifier for the processing job",
    )
    artifact_id: UUID = Field(
        ...,
        description="Artifact identifier",
    )
    status: str = Field(
        ...,
        description="Initial job status (typically 'queued')",
    )
    message: str = Field(
        ...,
        description="Human-readable status message",
    )
    class_id: str = Field(
        ...,
        description="Class identifier",
    )
    date: dt.date = Field(
        ...,
        description="Date of classroom session",
    )


class ArtifactMetadata(BaseModel):
    """Metadata required for artifact ingestion"""

    class_id: str = Field(
        ...,
        description="Unique identifier for the class",
        min_length=1,
        max_length=100,
    )
    date: dt.date = Field(
        ...,
        description="Date of the classroom session",
    )
    student_id: str = Field(
        ...,
        description="Student identifier who created the artifact",
        min_length=1,
        max_length=100,
    )
    artifact_type: str = Field(
        ...,
        description="Type of artifact (e.g., 'essay', 'project', 'presentation')",
        min_length=1,
        max_length=50,
    )


class ArtifactIngestRequest(BaseModel):
    """Request to process an uploaded artifact"""

    artifact_id: UUID = Field(
        ...,
        description="Artifact ID from presigned upload",
    )
    metadata: ArtifactMetadata = Field(
        ...,
        description="Required metadata for artifact processing",
    )


class ArtifactIngestResponse(BaseModel):
    """Response from artifact ingestion"""

    job_id: UUID = Field(
        ...,
        description="Unique identifier for the processing job",
    )
    artifact_id: UUID = Field(
        ...,
        description="Artifact identifier",
    )
    status: str = Field(
        ...,
        description="Initial job status (typically 'queued')",
    )
    message: str = Field(
        ...,
        description="Human-readable status message",
    )
    class_id: str = Field(
        ...,
        description="Class identifier",
    )
    student_id: str = Field(
        ...,
        description="Student identifier",
    )
    date: dt.date = Field(
        ...,
        description="Date of classroom session",
    )
