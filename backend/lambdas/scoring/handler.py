"""Lambda function for NLP scoring

This Lambda processes normalized transcripts through the NLP pipeline
to generate skill scores and evidence for students.
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

import boto3

# Add parent directory to path to import app modules
# In production, package these as Lambda layers or include in deployment
sys.path.insert(0, "/opt/python")  # Lambda layer path

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
rds_client = boto3.client("rds-data")
sqs_client = boto3.client("sqs")

# Environment variables
JOBS_TABLE = os.environ["DYNAMODB_JOBS_TABLE"]
S3_NORMALIZED_BUCKET = os.environ["S3_NORMALIZED_BUCKET"]
S3_OUTPUTS_BUCKET = os.environ["S3_OUTPUTS_BUCKET"]
RDS_DATABASE_ARN = os.environ.get("RDS_DATABASE_ARN")
RDS_SECRET_ARN = os.environ.get("RDS_SECRET_ARN")
AGGREGATION_QUEUE_URL = os.environ.get("AGGREGATION_QUEUE_URL")


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


def load_normalized_transcript(s3_key: str) -> list[Dict[str, Any]]:
    """
    Load normalized transcript from S3.

    Args:
        s3_key: S3 key for normalized JSONL file

    Returns:
        List of transcript line dicts
    """
    logger.info(f"Loading transcript from {s3_key}")
    response = s3_client.get_object(Bucket=S3_NORMALIZED_BUCKET, Key=s3_key)
    content = response["Body"].read().decode("utf-8")

    lines = []
    for line in content.strip().split("\n"):
        if line:
            lines.append(json.loads(line))

    return lines


def score_transcript_simple(lines: list[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Simple scoring implementation without heavy NLP dependencies.

    This is a lightweight implementation for Lambda. In production,
    you would either:
    1. Use Lambda layers with NLP libraries
    2. Use ECS/EKS for heavier compute
    3. Pre-package models in the Lambda deployment

    Args:
        lines: Normalized transcript lines

    Returns:
        Scoring results with skill scores and evidence
    """
    # Simple keyword-based scoring for MVP
    skill_keywords = {
        "empathy": ["understand", "feel", "sorry", "care", "support"],
        "collaboration": ["together", "team", "cooperate", "work with"],
        "communication": ["explain", "clarify", "discuss", "share"],
        "adaptability": ["change", "adapt", "adjust", "flexible"],
        "self_regulation": ["calm", "control", "focus", "patient"],
    }

    # Group lines by speaker
    speakers = {}
    for line in lines:
        speaker = line.get("speaker", "Unknown")
        if speaker not in speakers:
            speakers[speaker] = []
        speakers[speaker].append(line)

    # Score each student
    results = {}
    for speaker, utterances in speakers.items():
        # Skip teacher utterances (simple heuristic)
        if "teacher" in speaker.lower():
            continue

        speaker_scores = {}
        speaker_evidence = {}

        # Combine all utterances for this speaker
        full_text = " ".join(utt.get("text", "") for utt in utterances).lower()

        for skill, keywords in skill_keywords.items():
            # Count keyword matches
            matches = sum(1 for kw in keywords if kw in full_text)

            # Calculate simple score
            score = min(matches * 0.15 + 0.3, 1.0) if matches > 0 else 0.0

            speaker_scores[skill] = {
                "score": round(score, 3),
                "confidence": round(min(0.6 + matches * 0.1, 0.9), 3),
                "demonstration_count": matches,
            }

            # Extract evidence (simple - just find lines with keywords)
            evidence = []
            for utt in utterances:
                utt_text = utt.get("text", "").lower()
                for kw in keywords:
                    if kw in utt_text:
                        evidence.append({
                            "line_number": utt.get("line_number"),
                            "text": utt.get("text"),
                            "keyword": kw,
                        })
                        break  # One evidence per line

            speaker_evidence[skill] = evidence[:3]  # Top 3

        results[speaker] = {
            "scores": speaker_scores,
            "evidence": speaker_evidence,
            "utterance_count": len(utterances),
        }

    return results


def store_assessment_results(
    job_id: str, class_id: str, date: str, scores: Dict[str, Any]
) -> list[str]:
    """
    Store assessment results to RDS and S3.

    Args:
        job_id: Job identifier
        class_id: Class identifier
        date: Assessment date
        scores: Scoring results

    Returns:
        List of output S3 keys
    """
    output_keys = []

    # Store detailed results to S3
    results_key = f"scores/{class_id}/{date}/{job_id}.json"
    s3_client.put_object(
        Bucket=S3_OUTPUTS_BUCKET,
        Key=results_key,
        Body=json.dumps(scores, indent=2).encode("utf-8"),
        ContentType="application/json",
    )
    output_keys.append(results_key)

    logger.info(f"Stored results to S3: {results_key}")

    # TODO: Store to RDS using RDS Data API
    # For MVP, we'll just store to S3
    # Production should insert into assessments and evidence tables

    return output_keys


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for NLP scoring.

    Expected event structure (from SQS):
    {
        "Records": [{
            "body": {
                "job_id": "uuid",
                "normalized_key": "s3_key_to_normalized_file",
                "class_id": "class_id",
                "date": "2024-01-15",
                "line_count": 100,
                "metadata": {...}
            }
        }]
    }

    Args:
        event: Lambda event dict (SQS event)
        context: Lambda context

    Returns:
        Response dict with scoring results
    """
    successful = []
    failed = []

    # Process each SQS message
    for record in event.get("Records", []):
        try:
            # Parse message body
            message = json.loads(record["body"])
            job_id = message["job_id"]
            normalized_key = message["normalized_key"]
            class_id = message["class_id"]
            date = message["date"]

            logger.info(f"Starting scoring for job {job_id}")

            # Update job status
            update_job_status(job_id, "scoring")

            # Load normalized transcript
            transcript_lines = load_normalized_transcript(normalized_key)
            logger.info(f"Loaded {len(transcript_lines)} transcript lines")

            # Score transcript
            logger.info("Running NLP scoring pipeline")
            scores = score_transcript_simple(transcript_lines)
            logger.info(f"Generated scores for {len(scores)} students")

            # Store results
            output_keys = store_assessment_results(job_id, class_id, date, scores)

            # Update job status
            update_job_status(
                job_id,
                "scored",
                output_keys=output_keys,
                scoring_metadata={
                    "student_count": len(scores),
                    "completed_at": datetime.utcnow().isoformat(),
                },
            )

            # Send to aggregation queue (if configured)
            if AGGREGATION_QUEUE_URL:
                aggregation_message = {
                    "job_id": job_id,
                    "class_id": class_id,
                    "date": date,
                    "scores_key": output_keys[0],
                    "student_count": len(scores),
                }
                sqs_client.send_message(
                    QueueUrl=AGGREGATION_QUEUE_URL,
                    MessageBody=json.dumps(aggregation_message),
                )
                logger.info(f"Sent job to aggregation queue")

            successful.append(job_id)
            logger.info(f"Scoring completed for job {job_id}")

        except Exception as e:
            logger.error(f"Scoring failed: {e}", exc_info=True)
            if "job_id" in message:
                update_job_status(message["job_id"], "failed", error=str(e))
                failed.append(message["job_id"])

    return {
        "statusCode": 200,
        "batchItemFailures": [
            {"itemIdentifier": record["messageId"]}
            for record in event.get("Records", [])
            if json.loads(record["body"]).get("job_id") in failed
        ],
        "successful": successful,
        "failed": failed,
    }
