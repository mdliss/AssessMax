"""Lambda function for NLP scoring

This Lambda processes normalized transcripts through the NLP pipeline
to generate skill scores and evidence for students.
"""

import json
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, date
from typing import Any, Dict

import boto3

# Add parent directory to path to import app modules
# In production, package these as Lambda layers or include in deployment
sys.path.insert(0, "/opt/python")  # Lambda layer path

# Local development fallback so tests can import app modules
LOCAL_APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if LOCAL_APP_PATH not in sys.path:
    sys.path.insert(0, LOCAL_APP_PATH)

from app.nlp.llm_evidence_extractor import LLMEvidenceExtractor
from lambdas.common.persistence import PersistenceSummary, persist_llm_results

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
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
MODEL_VERSION = os.environ.get("LLM_MODEL_VERSION", "llm-1.0.0")
DATABASE_URL = os.environ.get("DATABASE_URL")


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


def score_transcript_with_llm(
    lines: list[Dict[str, Any]],
    extractor: LLMEvidenceExtractor,
) -> Dict[str, Any]:
    """
    Use the LLM evidence extractor to generate SEL scores and evidence.

    Args:
        lines: Normalized transcript lines
        extractor: Initialized LLMEvidenceExtractor

    Returns:
        Dict[str, Any]: Mapping of student_id -> analysis results
    """
    if not lines:
        return {}

    # Build transcript text sent to the model (preserve speaker context)
    transcript_text = "\n".join(
        f"{line.get('speaker', 'Unknown')}: {line.get('text', '')}"
        for line in lines
        if line.get("text")
    )

    # Organize utterances per student
    student_utterances: dict[str, list[Dict[str, Any]]] = defaultdict(list)
    student_names: dict[str, str] = {}
    student_external: dict[str, str | None] = {}

    for line in lines:
        student_id_value = line.get("student_id")
        if not student_id_value:
            continue

        student_id = str(student_id_value)

        student_utterances[student_id].append(line)
        student_names.setdefault(student_id, line.get("speaker", "Unknown"))
        if line.get("student_external_id"):
            student_external.setdefault(student_id, str(line["student_external_id"]))

    results: Dict[str, Any] = {}

    for student_id, utterances in student_utterances.items():
        student_name = student_names.get(student_id, f"Student {student_id}")

        logger.info(
            "Extracting SEL evidence for student %s (%s) with %s utterances",
            student_name,
            student_id,
            len(utterances),
        )

        evidence_dict, scores_dict = extractor.extract_and_score_student(
            transcript_text,
            student_name,
        )

        # Convert evidence dataclasses into plain dicts for serialization
        serialized_evidence: dict[str, list[dict[str, Any]]] = {}
        for skill, evidence_items in evidence_dict.items():
            serialized_evidence[skill] = [
                {
                    "quote": item.quote,
                    "rationale": item.rationale,
                    "score_contribution": item.score_contribution,
                    "confidence": item.confidence,
                }
                for item in evidence_items
            ]

        results[student_id] = {
            "student_id": student_id,
            "student_name": student_name,
            "student_external_id": student_external.get(student_id),
            "scores": scores_dict,
            "evidence": serialized_evidence,
            "utterance_count": len(utterances),
            "words_spoken": sum(
                len((utt.get("text") or "").split()) for utt in utterances
            ),
        }

    return results


