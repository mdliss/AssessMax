"""
Lambda function to persist scoring results from S3 to PostgreSQL database.

This function:
1. Receives scoring output location from Step Functions
2. Downloads the scoring JSON from S3
3. Creates/updates Student records in PostgreSQL
4. Creates Assessment records with skill scores
5. Creates Evidence records with supporting text spans
"""

import json
import logging
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import boto3
import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client("s3")

# Database connection string from environment
DATABASE_URL = os.environ.get("DATABASE_URL")


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda handler for persisting scoring results to PostgreSQL.

    Expected event structure from Step Functions:
    {
        "job_id": "uuid",
        "class_id": "MS-7A",
        "date": "2025-11-12",
        "normalizationResult": {
            "job_id": "uuid",
            "normalized_key": "s3-key",
            "line_count": 60
        },
        "scoringResult": {
            "job_id": "uuid",
            "output_key": "scores/MS-7A/2025-11-12/job-uuid.json",
            "student_count": 4
        }
    }
    """
    try:
        logger.info(f"Persistence Lambda invoked with event: {json.dumps(event)}")

        # Extract required fields
        job_id = event.get("job_id")
        class_id = event.get("class_id")
        session_date_str = event.get("date")

        scoring_result = event.get("scoringResult", {})
        output_key = scoring_result.get("output_key")

        if not all([job_id, class_id, session_date_str, output_key]):
            raise ValueError(f"Missing required fields: job_id={job_id}, class_id={class_id}, date={session_date_str}, output_key={output_key}")

        # Parse date
        session_date = date.fromisoformat(session_date_str)

        # Get S3 bucket from output key
        s3_bucket = os.environ.get("S3_OUTPUTS_BUCKET")

        logger.info(f"Downloading scoring results from s3://{s3_bucket}/{output_key}")

        # Download scoring results from S3
        response = s3_client.get_object(Bucket=s3_bucket, Key=output_key)
        scoring_data = json.loads(response["Body"].read().decode("utf-8"))

        logger.info(f"Loaded scoring data for {len(scoring_data)} students")

        # Connect to database
        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                students_processed = 0

                for student_name, student_data in scoring_data.items():
                    try:
                        # Ensure student exists
                        student_id = ensure_student_exists(cur, student_name, class_id)

                        # Create assessment record
                        assessment_id = create_assessment(
                            cur,
                            student_id=student_id,
                            class_id=class_id,
                            assessed_on=session_date,
                            scores=student_data["scores"],
                        )

                        # Create evidence records
                        create_evidence(
                            cur,
                            assessment_id=assessment_id,
                            evidence_data=student_data["evidence"],
                        )

                        students_processed += 1
                        logger.info(f"Processed student {student_name} (ID: {student_id})")

                    except Exception as e:
                        logger.error(f"Error processing student {student_name}: {e}")
                        # Continue processing other students
                        continue

                conn.commit()
                logger.info(f"Successfully persisted data for {students_processed} students")

        return {
            "statusCode": 200,
            "job_id": job_id,
            "students_processed": students_processed,
            "message": f"Successfully persisted scoring results for {students_processed} students",
        }

    except Exception as e:
        logger.error(f"Error in persistence Lambda: {e}", exc_info=True)
        raise


def ensure_student_exists(cur, student_name: str, class_id: str) -> UUID:
    """
    Ensure student exists in database, create if not exists.

    Returns the student_id UUID.
    """
    # Check if student exists by name and class
    cur.execute(
        "SELECT student_id FROM students WHERE name = %s AND class_id = %s",
        (student_name, class_id),
    )
    result = cur.fetchone()

    if result:
        return UUID(result["student_id"])

    # Create new student
    student_id = uuid4()
    cur.execute(
        """
        INSERT INTO students (student_id, name, class_id, created_at)
        VALUES (%s, %s, %s, %s)
        """,
        (str(student_id), student_name, class_id, datetime.utcnow()),
    )

    logger.info(f"Created new student: {student_name} (ID: {student_id})")
    return student_id


def create_assessment(
    cur,
    student_id: UUID,
    class_id: str,
    assessed_on: date,
    scores: dict[str, Any],
) -> UUID:
    """
    Create assessment record in database.

    Scores are expected in format:
    {
        "empathy": {"score": 0.45, "confidence": 0.7, "demonstration_count": 1},
        ...
    }

    Database stores scores on 0-10 scale, so we convert from 0-1 scale.
    """
    assessment_id = uuid4()

    # Convert scores from 0-1 to 0-10 scale and prepare values
    empathy = Decimal(str(scores.get("empathy", {}).get("score", 0))) * 10
    adaptability = Decimal(str(scores.get("adaptability", {}).get("score", 0))) * 10
    collaboration = Decimal(str(scores.get("collaboration", {}).get("score", 0))) * 10
    communication = Decimal(str(scores.get("communication", {}).get("score", 0))) * 10
    self_regulation = Decimal(str(scores.get("self_regulation", {}).get("score", 0))) * 10

    # Confidence values (0-1 scale)
    confidence_empathy = Decimal(str(scores.get("empathy", {}).get("confidence", 0)))
    confidence_adaptability = Decimal(str(scores.get("adaptability", {}).get("confidence", 0)))
    confidence_collaboration = Decimal(str(scores.get("collaboration", {}).get("confidence", 0)))
    confidence_communication = Decimal(str(scores.get("communication", {}).get("confidence", 0)))
    confidence_self_regulation = Decimal(str(scores.get("self_regulation", {}).get("confidence", 0)))

    cur.execute(
        """
        INSERT INTO assessments (
            assessment_id, student_id, class_id, assessed_on,
            empathy, adaptability, collaboration, communication, self_regulation,
            confidence_empathy, confidence_adaptability, confidence_collaboration,
            confidence_communication, confidence_self_regulation,
            model_version, created_at
        )
        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s
        )
        """,
        (
            str(assessment_id),
            str(student_id),
            class_id,
            assessed_on,
            empathy,
            adaptability,
            collaboration,
            communication,
            self_regulation,
            confidence_empathy,
            confidence_adaptability,
            confidence_collaboration,
            confidence_communication,
            confidence_self_regulation,
            "v1.0",  # Model version
            datetime.utcnow(),
        ),
    )

    logger.info(f"Created assessment {assessment_id} for student {student_id}")
    return assessment_id


def create_evidence(
    cur,
    assessment_id: UUID,
    evidence_data: dict[str, list[dict[str, Any]]],
) -> None:
    """
    Create evidence records in database.

    Evidence data format:
    {
        "empathy": [
            {"line_number": 51, "text": "...", "keyword": "support"},
            ...
        ],
        ...
    }
    """
    for skill, evidence_list in evidence_data.items():
        for evidence_item in evidence_list:
            evidence_id = uuid4()

            span_text = evidence_item.get("text", "")
            line_number = evidence_item.get("line_number")
            keyword = evidence_item.get("keyword", "")

            # Create location reference
            span_location = f"line {line_number}" if line_number else "unknown"

            # Create rationale
            rationale = f"Evidence of {skill} - keyword: {keyword}"

            cur.execute(
                """
                INSERT INTO evidence (
                    evidence_id, assessment_id, skill,
                    span_text, span_location, rationale,
                    score_contrib, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(evidence_id),
                    str(assessment_id),
                    skill,
                    span_text,
                    span_location,
                    rationale,
                    Decimal("0.1"),  # Default score contribution
                    datetime.utcnow(),
                ),
            )

    logger.info(f"Created evidence records for assessment {assessment_id}")
