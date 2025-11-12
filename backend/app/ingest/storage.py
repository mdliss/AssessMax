"""Storage operations for S3 and DynamoDB"""

import datetime as dt
import hashlib
from typing import Any
from uuid import UUID, uuid4

import boto3
from botocore.exceptions import ClientError

from app.config import settings


class S3Client:
    """S3 client for file storage and presigned URLs"""

    def __init__(self) -> None:
        self.client = boto3.client("s3", region_name=settings.aws_region)
        self.raw_bucket = settings.s3_bucket_raw
        self.normalized_bucket = settings.s3_bucket_normalized
        self.outputs_bucket = settings.s3_bucket_outputs

    def generate_s3_key(
        self,
        file_type: str,
        class_id: str,
        session_date: dt.date,
        file_name: str,
        artifact_id: UUID,
    ) -> str:
        """
        Generate S3 key following the architecture pattern:
        raw/{env}/{class_id}/{date}/{file_type}/{artifact_id}_{filename}

        Args:
            file_type: Type of file ('transcripts' or 'artifacts')
            class_id: Class identifier
            session_date: Date of classroom session
            file_name: Original file name
            artifact_id: Unique artifact identifier

        Returns:
            S3 object key
        """
        env = "dev"  # TODO: Make this configurable based on environment
        date_str = session_date.strftime("%Y-%m-%d")
        safe_filename = file_name.replace(" ", "_")
        return f"raw/{env}/{class_id}/{date_str}/{file_type}/{artifact_id}_{safe_filename}"

    def generate_presigned_upload_url(
        self,
        s3_key: str,
        content_type: str,
        expires_in: int = 3600,
    ) -> str:
        """
        Generate presigned URL for S3 PUT upload.

        Args:
            s3_key: S3 object key
            content_type: MIME type of the file
            expires_in: URL expiration time in seconds (default 1 hour)

        Returns:
            Presigned upload URL

        Raises:
            ClientError: If S3 operation fails
        """
        try:
            url = self.client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": self.raw_bucket,
                    "Key": s3_key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            raise RuntimeError(f"Failed to generate presigned URL: {e}") from e

    def check_object_exists(self, s3_key: str) -> bool:
        """
        Check if an object exists in S3.

        Args:
            s3_key: S3 object key

        Returns:
            True if object exists, False otherwise
        """
        try:
            self.client.head_object(Bucket=self.raw_bucket, Key=s3_key)
            return True
        except ClientError:
            return False

    def get_object_metadata(self, s3_key: str) -> dict[str, Any]:
        """
        Get metadata for an S3 object.

        Args:
            s3_key: S3 object key

        Returns:
            Object metadata

        Raises:
            ClientError: If object doesn't exist or operation fails
        """
        try:
            response = self.client.head_object(Bucket=self.raw_bucket, Key=s3_key)
            return {
                "content_type": response.get("ContentType"),
                "content_length": response.get("ContentLength"),
                "last_modified": response.get("LastModified"),
                "etag": response.get("ETag"),
            }
        except ClientError as e:
            raise RuntimeError(f"Failed to get object metadata: {e}") from e


