"""Step Functions workflow client for triggering transcript processing"""

import json
import logging
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

import boto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)

# Lazy initialization of Step Functions client
_sfn_client = None


def get_sfn_client():
    """Get or create Step Functions client with proper configuration"""
    global _sfn_client
    if _sfn_client is None:
        _sfn_client = boto3.client("stepfunctions", region_name=settings.aws_region)
    return _sfn_client


class WorkflowError(Exception):
    """Base exception for workflow-related errors"""

    pass


def trigger_transcript_workflow(
    job_id: UUID,
    artifact_id: UUID,
    s3_key: str,
    class_id: str,
    session_date: str,
    file_format: str,
    metadata: Dict[str, Any] | None = None,
) -> str:
    """
    Trigger the transcript processing Step Functions workflow.

    Args:
        job_id: Unique job identifier
        artifact_id: Artifact identifier
        s3_key: S3 key where raw transcript is stored
        class_id: Class identifier
        session_date: Session date in ISO format
        file_format: File format (txt, csv, jsonl)
        metadata: Optional additional metadata

    Returns:
        Execution ARN of the started Step Functions execution

    Raises:
        WorkflowError: If workflow cannot be started
    """
    try:
        # Get state machine ARN from environment or construct it
        state_machine_name = f"{settings.environment}-TranscriptProcessing"
        account_id = boto3.client("sts").get_caller_identity()["Account"]
        region = settings.aws_region

        state_machine_arn = (
            f"arn:aws:states:{region}:{account_id}:stateMachine:{state_machine_name}"
        )

        # Prepare input for state machine
        execution_input = {
            "job_id": str(job_id),
            "artifact_id": str(artifact_id),
            "input_key": s3_key,
            "format": file_format,
            "class_id": class_id,
            "date": session_date,
            "metadata": metadata or {},
            "triggered_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Starting Step Functions execution for job {job_id}, state machine: {state_machine_name}"
        )

        # Start execution
        sfn_client = get_sfn_client()
        response = sfn_client.start_execution(
            stateMachineArn=state_machine_arn,
            name=f"job-{job_id}-{int(datetime.utcnow().timestamp())}",
            input=json.dumps(execution_input),
        )

        execution_arn = response["executionArn"]
        logger.info(f"Started Step Functions execution: {execution_arn}")

        return execution_arn

    except ClientError as e:
        error_msg = f"Failed to start Step Functions workflow: {e}"
        logger.error(error_msg, exc_info=True)
        raise WorkflowError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error starting workflow: {e}"
        logger.error(error_msg, exc_info=True)
        raise WorkflowError(error_msg) from e


def get_workflow_status(execution_arn: str) -> Dict[str, Any]:
    """
    Get the current status of a Step Functions execution.

    Args:
        execution_arn: ARN of the execution to check

    Returns:
        Dict containing execution status and details

    Raises:
        WorkflowError: If status cannot be retrieved
    """
    try:
        logger.info(f"Checking Step Functions execution status: {execution_arn}")

        sfn_client = get_sfn_client()
        response = sfn_client.describe_execution(executionArn=execution_arn)

        return {
            "execution_arn": response["executionArn"],
            "status": response["status"],
            "start_date": response["startDate"].isoformat(),
            "stop_date": response.get("stopDate", "").isoformat()
            if response.get("stopDate")
            else None,
            "output": json.loads(response.get("output", "{}"))
            if response.get("output")
            else None,
            "error": response.get("error"),
            "cause": response.get("cause"),
        }

    except ClientError as e:
        error_msg = f"Failed to get workflow status: {e}"
        logger.error(error_msg, exc_info=True)
        raise WorkflowError(error_msg) from e
