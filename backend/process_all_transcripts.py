"""Process all sample transcripts and generate comprehensive assessments"""
import asyncio
import json
from pathlib import Path
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.student import Student
from app.models.assessment import Assessment
from app.models.evidence import Evidence
from app.nlp import NLPPipeline, SkillDetector, EvidenceExtractor


async def process_transcript_file(filepath: Path, pipeline: NLPPipeline):
    """Process a single transcript file"""

    # Load transcript
    transcript_lines = []
    with open(filepath) as f:
        for line in f:
            transcript_lines.append(json.loads(line))

    # Build full text
    full_text = "\n".join([
        f"{item.get('speaker', 'Unknown')}: {item.get('text', '')}"
        for item in transcript_lines
    ])

    # Extract student name from filename
    filename = filepath.stem  # e.g., "transcript_emma_1"
    student_name_part = filename.split('_')[1].capitalize()  # "emma" -> "Emma"

    # Map to full name
    name_map = {
        'Emma': 'Emma Johnson',
        'Marcus': 'Marcus Williams',
        'Sarah': 'Sarah Chen'
    }
    student_name = name_map.get(student_name_part, student_name_part)

    print(f"\n{'='*70}")
    print(f"Processing: {filepath.name}")
    print(f"Student: {student_name}")
    print(f"Utterances: {len(transcript_lines)}")
    print(f"Text length: {len(full_text)} characters")
    print(f"{'='*70}")

    # Process transcript with NLP pipeline
    result = pipeline.process_transcript(full_text)

    print(f"\n📊 NLP Processing Results:")
    print(f"  Language: {result['language']['language']} (confidence: {result['language']['confidence']:.2f})")
    print(f"  Sentences: {result['processing_stats']['sentence_count']}")
    print(f"  Students detected: {result['processing_stats']['student_count']}")

    # Initialize skill detector and evidence extractor
    skill_detector = SkillDetector()
    evidence_extractor = EvidenceExtractor()

    # Detect skills and extract evidence
    sentences = result['processing_stats'].get('sentences', [])

    # Calculate skill scores (simplified for demo)
    skill_scores = {}
    skill_confidences = {}
    skill_evidence = {}

    for skill_name in ['empathy', 'adaptability', 'collaboration', 'communication', 'self_regulation']:
        # Extract evidence for this skill
        evidence_items = evidence_extractor.extract_from_transcript(
            full_text,
            skill_name,
            student_id=student_name
        )

        skill_evidence[skill_name] = evidence_items

        # Calculate score based on evidence
        if evidence_items:
            avg_score = sum(e.score_contribution for e in evidence_items) / len(evidence_items)
            skill_scores[skill_name] = min(10.0, avg_score * 10)  # Scale to 0-10
            skill_confidences[skill_name] = min(1.0, len(evidence_items) / 5.0)  # More evidence = higher confidence
        else:
            skill_scores[skill_name] = 5.0  # Neutral score
            skill_confidences[skill_name] = 0.5

    print(f"\n🎯 Skill Assessments:")
    for skill_name in skill_scores:
        score = skill_scores[skill_name]
        confidence = skill_confidences[skill_name]
        evidence_count = len(skill_evidence[skill_name])
        print(f"  {skill_name.capitalize():15} {score:.1f}/10  (confidence: {confidence:.2f}, evidence: {evidence_count})")

    # Get student from database
    async with AsyncSessionLocal() as session:
        result_student = await session.execute(
            select(Student).where(Student.name == student_name)
        )
        student = result_student.scalars().first()

        if not student:
            print(f"\n❌ Student {student_name} not found in database")
            return None

        print(f"\n✅ Student found: {student.name} ({student.student_id})")

        # Create assessment
        assessment = Assessment(
            student_id=student.student_id,
            class_id=student.class_id,
            assessed_on=date.today(),
            model_version='1.0.0',
            empathy=Decimal(str(skill_scores['empathy'])),
            adaptability=Decimal(str(skill_scores['adaptability'])),
            collaboration=Decimal(str(skill_scores['collaboration'])),
            communication=Decimal(str(skill_scores['communication'])),
            self_regulation=Decimal(str(skill_scores['self_regulation'])),
            confidence_empathy=Decimal(str(skill_confidences['empathy'])),
            confidence_adaptability=Decimal(str(skill_confidences['adaptability'])),
            confidence_collaboration=Decimal(str(skill_confidences['collaboration'])),
            confidence_communication=Decimal(str(skill_confidences['communication'])),
            confidence_self_regulation=Decimal(str(skill_confidences['self_regulation'])),
        )

        session.add(assessment)
        await session.flush()

        # Add evidence records
        evidence_records = []
        for skill_name, evidence_items in skill_evidence.items():
            for item in evidence_items[:3]:  # Top 3 pieces of evidence per skill
                evidence_record = Evidence(
                    assessment_id=assessment.assessment_id,
                    skill=skill_name,
                    span_text=item.span_text,
                    span_location=item.location,
                    score_contrib=Decimal(str(item.score_contribution)),
                    rationale=item.rationale or f"Evidence of {skill_name}"
                )
                evidence_records.append(evidence_record)

        session.add_all(evidence_records)
        await session.commit()

        print(f"\n💾 Saved to database:")
        print(f"  Assessment ID: {assessment.assessment_id}")
        print(f"  Evidence records: {len(evidence_records)}")

        return {
            'student': student,
            'assessment': assessment,
            'evidence_count': len(evidence_records),
            'transcript_file': filepath.name
        }