class DynamoDBClient:
    """DynamoDB client for artifacts and jobs metadata"""

    def __init__(self) -> None:
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        self.artifacts_table = self.dynamodb.Table(settings.dynamodb_artifacts_table)
        self.jobs_table = self.dynamodb.Table(settings.dynamodb_jobs_table)

    def create_artifact_record(
        self,
        artifact_id: UUID,
        s3_key: str,
        uploader_id: str,
        class_id: str,
        content_type: str,
        file_size_bytes: int,
        sha256_hash: str | None = None,
    ) -> dict[str, Any]:
        """
        Create artifact record in DynamoDB.

        Args:
            artifact_id: Unique artifact identifier
            s3_key: S3 object key
            uploader_id: User ID of uploader
            class_id: Class identifier
            content_type: MIME type
            file_size_bytes: File size in bytes
            sha256_hash: Optional SHA256 hash of file content

        Returns:
            Created artifact record
        """
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        artifact = {
            "artifact_id": str(artifact_id),
            "artifact_key": s3_key,  # Using s3_key as artifact_key per schema
            "uploader_id": uploader_id,
            "class_id": class_id,
            "content_type": content_type,
            "file_size_bytes": file_size_bytes,
            "sha256": sha256_hash or "",
            "created_at": now,
            "status": "pending_upload",
        }

        try:
            self.artifacts_table.put_item(Item=artifact)
            return artifact
        except ClientError as e:
            raise RuntimeError(f"Failed to create artifact record: {e}") from e

    def get_artifact_record(self, artifact_id: UUID) -> dict[str, Any] | None:
        """
        Get artifact record from DynamoDB.

        Args:
            artifact_id: Artifact identifier

        Returns:
            Artifact record or None if not found
        """
        try:
            response = self.artifacts_table.get_item(Key={"artifact_id": str(artifact_id)})
            return response.get("Item")
        except ClientError as e:
            raise RuntimeError(f"Failed to get artifact record: {e}") from e

    def update_artifact_status(self, artifact_id: UUID, status: str) -> None:
        """
        Update artifact status.

        Args:
            artifact_id: Artifact identifier
            status: New status
        """
        try:
            self.artifacts_table.update_item(
                Key={"artifact_id": str(artifact_id)},
                UpdateExpression="SET #status = :status, updated_at = :updated_at",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": status,
                    ":updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                },
            )
        except ClientError as e:
            raise RuntimeError(f"Failed to update artifact status: {e}") from e

    def create_job_record(
        self,
        job_id: UUID,
        class_id: str,
        session_date: dt.date,
        input_keys: list[str],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Create job record in DynamoDB.

        Args:
            job_id: Unique job identifier
            class_id: Class identifier
            session_date: Date of classroom session
            input_keys: List of S3 keys for input files
            metadata: Additional job metadata

        Returns:
            Created job record
        """
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        job = {
            "job_id": str(job_id),
            "status": "queued",
            "class_id": class_id,
            "date": session_date.isoformat(),
            "input_keys": input_keys,
            "output_keys": [],
            "error": "",
            "metadata": metadata,
            "started_at": now,
            "ended_at": "",
            "created_at": now,
        }

        try:
            self.jobs_table.put_item(Item=job)
            return job
        except ClientError as e:
            raise RuntimeError(f"Failed to create job record: {e}") from e

    def get_job_record(self, job_id: UUID) -> dict[str, Any] | None:
        """
        Get job record from DynamoDB.

        Args:
            job_id: Job identifier

        Returns:
            Job record or None if not found
        """
        try:
            response = self.jobs_table.get_item(Key={"job_id": str(job_id)})
            return response.get("Item")
        except ClientError as e:
            raise RuntimeError(f"Failed to get job record: {e}") from e

    def update_job_status(
        self,
        job_id: UUID,
        status: str,
        error: str = "",
        output_keys: list[str] | None = None,
        execution_arn: str = "",
    ) -> None:
        """
        Update job status.

        Args:
            job_id: Job identifier
            status: New status
            error: Error message if failed
            output_keys: List of output S3 keys if succeeded
            execution_arn: Step Functions execution ARN
        """
        update_expr = "SET #status = :status, updated_at = :updated_at"
        expr_values: dict[str, Any] = {
            ":status": status,
            ":updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        expr_names = {"#status": "status"}

        if error:
            update_expr += ", error = :error"
            expr_values[":error"] = error

        if output_keys:
            update_expr += ", output_keys = :output_keys"
            expr_values[":output_keys"] = output_keys

        if execution_arn:
            update_expr += ", execution_arn = :execution_arn"
            expr_values[":execution_arn"] = execution_arn

        if status in ["succeeded", "failed", "cancelled"]:
            update_expr += ", ended_at = :ended_at"
            expr_values[":ended_at"] = dt.datetime.now(dt.timezone.utc).isoformat()

        try:
            self.jobs_table.update_item(
                Key={"job_id": str(job_id)},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values,
            )
        except ClientError as e:
            raise RuntimeError(f"Failed to update job status: {e}") from e


# Global client instances
s3_client = S3Client()
dynamodb_client = DynamoDBClient()
