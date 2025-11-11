"""Generate rubric-aligned synthetic data for AssessMax deployments.

This script seeds the Postgres database with classes, students, assessments,
evidence, and class aggregates so that the dashboard and API are populated
with realistic content for demos, staging environments, or QA runs.

Usage::

    python -m backend.scripts.generate_synthetic_data --classes 2 --weeks 12
"""

from __future__ import annotations

import argparse
import asyncio
import random
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable
from uuid import UUID, uuid4

from sqlalchemy import delete, select

from app.database import AsyncSessionLocal
from app.models.assessment import Assessment
from app.models.class_aggregate import ClassAggregate
from app.models.evidence import Evidence
from app.models.student import Student

SKILLS = ["empathy", "adaptability", "collaboration", "communication", "self_regulation"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed AssessMax with synthetic data.")
    parser.add_argument("--classes", type=int, default=2, help="Number of classes to generate.")
    parser.add_argument(
        "--students-per-class",
        type=int,
        default=6,
        help="Number of students per class roster.",
    )
    parser.add_argument("--weeks", type=int, default=12, help="Number of weekly assessments to create.")
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Purge existing students, assessments, evidence, and aggregates before seeding.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20241205,
        help="Random seed for reproducible datasets.",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    random.seed(args.seed)

    async with AsyncSessionLocal() as session:
        if args.drop_existing:
            await purge_existing_data(session)

        class_ids = generate_class_ids(args.classes)
        for class_id in class_ids:
            await ensure_students(session, class_id, args.students_per_class)
            await create_assessments_for_class(session, class_id, args.weeks)

        await create_class_aggregates(session, class_ids)
        await session.commit()

    print("✅ Synthetic dataset ready!")


async def purge_existing_data(session) -> None:
    """Remove existing seeded data to avoid collisions."""

    print("⚠️ Dropping existing assessments, evidence, aggregates, and students…")
    await session.execute(delete(Evidence))
    await session.execute(delete(Assessment))
    await session.execute(delete(ClassAggregate))
    await session.execute(delete(Student))
    await session.commit()


def generate_class_ids(count: int) -> list[str]:
    base_sections = ["A", "B", "C", "D", "E"]
    grade_levels = ["6", "7", "8"]
    class_ids = []
    for idx in range(count):
        section = base_sections[idx % len(base_sections)]
        grade = grade_levels[idx % len(grade_levels)]
        class_ids.append(f"MS-{grade}{section}")
    return class_ids


async def ensure_students(session, class_id: str, students_per_class: int) -> None:
    """Create students for a class if none exist."""

    existing = await session.execute(
        select(Student).where(Student.class_id == class_id)
    )
    students = existing.scalars().all()
    if students:
        print(f"ℹ️ Class {class_id} already has {len(students)} students – skipping creation.")
        return

    roster_names = [
        "Emma Johnson",
        "Marcus Williams",
        "Sarah Chen",
        "Alicia Rivera",
        "Omar Patel",
        "Liam Cooper",
        "Grace Thompson",
        "Isabella Rossi",
        "Noah Kim",
        "Sophia Martinez",
    ]
    random.shuffle(roster_names)

    print(f"➕ Creating {students_per_class} students for class {class_id}")
    for idx in range(students_per_class):
        name = roster_names[idx % len(roster_names)]
        student = Student(
            student_id=uuid4(),
            class_id=class_id,
            name=name,
            external_ref=f"{name.lower().replace(' ', '.')}.{class_id.lower()}@school.edu",
        )
        session.add(student)

    await session.flush()


async def create_assessments_for_class(session, class_id: str, weeks: int) -> None:
    """Generate weekly assessments and evidence for every student in a class."""

    result = await session.execute(select(Student).where(Student.class_id == class_id))
    students = result.scalars().all()
    if not students:
        return

    base_date = date.today()
    print(f"📈 Generating {weeks} weeks of assessments for {class_id}")

    for student in students:
        performance_anchor = random.uniform(6.0, 8.5)
        for week in range(weeks):
            assessed_on = base_date - timedelta(days=7 * week)
            scores = {}
            confidences = {}
            for skill in SKILLS:
                drift = random.uniform(-0.4, 0.6)
                value = min(9.5, max(4.5, performance_anchor + drift + random.uniform(-0.3, 0.3)))
                scores[skill] = Decimal(f"{value:.2f}")
                confidences[f"confidence_{skill}"] = Decimal(f"{random.uniform(0.6, 0.95):.3f}")

            assessment = Assessment(
                student_id=student.student_id,
                class_id=class_id,
                assessed_on=assessed_on,
                model_version="1.0.0-sim",
                **scores,
                **confidences,
            )
            session.add(assessment)
            await session.flush()

            evidence_entries = build_evidence_entries(assessment.assessment_id, student.name or str(student.student_id))
            session.add_all(evidence_entries)


def build_evidence_entries(assessment_id: UUID, student_name: str) -> list[Evidence]:
    """Create synthetic evidence spans referencing transcript locations."""

    entries: list[Evidence] = []
    for skill in SKILLS:
        for _ in range(2):
            entries.append(
                Evidence(
                    assessment_id=assessment_id,
                    skill=skill,
                    span_text=f"{student_name} demonstrated {format_skill_phrase(skill)} during collaborative work.",
                    span_location=f"Transcript line {random.randint(20, 140)}",
                    rationale=f"Clear indicators of {format_skill_phrase(skill)} in peer interactions.",
                    score_contrib=Decimal(f"{random.uniform(0.35, 0.9):.3f}"),
                )
            )
    return entries


def format_skill_phrase(skill: str) -> str:
    return skill.replace("_", " ").lower()


async def create_class_aggregates(session, class_ids: Iterable[str]) -> None:
    """Compute class aggregates for 4-week windows."""

    for class_id in class_ids:
        result = await session.execute(select(Assessment).where(Assessment.class_id == class_id))
        assessments = result.scalars().all()
        if not assessments:
            continue

        buckets: dict[tuple[date, date], list[Assessment]] = defaultdict(list)
        for assessment in assessments:
            window_start = assessment.assessed_on - timedelta(days=assessment.assessed_on.weekday())
            window_end = window_start + timedelta(days=27)
            buckets[(window_start, window_end)].append(assessment)

        for (window_start, window_end), records in buckets.items():
            for skill in SKILLS:
                avg_score = sum(float(getattr(record, skill) or 0) for record in records) / len(records)
                aggregate = ClassAggregate(
                    class_id=class_id,
                    window_start=window_start,
                    window_end=window_end,
                    metric_name=f"avg_{skill}",
                    metric_value=Decimal(f"{avg_score:.2f}"),
                )
                await session.merge(aggregate)


if __name__ == "__main__":
    asyncio.run(main())
