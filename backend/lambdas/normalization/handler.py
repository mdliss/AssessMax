"""Lambda function for transcript normalization"""

import json
import logging
import os
from typing import Any, Dict
from uuid import UUID

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
sqs_client = boto3.client("sqs")

# Environment variables
JOBS_TABLE = os.environ["DYNAMODB_JOBS_TABLE"]
S3_RAW_BUCKET = os.environ["S3_RAW_BUCKET"]
S3_NORMALIZED_BUCKET = os.environ["S3_NORMALIZED_BUCKET"]
SCORING_QUEUE_URL = os.environ["SCORING_QUEUE_URL"]


def update_job_status(job_id: str, status: str, **kwargs) -> None:
    """
    Update job status in DynamoDB.

    Args:
        job_id: Job identifier
        status: New status
        **kwargs: Additional attributes to update
    """
    table = dynamodb.Table(JOBS_TABLE)

    update_expr = "SET #status = :status"
    expr_attr_names = {"#status": "status"}
    expr_attr_values = {":status": status}

    for key, value in kwargs.items():
        update_expr += f", {key} = :{key}"
        expr_attr_values[f":{key}"] = value

    table.update_item(
        Key={"job_id": job_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values,
    )


def normalize_transcript(raw_text: str, format_type: str) -> Dict[str, Any]:
    """
    Normalize a transcript to canonical JSONL format.

    Args:
        raw_text: Raw transcript text
        format_type: Input format (txt, csv, jsonl)

    Returns:
        Normalized transcript dict with:
        - lines: List of utterances
        - metadata: Processing metadata
        - validation: Validation results
    """
    normalized_lines = []
    warnings = []

    if format_type == "txt":
        # Parse text format: "Speaker: utterance"
        lines = raw_text.strip().split("\n")
        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue

            # Try to parse speaker and text
            if ":" in line:
                parts = line.split(":", 1)
                speaker = parts[0].strip()
                text = parts[1].strip()

                normalized_lines.append({
                    "line_number": line_num,
                    "speaker": speaker,
                    "text": text,
                    "timestamp": None,
                })
            else:
                warnings.append(f"Line {line_num}: Could not parse speaker")

    elif format_type == "csv":
        # Parse CSV format
        # Expected: speaker,text,timestamp (optional)
        import csv
        from io import StringIO

        reader = csv.DictReader(StringIO(raw_text))
        for line_num, row in enumerate(reader, start=1):
            if "speaker" in row and "text" in row:
                normalized_lines.append({
                    "line_number": line_num,
                    "speaker": row["speaker"].strip(),
                    "text": row["text"].strip(),
                    "timestamp": row.get("timestamp"),
                })
            else:
                warnings.append(f"Line {line_num}: Missing required fields")

    elif format_type == "jsonl":
        # Parse JSONL format
        lines = raw_text.strip().split("\n")
        for line_num, line in enumerate(lines, start=1):
            try:
                data = json.loads(line)
                normalized_lines.append({
                    "line_number": line_num,
                    "speaker": data.get("speaker", "Unknown"),
                    "text": data.get("text", ""),
                    "timestamp": data.get("timestamp"),
                })
            except json.JSONDecodeError:
                warnings.append(f"Line {line_num}: Invalid JSON")

    return {
        "lines": normalized_lines,
        "metadata": {
            "total_lines": len(normalized_lines),
            "format": format_type,
            "validation_warnings": warnings,
        },
        "validation": {
            "is_valid": len(normalized_lines) > 0,
            "warning_count": len(warnings),
            "warnings": warnings[:10],  # Limit warnings
        },
    }


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for transcript normalization.

    Expected event structure:
    {
        "job_id": "uuid",
        "input_key": "s3_key_to_raw_file",
        "format": "txt|csv|jsonl",
        "class_id": "class_id",
        "date": "2024-01-15",
        "metadata": {...}
    }

    Args:
        event: Lambda event dict
        context: Lambda context

    Returns:
        Response dict with normalized file location
    """
    try:
        job_id = event["job_id"]
        input_key = event["input_key"]
        format_type = event.get("format", "txt")
        class_id = event["class_id"]
        date = event["date"]

        logger.info(f"Starting normalization for job {job_id}, input: {input_key}")

        # Update job status
        update_job_status(job_id, "normalizing")

        # Download raw file from S3
        logger.info(f"Downloading {input_key} from {S3_RAW_BUCKET}")
        response = s3_client.get_object(Bucket=S3_RAW_BUCKET, Key=input_key)
        raw_text = response["Body"].read().decode("utf-8")

        # Normalize transcript
        logger.info(f"Normalizing transcript, format: {format_type}")
        normalized = normalize_transcript(raw_text, format_type)

        # Generate output key
        output_key = f"normalized/{class_id}/{date}/{job_id}.jsonl"

        # Convert to JSONL format
        jsonl_output = "\n".join(json.dumps(line) for line in normalized["lines"])

        # Upload normalized file to S3
        logger.info(f"Uploading normalized file to {output_key}")
        s3_client.put_object(
            Bucket=S3_NORMALIZED_BUCKET,
            Key=output_key,
            Body=jsonl_output.encode("utf-8"),
            ContentType="application/jsonlines",
        )

        # Update job status
        update_job_status(
            job_id,
            "normalized",
            output_keys=[output_key],
            normalization_metadata=normalized["metadata"],
        )

        # Send message to scoring queue
        scoring_message = {
            "job_id": job_id,
            "normalized_key": output_key,
            "class_id": class_id,
            "date": date,
            "line_count": len(normalized["lines"]),
            "metadata": event.get("metadata", {}),
        }

        logger.info(f"Sending job to scoring queue: {SCORING_QUEUE_URL}")
        sqs_client.send_message(
            QueueUrl=SCORING_QUEUE_URL,
            MessageBody=json.dumps(scoring_message),
        )

        logger.info(f"Normalization completed for job {job_id}")

        return {
            "statusCode": 200,
            "job_id": job_id,
            "status": "normalized",
            "normalized_key": output_key,
            "line_count": len(normalized["lines"]),
            "warnings": normalized["validation"]["warnings"],
        }

    except KeyError as e:
        logger.error(f"Missing required field: {e}")
        if "job_id" in event:
            update_job_status(
                event["job_id"], "failed", error=f"Missing required field: {e}"
            )
        return {"statusCode": 400, "error": f"Missing required field: {str(e)}"}

    except Exception as e:
        logger.error(f"Normalization failed: {e}", exc_info=True)
        if "job_id" in event:
            update_job_status(event["job_id"], "failed", error=str(e))
        return {"statusCode": 500, "error": str(e)}
