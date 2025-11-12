"""
Script to populate the database with sample student and assessment data.
Run this to get data showing in your frontend.
"""

import asyncio
import random
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.assessment import Assessment
from app.models.base import Base
from app.models.evidence import Evidence
from app.models.student import Student

# Sample data
CLASSES = ["MS-7A", "MS-7B", "MS-8A"]
STUDENT_NAMES = [
    "Emma Johnson",
    "Marcus Williams",
    "Sarah Chen",
    "Alicia Rivera",
    "James Brown",
    "Olivia Martinez",
    "Lucas Davis",
    "Sophia Garcia",
    "Ethan Rodriguez",
    "Ava Wilson",
    "Noah Anderson",
    "Isabella Thomas",
    "Mason Taylor",
    "Mia Moore",
    "Logan Jackson",
]

SKILLS = ["empathy", "adaptability", "collaboration", "communication", "self_regulation"]

EVIDENCE_SAMPLES = [
    "Student helped a classmate understand a difficult concept during group work.",
    "Adapted well to a last-minute change in project requirements.",
    "Actively participated in team discussions and encouraged others to share ideas.",
    "Clearly presented their research findings to the class.",
    "Remained calm and focused despite setbacks in the project.",
    "Showed understanding of another student's perspective during a disagreement.",
    "Quickly adjusted approach when initial strategy wasn't working.",
    "Facilitated group coordination and ensured everyone contributed.",
    "Articulated complex ideas in an easy-to-understand manner.",
    "Demonstrated patience and self-control in a challenging situation.",
]


def generate_skill_score() -> Decimal:
    """Generate a random skill score between 3.0 and 9.5 (on 0-10 scale)"""
    return Decimal(str(round(random.uniform(3.0, 9.5), 2)))


def generate_confidence() -> Decimal:
    """Generate a random confidence score between 0.5 and 0.95"""
    return Decimal(str(round(random.uniform(0.5, 0.95), 3)))


async def populate_database():
    """Populate database with sample data"""

    # Create async engine (use asyncpg driver)
    db_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url, echo=True)

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print("Creating students and assessments...")

        student_count = 0
        assessment_count = 0
        evidence_count = 0

        for class_id in CLASSES:
            # Create 5 students per class
            students_in_class = random.sample(STUDENT_NAMES, 5)

            for student_name in students_in_class:
                # Create student
                student = Student(
                    student_id=uuid4(),
                    class_id=class_id,
                    name=student_name,
                    external_ref=f"EXT-{random.randint(1000, 9999)}",
                )
                session.add(student)
                student_count += 1

                # Create 3-5 assessments per student (over the last 60 days)
                num_assessments = random.randint(3, 5)
                for i in range(num_assessments):
                    days_ago = random.randint(0, 60)
                    assessed_date = date.today() - timedelta(days=days_ago)

                    # Generate skill scores
                    assessment = Assessment(
                        assessment_id=uuid4(),
                        student_id=student.student_id,
                        class_id=class_id,
                        assessed_on=assessed_date,
                        model_version="v1.0.0",
                        empathy=generate_skill_score(),
                        adaptability=generate_skill_score(),
                        collaboration=generate_skill_score(),
                        communication=generate_skill_score(),
                        self_regulation=generate_skill_score(),
                        confidence_empathy=generate_confidence(),
                        confidence_adaptability=generate_confidence(),
                        confidence_collaboration=generate_confidence(),
                        confidence_communication=generate_confidence(),
                        confidence_self_regulation=generate_confidence(),
                    )
                    session.add(assessment)
                    assessment_count += 1

                    # Add 2-4 evidence items per assessment
                    num_evidence = random.randint(2, 4)
                    for _ in range(num_evidence):
                        skill = random.choice(SKILLS)
                        span_text = random.choice(EVIDENCE_SAMPLES)

                        evidence = Evidence(
                            evidence_id=uuid4(),
                            assessment_id=assessment.assessment_id,
                            skill=skill,
                            span_text=span_text,
                            span_location=f"Observation {random.randint(1, 20)}",
                            rationale=f"This demonstrates {skill.replace('_', ' ')} through their actions.",
                            score_contrib=generate_confidence(),
                        )
                        session.add(evidence)
                        evidence_count += 1

        # Commit all data
        await session.commit()

        print(f"\n✅ Database populated successfully!")
        print(f"   - Students created: {student_count}")
        print(f"   - Assessments created: {assessment_count}")
        print(f"   - Evidence items created: {evidence_count}")
        print(f"   - Classes: {', '.join(CLASSES)}")
        print(f"\nYou can now view this data in your frontend!")


if __name__ == "__main__":
    asyncio.run(populate_database())
