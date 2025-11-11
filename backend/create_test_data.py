"""Create test data for AssessMax"""
import asyncio
from uuid import UUID

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.student import Student


async def create_test_students():
    """Create test students in the database"""
    async with AsyncSessionLocal() as session:
        # Check if students already exist
        result = await session.execute(select(Student))
        existing = result.scalars().all()

        if existing:
            print(f"✅ Found {len(existing)} existing students:")
            for s in existing:
                print(f"  - {s.name} ({s.student_id})")
            return

        # Create 3 test students
        students = [
            Student(
                student_id=UUID('550e8400-e29b-41d4-a716-446655440001'),
                name='Emma Johnson',
                class_id='MS-7A',
                external_ref='emma.j@school.edu'
            ),
            Student(
                student_id=UUID('550e8400-e29b-41d4-a716-446655440002'),
                name='Marcus Williams',
                class_id='MS-7A',
                external_ref='marcus.w@school.edu'
            ),
            Student(
                student_id=UUID('550e8400-e29b-41d4-a716-446655440003'),
                name='Sarah Chen',
                class_id='MS-7A',
                external_ref='sarah.c@school.edu'
            ),
        ]

        for student in students:
            session.add(student)

        await session.commit()

        # Verify
        result = await session.execute(select(Student))
        all_students = result.scalars().all()
        print(f'✅ Created {len(all_students)} test students:')
        for s in all_students:
            print(f'  - {s.name} ({s.student_id})')


if __name__ == '__main__':
    asyncio.run(create_test_students())
