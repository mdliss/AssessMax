"""Utilities for persisting LLM scoring results to PostgreSQL."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Iterable
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)


@dataclass
class PersistenceSummary:
    """Summary of database persistence operations."""

    students_processed: int
    assessments_created: int
    evidence_created: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "students_processed": self.students_processed,
            "assessments_created": self.assessments_created,
            "evidence_created": self.evidence_created,
        }


def ensure_student_exists(
    cur,
    student_id: UUID,
    class_id: str,
    student_name: str | None = None,
    external_ref: str | None = None,
) -> UUID:
    """
    Ensure the student record exists; create it if necessary.

    Args:
        cur: psycopg cursor
        student_id: Student UUID from transcript payload
        class_id: Class identifier
        student_name: Optional student name
        external_ref: Optional external identifier

    Returns:
        UUID of the student record
    """
    cur.execute(
        "SELECT student_id, name, external_ref FROM students WHERE student_id = %s",
        (str(student_id),),
    )
    result = cur.fetchone()

    if result:
        # Update name/external_ref if missing and we have new info
        updates = []
        params: list[Any] = []

        if student_name and not result.get("name"):
            updates.append("name = %s")
            params.append(student_name)

        if external_ref and not result.get("external_ref"):
            updates.append("external_ref = %s")
            params.append(external_ref)

        if updates:
            params.append(str(student_id))
            cur.execute(f"UPDATE students SET {', '.join(updates)} WHERE student_id = %s", params)

        return UUID(result["student_id"])

    # Insert new student record
    cur.execute(
        """
        INSERT INTO students (student_id, class_id, name, external_ref, created_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            str(student_id),
            class_id,
            student_name,
            external_ref,
            datetime.utcnow(),
        ),
    )
    logger.info("Created new student record %s (%s)", student_id, student_name)
    return student_id


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (ValueError, TypeError):
        return None


def create_assessment(
    cur,
    student_id: UUID,
    class_id: str,
    assessed_on: date,
    scores: dict[str, Any],
    model_version: str,
) -> UUID:
    """
    Create an assessment row for the student.

    Args:
        cur: psycopg cursor
        student_id: Student UUID
        class_id: Class identifier
        assessed_on: Assessment date
        scores: Skill score dictionary from LLM
        model_version: Model version string

    Returns:
        UUID of the created assessment
    """
    assessment_id = uuid4()

    def skill_value(skill: str, key: str, default: float) -> Decimal:
        value = scores.get(skill, {}).get(key, default)
        return Decimal(str(value))

    empathy = skill_value("empathy", "score", 5.0)
    adaptability = skill_value("adaptability", "score", 5.0)
    collaboration = skill_value("collaboration", "score", 5.0)
    communication = skill_value("communication", "score", 5.0)
    self_regulation = skill_value("self_regulation", "score", 5.0)

    confidence_empathy = skill_value("empathy", "confidence", 0.3)
    confidence_adaptability = skill_value("adaptability", "confidence", 0.3)
    confidence_collaboration = skill_value("collaboration", "confidence", 0.3)
    confidence_communication = skill_value("communication", "confidence", 0.3)
    confidence_self_regulation = skill_value("self_regulation", "confidence", 0.3)

    cur.execute(
        """
        INSERT INTO assessments (
            assessment_id,
            student_id,
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
            model_version,
            created_at
        )
        VALUES (
            %(assessment_id)s,
            %(student_id)s,
            %(class_id)s,
            %(assessed_on)s,
            %(empathy)s,
            %(adaptability)s,
            %(collaboration)s,
            %(communication)s,
            %(self_regulation)s,
            %(confidence_empathy)s,
            %(confidence_adaptability)s,
            %(confidence_collaboration)s,
            %(confidence_communication)s,
            %(confidence_self_regulation)s,
            %(model_version)s,
            %(created_at)s
        )
        """,
        {
            "assessment_id": str(assessment_id),
            "student_id": str(student_id),
            "class_id": class_id,
            "assessed_on": assessed_on,
            "empathy": empathy,
            "adaptability": adaptability,
            "collaboration": collaboration,
            "communication": communication,
            "self_regulation": self_regulation,
            "confidence_empathy": confidence_empathy,
            "confidence_adaptability": confidence_adaptability,
            "confidence_collaboration": confidence_collaboration,
            "confidence_communication": confidence_communication,
            "confidence_self_regulation": confidence_self_regulation,
            "model_version": model_version,
            "created_at": datetime.utcnow(),
        },
    )

    return assessment_id


def create_evidence(
    cur,
    assessment_id: UUID,
    evidence_data: dict[str, Iterable[dict[str, Any]]],
) -> int:
    """
    Create evidence rows for an assessment.

    Args:
        cur: psycopg cursor
        assessment_id: Assessment UUID
        evidence_data: Dict of skill -> iterable of evidence dicts

    Returns:
        Total evidence records inserted
    """
    count = 0

    for skill, evidence_items in evidence_data.items():
        for item in evidence_items or []:
            evidence_id = uuid4()
            quote = item.get("quote", "")
            rationale = item.get("rationale", "")
            score_contrib = _decimal_or_none(item.get("score_contribution"))

            cur.execute(
                """
                INSERT INTO evidence (
                    evidence_id,
                    assessment_id,
                    skill,
                    span_text,
                    span_location,
                    rationale,
                    score_contrib,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(evidence_id),
                    str(assessment_id),
                    skill,
                    quote,
                    "llm-transcript",
                    rationale,
                    score_contrib,
                    datetime.utcnow(),
                ),
            )
            count += 1

    return count


def persist_llm_results(
    database_url: str,
    class_id: str,
    session_date: date,
    model_version: str,
    students: Dict[str, Dict[str, Any]],
) -> PersistenceSummary:
    """
    Persist LLM scoring output to PostgreSQL.

    Args:
        database_url: Connection string
        class_id: Class identifier
        session_date: Session date
        model_version: Model version string
        students: Mapping of student_id -> analysis dict

    Returns:
        PersistenceSummary describing work performed
    """
    if not students:
        logger.warning("No students to persist for class %s on %s", class_id, session_date)
        return PersistenceSummary(0, 0, 0)

    assessments_created = 0
    evidence_created = 0

    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            for student_id_str, student_data in students.items():
                try:
                    student_uuid = UUID(student_id_str)
                except ValueError:
                    logger.error("Invalid student_id '%s'; skipping", student_id_str)
                    continue

                student_name = student_data.get("student_name")
                external_ref = student_data.get("student_external_id")

                ensure_student_exists(
                    cur,
                    student_uuid,
                    class_id,
                    student_name=student_name,
                    external_ref=external_ref,
                )

                assessment_id = create_assessment(
                    cur,
                    student_uuid,
                    class_id,
                    session_date,
                    student_data.get("scores", {}),
                    model_version=model_version,
                )
                assessments_created += 1

                evidence_created += create_evidence(
                    cur,
                    assessment_id,
                    student_data.get("evidence", {}),
                )

        conn.commit()

    return PersistenceSummary(
        students_processed=len(students),
        assessments_created=assessments_created,
        evidence_created=evidence_created,
    )

