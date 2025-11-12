"""
Populate AssessMax with realistic demo data for classes, students, assessments,
trends, and upload jobs. This script creates a full six-month dataset that
powers the dashboard, history views, and uploads/jobs page without manual entry.
"""

from __future__ import annotations

import asyncio
import random
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.config import settings
from app.models.assessment import Assessment
from app.models.base import Base, TimestampMixin
from app.models.class_aggregate import ClassAggregate
from app.models.evidence import Evidence
from app.models.student import Student


class UploadJob(Base, TimestampMixin):
    """Minimal upload job model so we can seed pipeline history data."""

    __tablename__ = "upload_jobs"

    job_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, nullable=False)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, index=True)
    class_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    student_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("students.student_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assessment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assessments.assessment_id", ondelete="SET NULL"),
        nullable=True,
    )
    job_type: Mapped[str | None] = mapped_column(String, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


SKILLS = ["empathy", "adaptability", "collaboration", "communication", "self_regulation"]
MODEL_VERSIONS = ["v1.3.0", "v1.3.1", "v1.4.0"]
USER_IDS = [
    "educator.smith",
    "educator.lee",
    "educator.nguyen",
    "educator.patel",
    "principal.martinez",
]
TREND_CHOICES = ["improving", "declining", "mixed"]

CLASS_CONFIGS = [
    {
        "id": "MS-7A",
        "display_name": "7th Grade Advisory A",
        "advisor": "Ms. Evelyn Carter",
        "focus": "Community building & narrative writing",
        "meeting_days": ["Mon", "Wed"],
    },
    {
        "id": "MS-7B",
        "display_name": "7th Grade Advisory B",
        "advisor": "Mr. Jordan Mitchell",
        "focus": "STEM collaborations & peer feedback",
        "meeting_days": ["Tue", "Thu"],
    },
    {
        "id": "MS-8A",
        "display_name": "8th Grade Capstone",
        "advisor": "Dr. Alicia Gonzales",
        "focus": "Capstone presentations & leadership labs",
        "meeting_days": ["Mon", "Wed", "Fri"],
    },
]

CLASS_STUDENT_NAME_POOL = {
    "MS-7A": [
        "Lucas Davis",
        "Isabella Thomas",
        "Harper Nguyen",
        "Caleb Robinson",
        "Elena Brooks",
        "Savannah Reed",
        "Mateo Alvarez",
        "Jocelyn Carter",
        "Parker Simmons",
        "Aiden Kelly",
        "Faith Johnson",
        "Lily Chen",
        "Jamal Rivers",
        "Aubrey Long",
        "Chase Morgan",
        "Genesis Powell",
        "Owen Ramirez",
        "Mila Flores",
        "Declan Price",
        "Amelia Ward",
        "Micah Turner",
    ],
    "MS-7B": [
        "Sophia Garcia",
        "Noah Anderson",
        "Landon Brooks",
        "Scarlett Howard",
        "Gabriel Ortega",
        "Paisley Hughes",
        "Diego Castillo",
        "Natalie Fox",
        "Zion Edwards",
        "Kendall Fisher",
        "Eva Morales",
        "Colton Hayes",
        "Riley Simmons",
        "Piper Watts",
        "Santiago Chavez",
        "Hazel Bryant",
        "Rowan Foster",
        "Gianna Jenkins",
        "Emmett Walsh",
        "Ariana Daniels",
        "Miles Barrett",
    ],
    "MS-8A": [
        "James Brown",
        "Aaliyah Scott",
        "Lincoln Gray",
        "Valentina Ruiz",
        "Elias Porter",
        "London Hayes",
        "Kingston Blake",
        "Maria Ortiz",
        "Jayden Foster",
        "Lila Alexander",
        "Everett Collins",
        "Brooklyn Sanders",
        "Thiago Mendez",
        "Norah Phillips",
        "Kai Robertson",
        "Freya Wallace",
        "Josiah Allen",
        "Avery Bennett",
        "Raelynn Cooper",
        "Zoe Patterson",
        "Greyson Carter",
        "Serena Cole",
    ],
}

FALLBACK_NAMES = [
    "Marcus Williams",
    "Sarah Chen",
    "Alicia Rivera",
    "Elijah Thompson",
    "Naomi Parker",
    "Cooper Bryant",
    "Ivy Sanders",
    "Jordan McKinney",
    "Maya Watson",
    "Emilia Ross",
    "Xavier Lopez",
    "Charlotte Perez",
    "King Rivera",
    "Camila Ortiz",
    "Giovanni Rivera",
]

FIXED_STUDENTS = [
    {"student_id": UUID("d9ad471f-a5d2-4a4d-bd89-29934cdb25c9"), "name": "Lucas Davis", "class_id": "MS-7A"},
    {"student_id": UUID("c187240e-5189-46b7-8114-063252e591b9"), "name": "Isabella Thomas", "class_id": "MS-7A"},
    {"student_id": UUID("48785326-db5d-4c79-b62e-6c1bfddf2c22"), "name": "Sophia Garcia", "class_id": "MS-7B"},
    {"student_id": UUID("39043165-1f24-4f47-bba0-152bbc0b9c96"), "name": "Noah Anderson", "class_id": "MS-7B"},
    {"student_id": UUID("94831446-e4a1-459b-82cc-3c05964db370"), "name": "James Brown", "class_id": "MS-8A"},
]

EVIDENCE_TEMPLATES = {
    "empathy": [
        "{name} noticed a classmate struggling and offered quiet support without being prompted.",
        "{name} paraphrased a peer's perspective during a restorative circle conversation.",
        "During advisory, {name} validated a partner's feelings before suggesting next steps.",
    ],
    "adaptability": [
        "{name} adjusted their presentation plan when the projector failed and kept the group calm.",
        "{name} changed roles mid-activity to cover an absent teammate.",
        "When the lab supplies ran low, {name} proposed an alternative experiment approach.",
    ],
    "collaboration": [
        "{name} facilitated turn-taking so every team member contributed to the design sprint.",
        "{name} synthesized ideas from three classmates into a shared plan.",
        "Group journals show {name} capturing highlights from every teammate after each session.",
    ],
    "communication": [
        "{name} delivered clear instructions before the peer feedback round began.",
        "{name} used academic vocabulary to summarize discussion outcomes for the group.",
        "Student demonstrated active listening by recapping the group's norms aloud.",
    ],
    "self_regulation": [
        "{name} took a brief reset walk when frustrated, then rejoined ready to collaborate.",
        "{name} monitored time-on-task and nudged the team back to the agenda when needed.",
        "Reflection notes show {name} using breathing strategies to stay focused during debate prep.",
    ],
}

UPLOAD_ERRORS = [
    "Document parser timed out before normalization completed.",
    "Audio transcript missing speaker labels for 20% of segments.",
    "File encrypted – please export an unprotected PDF.",
]


def make_external_ref(name: str, class_id: str) -> str:
    slug = name.lower().replace(" ", ".")
    return f"{slug}@{class_id.lower()}.school.local"


def title_case_skill(skill: str) -> str:
    return skill.replace("_", " ").title()


def month_end(day: date) -> date:
    first_next_month = (day.replace(day=1) + timedelta(days=32)).replace(day=1)
    return first_next_month - timedelta(days=1)


async def purge_existing_data(session: AsyncSession) -> None:
    """Remove previously seeded demo data so reruns remain deterministic."""

    await session.execute(delete(Evidence))
    await session.execute(delete(Assessment))
    await session.execute(delete(ClassAggregate))
    await session.execute(delete(UploadJob))
    await session.execute(delete(Student))
    await session.flush()


async def create_students_for_class(
    session: AsyncSession,
    class_id: str,
    stats: dict[str, int],
    class_registry: dict[str, dict[str, list]],
) -> list[Student]:
    """Create 15-20 students for the given class, including fixed IDs."""

    target = random.randint(15, 20)
    created: list[Student] = []
    fixed_lookup = {f["name"]: f for f in FIXED_STUDENTS if f["class_id"] == class_id}

    for student_info in fixed_lookup.values():
        student = Student(
            student_id=student_info["student_id"],
            class_id=class_id,
            name=student_info["name"],
            external_ref=make_external_ref(student_info["name"], class_id),
        )
        session.add(student)
        created.append(student)

    available_names = [
        name for name in CLASS_STUDENT_NAME_POOL[class_id] if name not in fixed_lookup
    ]
    random.shuffle(available_names)
    fallback_cycle = FALLBACK_NAMES.copy()
    random.shuffle(fallback_cycle)

    while len(created) < target:
        if available_names:
            name = available_names.pop()
        elif fallback_cycle:
            name = fallback_cycle.pop()
        else:
            name = f"Student {len(created) + 1}"

        student = Student(
            student_id=uuid4(),
            class_id=class_id,
            name=name,
            external_ref=make_external_ref(name, class_id),
        )
        session.add(student)
        created.append(student)

    await session.flush()

    stats["students"] += len(created)
    class_registry[class_id]["students"].extend(created)
    return created


def generate_assessment_dates(num_assessments: int) -> list[date]:
    """Spread assessments across the last six months."""

    start = date.today() - timedelta(days=180)
    offsets = sorted(random.sample(range(0, 181), num_assessments))
    return [start + timedelta(days=offset) for offset in offsets]


async def create_assessments_for_student(
    session: AsyncSession,
    student: Student,
    class_focus: str,
    stats: dict[str, int],
    class_registry: dict[str, dict[str, list]],
) -> None:
    """Generate 10-15 assessments per student with evidence and trend."""

    num_assessments = random.randint(10, 15)
    assessment_dates = generate_assessment_dates(num_assessments)
    trend = random.choice(TREND_CHOICES)

    baseline = {skill: random.uniform(4.8, 8.2) for skill in SKILLS}
    if trend == "improving":
        base_slope = random.uniform(0.8, 1.4)
        slopes = {skill: base_slope * random.uniform(0.6, 1.2) for skill in SKILLS}
    elif trend == "declining":
        base_slope = -random.uniform(0.6, 1.0)
        slopes = {skill: base_slope * random.uniform(0.7, 1.3) for skill in SKILLS}
    else:
        slopes = {skill: random.uniform(-0.6, 0.9) for skill in SKILLS}

    for index, assessed_on in enumerate(assessment_dates):
        progress = index / max(num_assessments - 1, 1)

        scores: dict[str, Decimal] = {}
        confidences: dict[str, Decimal] = {}

        for skill in SKILLS:
            raw = baseline[skill] + slopes[skill] * progress + random.uniform(-0.35, 0.35)
            clamped = min(9.6, max(3.2, raw))
            scores[skill] = Decimal(f"{clamped:.2f}")

            confidence_base = random.uniform(0.62, 0.86)
            confidence_delta = 0.12 * progress if slopes[skill] >= 0 else -0.08 * progress
            confidence_value = min(0.97, max(0.55, confidence_base + confidence_delta))
            confidences[f"confidence_{skill}"] = Decimal(f"{confidence_value:.3f}")

        assessment = Assessment(
            student_id=student.student_id,
            class_id=student.class_id,
            assessed_on=assessed_on,
            model_version=random.choice(MODEL_VERSIONS),
            **scores,
            **confidences,
        )
        session.add(assessment)
        await session.flush()  # Needed so evidence can reference assessment_id

        evidence_entries = build_evidence_entries(
            assessment_id=assessment.assessment_id,
            student_name=student.name or "Student",
            class_focus=class_focus,
        )
        session.add_all(evidence_entries)

        stats["assessments"] += 1
        stats["evidence"] += len(evidence_entries)
        class_registry[student.class_id]["assessments"].append(assessment)


def build_evidence_entries(assessment_id: UUID, student_name: str, class_focus: str) -> list[Evidence]:
    """Create four evidence entries per assessment, one per skill focus."""

    entries: list[Evidence] = []
    for skill in SKILLS:
        note = random.choice(EVIDENCE_TEMPLATES[skill])
        narrative = f"{note.format(name=student_name)} Focus area: {class_focus.lower()}."
        entries.append(
            Evidence(
                assessment_id=assessment_id,
                skill=skill,
                span_text=narrative,
                span_location=f"Session note {random.randint(3, 18)}",
                rationale=f"Illustrates growth in {title_case_skill(skill)} within advisory.",
                score_contrib=Decimal(f"{random.uniform(0.35, 0.9):.3f}"),
            )
        )
    return entries


async def build_class_aggregates(
    session: AsyncSession,
    class_registry: dict[str, dict[str, list]],
    stats: dict[str, int],
) -> None:
    """Create monthly class aggregates and long-range momentum metrics."""

    for class_id in class_registry:
        await session.execute(delete(ClassAggregate).where(ClassAggregate.class_id == class_id))
    await session.flush()

    for class_id, payload in class_registry.items():
        assessments: list[Assessment] = payload["assessments"]
        if not assessments:
            continue

        buckets: dict[tuple[date, date], list[Assessment]] = defaultdict(list)
        for record in assessments:
            window_start = record.assessed_on.replace(day=1)
            window_end = month_end(record.assessed_on)
            buckets[(window_start, window_end)].append(record)

        for (window_start, window_end), records in buckets.items():
            for skill in SKILLS:
                values = [float(getattr(record, skill) or 0) * 10 for record in records]
                if not values:
                    continue
                average = sum(values) / len(values)
                aggregate = ClassAggregate(
                    class_id=class_id,
                    window_start=window_start,
                    window_end=window_end,
                    metric_name=f"avg_{skill}",
                    metric_value=Decimal(f"{average:.2f}"),
                )
                session.add(aggregate)
                stats["aggregates"] += 1

        ordered = sorted(assessments, key=lambda item: item.assessed_on)
        first_date = ordered[0].assessed_on
        last_date = ordered[-1].assessed_on
        for skill in SKILLS:
            start_value = float(getattr(ordered[0], skill) or 0) * 10
            end_value = float(getattr(ordered[-1], skill) or 0) * 10
            delta = end_value - start_value
            momentum = ClassAggregate(
                class_id=class_id,
                window_start=first_date,
                window_end=last_date,
                metric_name=f"momentum_{skill}",
                metric_value=Decimal(f"{delta:.2f}"),
            )
            session.add(momentum)
            stats["aggregates"] += 1


async def create_upload_jobs(
    session: AsyncSession,
    class_registry: dict[str, dict[str, list]],
    stats: dict[str, int],
) -> None:
    """Seed uploads/jobs dashboard with realistic pipeline records."""

    now = datetime.now(tz=UTC)

    for class_id, payload in class_registry.items():
        students: list[Student] = payload["students"]
        assessments: list[Assessment] = payload["assessments"]
        if not students or not assessments:
            continue

        scenarios = [
            ("completed", "transcript", -12),
            ("processing", "transcript", -3),
            ("failed", "artifact", -8),
        ]

        for status, job_type, day_offset in scenarios:
            created_at = now + timedelta(days=day_offset)
            started_at = created_at + timedelta(minutes=random.randint(10, 45))
            completed_at = None
            error_message = None

            if status == "completed":
                completed_at = started_at + timedelta(minutes=random.randint(18, 60))
            elif status == "failed":
                completed_at = started_at + timedelta(minutes=random.randint(8, 20))
                error_message = random.choice(UPLOAD_ERRORS)

            student = random.choice(students)
            assessment = random.choice(assessments)
            filename_suffix = f"{created_at:%Y%m%d}"
            extension = ".jsonl" if job_type == "transcript" else ".pdf"
            file_name = f"{class_id.lower()}_{job_type}_{filename_suffix}{extension}"

            job = UploadJob(
                user_id=random.choice(USER_IDS),
                file_name=file_name,
                status=status,
                class_id=class_id,
                student_id=student.student_id,
                assessment_id=assessment.assessment_id,
                job_type=job_type,
                started_at=started_at,
                completed_at=completed_at,
                error_message=error_message,
                created_at=created_at,
            )
            session.add(job)
            stats["upload_jobs"] += 1


async def populate_database() -> None:
    """Main entry point to generate synthetic AssessMax data."""

    random.seed(20250217)

    db_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("🧹 Clearing existing demo data...")
        await purge_existing_data(session)

        stats = {"students": 0, "assessments": 0, "evidence": 0, "aggregates": 0, "upload_jobs": 0}
        class_registry: dict[str, dict[str, list]] = {
            config["id"]: {"students": [], "assessments": []} for config in CLASS_CONFIGS
        }

        print("👩‍🏫 Creating classes, students, and assessments...")
        for config in CLASS_CONFIGS:
            students = await create_students_for_class(session, config["id"], stats, class_registry)
            for student in students:
                await create_assessments_for_student(
                    session,
                    student,
                    class_focus=config["focus"],
                    stats=stats,
                    class_registry=class_registry,
                )

        print("📊 Building class trend aggregates...")
        await build_class_aggregates(session, class_registry, stats)

        print("📂 Seeding upload and job history...")
        await create_upload_jobs(session, class_registry, stats)

        await session.commit()

        print("\n✅ AssessMax data population complete!")
        print(f"   • Classes seeded: {', '.join(cfg['id'] for cfg in CLASS_CONFIGS)}")
        print(f"   • Students created: {stats['students']}")
        print(f"   • Assessments generated: {stats['assessments']}")
        print(f"   • Evidence entries: {stats['evidence']}")
        print(f"   • Class aggregates: {stats['aggregates']}")
        print(f"   • Upload/job records: {stats['upload_jobs']}")
        print("\nRun the frontend to explore dashboards, trends, and upload history.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(populate_database())
