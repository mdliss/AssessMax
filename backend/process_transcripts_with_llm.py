"""Process transcripts using LLM-based evidence extraction and save to database"""
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
from app.nlp import LLMEvidenceExtractor


async def process_transcript_file(filepath: Path, extractor: LLMEvidenceExtractor):
    """Process a single transcript file and save assessments to database"""

    print(f"\n{'='*80}")
    print(f"Processing: {filepath.name}")
    print(f"{'='*80}")

    # Load transcript
    transcript_lines = []
    with open(filepath) as f:
        for line in f:
            transcript_lines.append(json.loads(line))

    # Get unique students from transcript
    student_data = {}
    for item in transcript_lines:
        sid = item.get('student_id')
        speaker = item.get('speaker')
        if sid and speaker != "Teacher":
            student_data[UUID(sid)] = speaker

    print(f"\n📋 Students in transcript: {len(student_data)}")

    # Build full transcript text
    transcript_text = "\n".join([
        f"{item.get('speaker', 'Unknown')}: {item.get('text', '')}"
        for item in transcript_lines
    ])

    # Process each student
    results = []
    for student_id, student_name in student_data.items():
        print(f"\n{'─'*70}")
        print(f"Processing: {student_name}")

        # Get student from database
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Student).where(Student.student_id == student_id)
            )
            student = result.scalars().first()

            if not student:
                print(f"❌ Student {student_name} ({student_id}) not found in database")
                continue

            print(f"✅ Student found: {student.name} - Class: {student.class_id}")

        # Extract evidence using LLM
        print(f"🤖 Analyzing with Claude...")
        evidence_dict, scores_dict = extractor.extract_and_score_student(
            transcript_text,
            student_name
        )

        # Print results
        print(f"\n📊 SEL Scores:")
        for skill in ['empathy', 'adaptability', 'collaboration', 'communication', 'self_regulation']:
            score = scores_dict[skill]['score']
            confidence = scores_dict[skill]['confidence']
            evidence_count = scores_dict[skill]['evidence_count']
            print(f"  {skill.capitalize():<20} {score:.1f}/10 (confidence: {confidence:.2f}, evidence: {evidence_count})")

        # Save to database
        async with AsyncSessionLocal() as session:
            # Create assessment
            assessment = Assessment(
                student_id=student.student_id,
                class_id=student.class_id,
                assessed_on=date.today(),
                model_version='llm-1.0.0',
                empathy=Decimal(str(scores_dict['empathy']['score'])),
                adaptability=Decimal(str(scores_dict['adaptability']['score'])),
                collaboration=Decimal(str(scores_dict['collaboration']['score'])),
                communication=Decimal(str(scores_dict['communication']['score'])),
                self_regulation=Decimal(str(scores_dict['self_regulation']['score'])),
                confidence_empathy=Decimal(str(scores_dict['empathy']['confidence'])),
                confidence_adaptability=Decimal(str(scores_dict['adaptability']['confidence'])),
                confidence_collaboration=Decimal(str(scores_dict['collaboration']['confidence'])),
                confidence_communication=Decimal(str(scores_dict['communication']['confidence'])),
                confidence_self_regulation=Decimal(str(scores_dict['self_regulation']['confidence'])),
            )

            session.add(assessment)
            await session.flush()

            # Add evidence records
            evidence_records = []
            for skill, evidence_list in evidence_dict.items():
                for evidence_item in evidence_list[:3]:  # Top 3 pieces per skill
                    evidence_record = Evidence(
                        assessment_id=assessment.assessment_id,
                        skill=skill,
                        span_text=evidence_item.quote,
                        span_location="transcript",
                        score_contrib=Decimal(str(evidence_item.score_contribution)),
                        rationale=evidence_item.rationale
                    )
                    evidence_records.append(evidence_record)

            session.add_all(evidence_records)
            await session.commit()

            print(f"💾 Saved assessment {assessment.assessment_id} with {len(evidence_records)} evidence records")

        results.append({
            'student': student,
            'assessment_id': assessment.assessment_id,
            'evidence_count': len(evidence_records)
        })

    return results


async def main():
    """Main processing function"""

    print("="*80)
    print("LLM-BASED TRANSCRIPT PROCESSING")
    print("Process transcripts and save SEL assessments to database")
    print("="*80)

    # Initialize LLM extractor
    print("\n🔧 Initializing LLM Evidence Extractor...")
    try:
        extractor = LLMEvidenceExtractor()
        print("✅ LLM Extractor ready (using OpenAI GPT-4o)")
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\nPlease set OPENAI_API_KEY environment variable")
        print("Usage: OPENAI_API_KEY=your-key-here python process_transcripts_with_llm.py")
        return

    # Find all transcript files
    test_data_dir = Path("test_data")
    transcript_files = sorted([
        f for f in test_data_dir.glob("transcript_class_*.jsonl")
    ])

    print(f"\n📁 Found {len(transcript_files)} transcript files:")
    for i, tf in enumerate(transcript_files, 1):
        print(f"  {i}. {tf.name}")

    # Process each transcript
    all_results = []
    for transcript_file in transcript_files:
        results = await process_transcript_file(transcript_file, extractor)
        all_results.extend(results)

    # Summary
    print(f"\n{'='*80}")
    print(f"✅ PROCESSING COMPLETE")
    print(f"{'='*80}")
    print(f"Transcripts processed: {len(transcript_files)}")
    print(f"Assessments created: {len(all_results)}")
    print(f"Students assessed: {len(set(r['student'].student_id for r in all_results))}")
    print(f"Total evidence records: {sum(r['evidence_count'] for r in all_results)}")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())