def store_assessment_results(
    job_id: str,
    class_id: str,
    date: str,
    analysis: Dict[str, Any],
    metadata: Dict[str, Any] | None = None,
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
    payload = {
        "job_id": job_id,
        "class_id": class_id,
        "date": date,
        "model_version": MODEL_VERSION,
        "analysis_mode": "llm",
        "generated_at": datetime.utcnow().isoformat(),
        "students": analysis,
        "metadata": metadata or {},
    }
    s3_client.put_object(
        Bucket=S3_OUTPUTS_BUCKET,
        Key=results_key,
        Body=json.dumps(payload, indent=2).encode("utf-8"),
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
    successful: list[str] = []
    failed: list[str] = []
    extractor: LLMEvidenceExtractor | None = None

    # Process each SQS message
    for record in event.get("Records", []):
        message: Dict[str, Any] = {}
        try:
            message = json.loads(record["body"])
            job_id = message["job_id"]
            normalized_key = message["normalized_key"]
            class_id = message["class_id"]
            session_date_str = message["date"]
            analysis_mode = message.get("analysis_mode", "llm")
            model_version = message.get("model_version", MODEL_VERSION)

            logger.info(
                "Starting LLM scoring for job %s (class=%s, date=%s, analysis_mode=%s, model_version=%s)",
                job_id,
                class_id,
                session_date_str,
                analysis_mode,
                model_version,
            )

            # Update job status
            update_job_status(job_id, "scoring", analysis_mode=analysis_mode)

            # Load normalized transcript
            transcript_lines = load_normalized_transcript(normalized_key)
            line_count = len(transcript_lines)
            logger.info("Loaded %d transcript lines from %s", line_count, normalized_key)

            if line_count == 0:
                raise ValueError("Transcript contains no lines after normalization")

            # Initialize extractor lazily
            if extractor is None:
                logger.info("Initializing LLMEvidenceExtractor (model=%s)", OPENAI_MODEL)
                extractor = LLMEvidenceExtractor(model=OPENAI_MODEL)

            if analysis_mode != "llm":
                logger.warning(
                    "Received analysis_mode=%s but only 'llm' is supported; continuing with LLM scoring",
                    analysis_mode,
                )

            # Score transcript with LLM
            scores = score_transcript_with_llm(transcript_lines, extractor)
            student_count = len(scores)
            logger.info("Generated LLM scores for %d students", student_count)

            metadata_payload = {
                "line_count": line_count,
                "analysis_mode": "llm",
                "model_version": model_version,
                "normalized_key": normalized_key,
                "source_metadata": message.get("metadata", {}),
            }
            scoring_metadata = {
                "student_count": student_count,
                "analysis_mode": "llm",
                "model_version": model_version,
                "completed_at": datetime.utcnow().isoformat(),
            }

            # Store results to S3
            output_keys = store_assessment_results(
                job_id,
                class_id,
                session_date_str,
                scores,
                metadata=metadata_payload,
            )

            # Mark scoring phase complete
            update_job_status(
                job_id,
                "scored",
                output_keys=output_keys,
                scoring_metadata=scoring_metadata,
            )

            if not DATABASE_URL:
                raise ValueError("DATABASE_URL environment variable not set")

            try:
                session_date = date.fromisoformat(session_date_str)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid session date '{session_date_str}': {exc}"
                ) from exc

            persistence_summary: PersistenceSummary = persist_llm_results(
                DATABASE_URL,
                class_id,
                session_date,
                model_version,
                scores,
            )
            logger.info(
                "Persisted assessments for job %s (students=%d, assessments=%d, evidence=%d)",
                job_id,
                persistence_summary.students_processed,
                persistence_summary.assessments_created,
                persistence_summary.evidence_created,
            )

            # Finalize job status
            update_job_status(
                job_id,
                "succeeded",
                output_keys=output_keys,
                scoring_metadata=scoring_metadata,
                persistence_metadata=persistence_summary.as_dict(),
                completed_at=datetime.utcnow().isoformat(),
            )

            # Send to aggregation queue (if configured)
            if AGGREGATION_QUEUE_URL and output_keys:
                aggregation_message = {
                    "job_id": job_id,
                    "class_id": class_id,
                    "date": session_date_str,
                    "scores_key": output_keys[0],
                    "student_count": student_count,
                    "analysis_mode": "llm",
                    "model_version": model_version,
                }
                sqs_client.send_message(
                    QueueUrl=AGGREGATION_QUEUE_URL,
                    MessageBody=json.dumps(aggregation_message),
                )
                logger.info("Sent job %s to aggregation queue", job_id)

            successful.append(job_id)
            logger.info("Completed LLM scoring for job %s", job_id)

        except Exception as e:
            logger.error("Scoring failed: %s", e, exc_info=True)
            job_id = message.get("job_id")
            if job_id:
                update_job_status(job_id, "failed", error=str(e))
                failed.append(job_id)

    failed_identifiers = []
    if failed:
        failed_job_ids = set(failed)
        for record in event.get("Records", []):
            try:
                body = json.loads(record["body"])
                if body.get("job_id") in failed_job_ids:
                    failed_identifiers.append({"itemIdentifier": record["messageId"]})
            except Exception:
                continue

    return {
        "statusCode": 200,
        "batchItemFailures": failed_identifiers,
        "successful": successful,
        "failed": failed,
    }