async def generate_summary_report(results):
    """Generate a comprehensive summary report"""

    print(f"\n{'='*70}")
    print("COMPREHENSIVE ASSESSMENT SUMMARY")
    print(f"{'='*70}")

    async with AsyncSessionLocal() as session:
        # Get all assessments
        assessment_result = await session.execute(
            select(Assessment).order_by(Assessment.created_at.desc())
        )
        assessments = assessment_result.scalars().all()

        print(f"\n📊 Total Assessments: {len(assessments)}")

        # Group by student
        student_assessments = {}
        for assessment in assessments:
            if assessment.student_id not in student_assessments:
                student_assessments[assessment.student_id] = []
            student_assessments[assessment.student_id].append(assessment)

        # Display per student
        for student_id, student_assmts in student_assessments.items():
            student_result = await session.execute(
                select(Student).where(Student.student_id == student_id)
            )
            student = student_result.scalars().first()

            print(f"\n{'─'*70}")
            print(f"Student: {student.name}")
            print(f"Class: {student.class_id}")
            print(f"Assessments: {len(student_assmts)}")
            print(f"{'─'*70}")

            # Latest assessment
            latest = student_assmts[0]

            print(f"\nLatest Assessment ({latest.assessed_on}):")
            print(f"  {'Skill':<20} {'Score':<10} {'Confidence'}")
            print(f"  {'-'*45}")
            print(f"  {'Empathy':<20} {float(latest.empathy):<10.1f} {float(latest.confidence_empathy):.2f}")
            print(f"  {'Adaptability':<20} {float(latest.adaptability):<10.1f} {float(latest.confidence_adaptability):.2f}")
            print(f"  {'Collaboration':<20} {float(latest.collaboration):<10.1f} {float(latest.confidence_collaboration):.2f}")
            print(f"  {'Communication':<20} {float(latest.communication):<10.1f} {float(latest.confidence_communication):.2f}")
            print(f"  {'Self-regulation':<20} {float(latest.self_regulation):<10.1f} {float(latest.confidence_self_regulation):.2f}")

            # Get evidence
            evidence_result = await session.execute(
                select(Evidence).where(Evidence.assessment_id == latest.assessment_id)
            )
            evidence_items = evidence_result.scalars().all()

            print(f"\nSupporting Evidence ({len(evidence_items)} items):")

            # Group by skill
            by_skill = {}
            for ev in evidence_items:
                if ev.skill not in by_skill:
                    by_skill[ev.skill] = []
                by_skill[ev.skill].append(ev)

            for skill_name in sorted(by_skill.keys()):
                skill_evidence = by_skill[skill_name]
                print(f"\n  {skill_name.upper()}:")
                for ev in skill_evidence[:2]:  # Show top 2
                    print(f"    • \"{ev.span_text}\"")
                    print(f"      → {ev.rationale}")
                    print(f"      → Score contribution: {float(ev.score_contrib):.2f}")


async def main():
    """Main processing function"""

    print("="*70)
    print("ASSESSMAX - COMPREHENSIVE TRANSCRIPT PROCESSING")
    print("="*70)

    # Initialize NLP pipeline
    print("\n🔧 Initializing NLP pipeline...")
    pipeline = NLPPipeline()
    print("✅ Pipeline ready")

    # Find all transcript files
    test_data_dir = Path("test_data")
    transcript_files = sorted(test_data_dir.glob("transcript_*.jsonl"))

    print(f"\n📁 Found {len(transcript_files)} transcript files:")
    for tf in transcript_files:
        print(f"  • {tf.name}")

    # Process each transcript
    results = []
    for transcript_file in transcript_files:
        result = await process_transcript_file(transcript_file, pipeline)
        if result:
            results.append(result)

    # Generate summary report
    await generate_summary_report(results)

    print(f"\n{'='*70}")
    print(f"✅ PROCESSING COMPLETE")
    print(f"{'='*70}")
    print(f"Transcripts processed: {len(results)}")
    print(f"Assessments created: {len(results)}")
    print(f"Database: Updated successfully")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
