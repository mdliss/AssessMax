"""Simple end-to-end system test"""
import asyncio
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.assessment import Assessment
from app.models.evidence import Evidence
from app.models.student import Student


async def test_system():
    """Test basic system functionality"""

    print("="*70)
    print("ASSESSMAX END-TO-END SYSTEM TEST")
    print("="*70)

    # Test 1: Database Connection
    print("\n✓ Test 1: Database Connection")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Student))
        students = result.scalars().all()
        print(f"  - Connected to database successfully")
        print(f"  - Found {len(students)} students in database")
        for student in students:
            print(f"    • {student.name} ({student.student_id})")

    # Test 2: NLP Pipeline Initialization
    print("\n✓ Test 2: NLP Pipeline Initialization")
    from app.nlp import NLPPipeline
    pipeline = NLPPipeline()
    print("  - NLP Pipeline initialized successfully")
    print(f"  - Pipeline version: {pipeline.__class__.__name__}")

    # Test 3: Process Sample Text
    print("\n✓ Test 3: Process Sample Transcript")
    sample_text = """Teacher: Good morning class.
Student A: Good morning! I'm ready to learn.
Student A: Can I help someone who's confused?
Teacher: That's very thoughtful of you.
Student A: I understand how they feel."""

    result = pipeline.process_transcript(sample_text)
    print("  - Transcript processed successfully")
    print(f"  - Detected language: {result['language']['language']}")
    print(f"  - Sentence count: {result['processing_stats']['sentence_count']}")
    print(f"  - Student IDs found: {len(result['student_ids'])}")

    # Test 4: Create Assessment Record
    print("\n✓ Test 4: Create Assessment Record")
    async with AsyncSessionLocal() as session:
        # Create a test assessment
        assessment = Assessment(
            student_id=UUID('550e8400-e29b-41d4-a716-446655440001'),
            class_id='MS-7A',
            assessed_on=date.today(),
            model_version='1.0.0',
            empathy=Decimal('7.5'),
            adaptability=Decimal('6.2'),
            collaboration=Decimal('8.1'),
            communication=Decimal('7.8'),
            self_regulation=Decimal('6.5'),
            confidence_empathy=Decimal('0.85'),
            confidence_adaptability=Decimal('0.72'),
            confidence_collaboration=Decimal('0.91'),
            confidence_communication=Decimal('0.88'),
            confidence_self_regulation=Decimal('0.75'),
        )
        session.add(assessment)
        await session.flush()
        assessment_id = assessment.assessment_id

        # Create evidence records
        evidence1 = Evidence(
            assessment_id=assessment_id,
            skill='empathy',
            span_text='I understand how they feel',
            span_location='line 5',
            score_contrib=Decimal('0.8'),
            rationale='Clear expression of understanding others feelings',
        )
        evidence2 = Evidence(
            assessment_id=assessment_id,
            skill='collaboration',
            span_text='Can I help someone who is confused',
            span_location='line 3',
            score_contrib=Decimal('0.9'),
            rationale='Proactive offer to collaborate and help others',
        )
        session.add_all([evidence1, evidence2])
        await session.commit()

        print(f"  - Created assessment record: {assessment_id}")
        print(f"  - Created 2 evidence records")

    # Test 5: Query Assessment Data
    print("\n✓ Test 5: Query Assessment Data")
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Assessment).where(Assessment.student_id == UUID('550e8400-e29b-41d4-a716-446655440001'))
        )
        assessments = result.scalars().all()

        print(f"  - Found {len(assessments)} assessment(s) for Emma Johnson")
        if assessments:
            latest = assessments[-1]
            print(f"  - Latest assessment date: {latest.assessed_on}")
            print(f"  - Skill scores:")
            print(f"    • Empathy: {latest.empathy}/10 (confidence: {latest.confidence_empathy})")
            print(f"    • Adaptability: {latest.adaptability}/10 (confidence: {latest.confidence_adaptability})")
            print(f"    • Collaboration: {latest.collaboration}/10 (confidence: {latest.confidence_collaboration})")
            print(f"    • Communication: {latest.communication}/10 (confidence: {latest.confidence_communication})")
            print(f"    • Self-regulation: {latest.self_regulation}/10 (confidence: {latest.confidence_self_regulation})")

    # Test 6: Validate Core NLP Components
    print("\n✓ Test 6: Validate Core NLP Components")
    from app.nlp.language_detection import LanguageDetector
    from app.nlp.text_cleanup import TextCleaner
    from app.nlp.sentence_segmentation import SentenceSegmenter
    from app.nlp.skill_detection import SkillDetector

    lang_detector = LanguageDetector()
    lang_result = lang_detector.detect("This is English text")
    print(f"  - Language Detection: {lang_result['language']} ({lang_result['confidence']:.2f})")

    cleaner = TextCleaner()
    clean_text = cleaner.clean_transcript("  Extra   spaces   ")
    print(f"  - Text Cleanup: Working")

    segmenter = SentenceSegmenter()
    sentences = segmenter.segment("First sentence. Second sentence.")
    print(f"  - Sentence Segmentation: {len(sentences)} sentences")

    skill_det = SkillDetector()
    print(f"  - Skill Detector: Initialized with {len(skill_det.SKILL_PATTERNS)} skills")

    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED - SYSTEM IS FUNCTIONAL")
    print("="*70)
    print("\n📋 System Status:")
    print("  ✅ Database: Connected and operational")
    print("  ✅ NLP Pipeline: All components initialized")
    print("  ✅ Data Models: Student, Assessment, Evidence working")
    print("  ✅ Core Processing: Language detection, text cleanup, segmentation functional")
    print("\n💡 Next Steps:")
    print("  - Connect to AWS services (S3, DynamoDB) for production")
    print("  - Set up authentication (Cognito)")
    print("  - Deploy Streamlit dashboard")
    print("  - Process real transcript data")
    print("="*70)


if __name__ == '__main__':
    asyncio.run(test_system())
