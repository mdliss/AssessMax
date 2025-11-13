"""Test LLM-based SEL skill scoring on sample transcripts"""
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


async def get_student_previous_scores(student_id: UUID) -> dict:
    """Get previous assessment scores for comparison"""
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
        }


async def analyze_transcript(filepath: Path, extractor: LLMEvidenceExtractor):
    """Analyze a single transcript file"""

    print(f"\n{'='*80}")
    print(f"Analyzing: {filepath.name}")
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
    for sid, name in student_data.items():
        print(f"  • {name} ({sid})")

    # Build full transcript text
    transcript_text = "\n".join([
        f"{item.get('speaker', 'Unknown')}: {item.get('text', '')}"
        for item in transcript_lines
    ])

    print(f"\n📝 Transcript length: {len(transcript_text)} characters")

    # Analyze each student
    for student_id, student_name in student_data.items():
        print(f"\n{'─'*80}")
        print(f"🎓 Analyzing: {student_name}")
        print(f"{'─'*80}")

        # Get utterance count
        utterances = [item for item in transcript_lines if item.get('student_id') == str(student_id)]
        total_words = sum(len(item.get('text', '').split()) for item in utterances)

        print(f"  Utterances: {len(utterances)}")
        print(f"  Words spoken: {total_words}")

        # Get previous scores
        previous_scores = await get_student_previous_scores(student_id)

        # Extract evidence and calculate scores using LLM
        print(f"\n  🤖 Calling Claude API for evidence extraction...")
        evidence_dict, scores_dict = extractor.extract_and_score_student(
            transcript_text,
            student_name
        )

        # Display results
        print(f"\n  📊 SEL Skill Assessment:")
        print(f"  {'─'*70}")
        print(f"  {'Skill':<20} {'Before':<10} {'New':<10} {'Change':<10} {'Evidence'}")
        print(f"  {'─'*70}")

        for skill in ['empathy', 'adaptability', 'collaboration', 'communication', 'self_regulation']:
            new_score = scores_dict[skill]['score']
            confidence = scores_dict[skill]['confidence']
            evidence_count = scores_dict[skill]['evidence_count']

            if previous_scores:
                before_score = previous_scores[skill]
                change = new_score - before_score
                change_str = f"{change:+.1f}"
                before_str = f"{before_score:.1f}"
            else:
                change_str = "NEW"
                before_str = "N/A"

            print(f"  {skill.capitalize():<20} {before_str:<10} {new_score:<10.1f} {change_str:<10} {evidence_count} items (conf: {confidence:.2f})")

        # Show evidence details
        print(f"\n  💡 Evidence Examples:")
        for skill, evidence_list in evidence_dict.items():
            if evidence_list:
                print(f"\n    {skill.upper()}:")
                for i, evidence in enumerate(evidence_list[:2], 1):  # Show top 2
                    quote_display = evidence.quote if len(evidence.quote) <= 80 else evidence.quote[:77] + "..."
                    print(f"      {i}. \"{quote_display}\"")
                    print(f"         → {evidence.rationale}")
                    print(f"         → Score: {evidence.score_contribution:.2f}, Confidence: {evidence.confidence:.2f}")


async def main():
    """Main test function"""

    print("="*80)
    print("LLM-BASED SEL SKILL ASSESSMENT TEST")
    print("Using Claude to extract evidence from classroom conversations")
    print("="*80)

    # Initialize LLM extractor
    print("\n🔧 Initializing LLM Evidence Extractor...")
    try:
        extractor = LLMEvidenceExtractor()
        print("✅ LLM Extractor ready (using OpenAI GPT-4o)")
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\nPlease set OPENAI_API_KEY environment variable")
        return

    # Find transcript files
    test_data_dir = Path("test_data")
    transcript_files = sorted([
        f for f in test_data_dir.glob("transcript_class_*.jsonl")
    ])

    print(f"\n📁 Found {len(transcript_files)} transcript files:")
    for i, tf in enumerate(transcript_files, 1):
        print(f"  {i}. {tf.name}")

    # Analyze first transcript as a demo
    print(f"\n🎯 Running analysis on first transcript as demonstration...\n")

    if transcript_files:
        await analyze_transcript(transcript_files[0], extractor)
    else:
        print("❌ No transcript files found!")

    print(f"\n{'='*80}")
    print("✅ ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print("\nInterpretation Guide:")
    print("  • Evidence count shows how many examples Claude found for each skill")
    print("  • Scores (0-10) reflect the quality and frequency of skill demonstrations")
    print("  • Confidence (0-1) indicates how certain Claude is about the assessment")
    print("  • High scores should correlate with strong, clear demonstrations in the text")
    print("  • Changes from 'Before' show how new transcript data affects assessments")
    print(f"{'='*80}")

    # Option to analyze all
    print("\n💡 To analyze all transcripts, modify the script to loop through transcript_files")


if __name__ == "__main__":
    asyncio.run(main())
