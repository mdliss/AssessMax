"""Test script to verify transcript processing affects student scores reasonably"""
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


async def get_student_scores(student_id: UUID) -> dict:
    """Get current scores for a student"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Assessment)
            .where(Assessment.student_id == student_id)
            .order_by(Assessment.created_at.desc())
        )
        latest = result.scalars().first()

        if not latest:
            return None

        return {
            'empathy': float(latest.empathy),
            'adaptability': float(latest.adaptability),
            'collaboration': float(latest.collaboration),
            'communication': float(latest.communication),
            'self_regulation': float(latest.self_regulation),
            'assessed_on': latest.assessed_on,
            'assessment_id': latest.assessment_id
        }


async def process_and_compare_transcript(filepath: Path, pipeline: NLPPipeline):
    """Process a transcript and compare before/after scores"""

    print(f"\n{'='*80}")
    print(f"Processing: {filepath.name}")
    print(f"{'='*80}")

    # Load transcript
    transcript_lines = []
    with open(filepath) as f:
        for line in f:
            transcript_lines.append(json.loads(line))

    # Get unique students from transcript
    student_ids = set()
    student_names = {}
    for item in transcript_lines:
        sid = item.get('student_id')
        if sid:
            student_ids.add(UUID(sid))
            student_names[UUID(sid)] = item.get('speaker')

    print(f"\n📋 Students in transcript: {len(student_ids)}")

    # Get before scores
    before_scores = {}
    for student_id in student_ids:
        scores = await get_student_scores(student_id)
        before_scores[student_id] = scores
        name = student_names.get(student_id, str(student_id))
        if scores:
            print(f"  • {name}: Has existing assessment from {scores['assessed_on']}")
        else:
            print(f"  • {name}: No existing assessments")

    # Build full text
    full_text = "\n".join([
        f"{item.get('speaker', 'Unknown')}: {item.get('text', '')}"
        for item in transcript_lines
    ])

    # Process with NLP
    print(f"\n🔄 Processing transcript...")
    result = pipeline.process_transcript(full_text)

    # Initialize extractors
    skill_detector = SkillDetector()
    evidence_extractor = EvidenceExtractor()

    # Process each student
    for student_id in student_ids:
        student_name = student_names.get(student_id)
        print(f"\n{'─'*80}")
        print(f"Student: {student_name}")
        print(f"{'─'*80}")

        # Get student's utterances
        student_text = "\n".join([
            item.get('text', '')
            for item in transcript_lines
            if item.get('student_id') == str(student_id)
        ])

        utterance_count = sum(1 for item in transcript_lines if item.get('student_id') == str(student_id))
        print(f"Utterances in transcript: {utterance_count}")
        print(f"Total words spoken: {len(student_text.split())}")

        # Calculate new skill scores
        new_scores = {}
        evidence_details = {}

        for skill_name in ['empathy', 'adaptability', 'collaboration', 'communication', 'self_regulation']:
            # Extract evidence
            evidence_items = evidence_extractor.extract_from_transcript(
                full_text,
                skill_name,
                student_id=student_name
            )

            evidence_details[skill_name] = evidence_items

            # Calculate score
            if evidence_items:
                avg_score = sum(e.score_contribution for e in evidence_items) / len(evidence_items)
                new_scores[skill_name] = min(10.0, avg_score * 10)
            else:
                new_scores[skill_name] = 5.0

        # Compare with before
        before = before_scores.get(student_id)

        print(f"\n📊 Score Analysis:")
        print(f"{'Skill':<20} {'Before':<10} {'After':<10} {'Change':<10} {'Evidence'}")
        print(f"{'-'*70}")

        for skill_name in ['empathy', 'adaptability', 'collaboration', 'communication', 'self_regulation']:
            before_score = before[skill_name] if before else None
            after_score = new_scores[skill_name]
            evidence_count = len(evidence_details[skill_name])

            if before_score is not None:
                change = after_score - before_score
                change_str = f"{change:+.1f}"
                before_str = f"{before_score:.1f}"
            else:
                change_str = "NEW"
                before_str = "N/A"

            print(f"{skill_name.capitalize():<20} {before_str:<10} {after_score:<10.1f} {change_str:<10} {evidence_count} items")

        # Show evidence examples
        print(f"\n💡 Evidence Examples:")
        for skill_name, items in evidence_details.items():
            if items:
                print(f"\n  {skill_name.upper()}:")
                for item in items[:2]:  # Show top 2
                    print(f"    • \"{item.span_text[:80]}...\"" if len(item.span_text) > 80 else f"    • \"{item.span_text}\"")
                    print(f"      Score contribution: {item.score_contribution:.2f}")
                    if item.rationale:
                        print(f"      Rationale: {item.rationale}")


async def main():
    """Main test function"""

    print("="*80)
    print("TRANSCRIPT IMPACT ANALYSIS")
    print("Testing if transcripts reasonably affect student scores")
    print("="*80)

    # Initialize NLP pipeline
    print("\n🔧 Initializing NLP pipeline...")
    pipeline = NLPPipeline()
    print("✅ Pipeline ready")

    # Find all new transcript files
    test_data_dir = Path("test_data")
    transcript_files = sorted([
        f for f in test_data_dir.glob("transcript_class_*.jsonl")
    ])

    print(f"\n📁 Found {len(transcript_files)} class transcript files")

    # Let user choose which to test
    print("\nAvailable transcripts:")
    for i, tf in enumerate(transcript_files, 1):
        print(f"  {i}. {tf.name}")

    print("\n🔍 Analyzing all transcripts...\n")

    # Process each transcript
    for transcript_file in transcript_files:
        await process_and_compare_transcript(transcript_file, pipeline)

    print(f"\n{'='*80}")
    print("✅ ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print("\nInterpretation Guide:")
    print("  • Evidence count shows how many examples were found for each skill")
    print("  • Scores should reflect the conversation content reasonably")
    print("  • High collaboration scores = students working together well")
    print("  • High communication scores = clear, articulate expression")
    print("  • High empathy scores = understanding others' perspectives")
    print("  • Changes from 'Before' show if new data affects existing assessments")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())
