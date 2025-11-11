"""Test the NLP pipeline end-to-end"""
import asyncio
import json
from datetime import datetime
from uuid import UUID

from app.database import AsyncSessionLocal
from app.models.assessment import Assessment
from app.models.evidence import Evidence
from app.nlp import NLPPipeline

# Define the five skills
SKILLS = ["empathy", "adaptability", "collaboration", "communication", "self_regulation"]


async def test_nlp_pipeline():
    """Test processing a transcript through the NLP pipeline"""

    # Load transcript
    transcript_file = "test_data/transcript_emma_1.jsonl"
    print(f"📂 Loading transcript: {transcript_file}")

    with open(transcript_file, 'r') as f:
        lines = f.readlines()
        transcript_data = [json.loads(line) for line in lines]

    # Combine all utterances into full text
    full_text = "\n".join([f"{item['speaker']}: {item['text']}" for item in transcript_data])
    print(f"📝 Transcript has {len(transcript_data)} utterances")
    print(f"📏 Total length: {len(full_text)} characters")

    # Initialize NLP pipeline
    print("\n🔧 Initializing NLP pipeline...")
    pipeline = NLPPipeline()

    # Process transcript
    student_id = UUID('550e8400-e29b-41d4-a716-446655440001')  # Emma
    student_name = "Emma Johnson"

    print(f"\n🎯 Processing transcript for {student_name}...")
    result = pipeline.process_transcript(
        text=full_text,
        metadata={
            "student_id": str(student_id),
            "class_id": "MS-7A",
            "date": datetime.utcnow().isoformat()
        }
    )

    # Display results
    print("\n" + "="*60)
    print(f"📊 ASSESSMENT RESULTS FOR {student_name}")
    print("="*60)

    for skill in SKILLS:
        score = result["skill_scores"].get(skill, 0.0)
        confidence = result["confidence_scores"].get(skill, 0.0)
        evidence_count = len([e for e in result["evidence"] if e["skill"] == skill])

        print(f"\n{skill.upper()}")
        print(f"  Score: {score:.2f}/10")
        print(f"  Confidence: {confidence:.2%}")
        print(f"  Evidence spans: {evidence_count}")

    # Save to database
    print("\n💾 Saving assessment to database...")
    async with AsyncSessionLocal() as session:
        # Create assessment
        assessment = Assessment(
            student_id=student_id,
            class_id="MS-7A",
            assessed_on=datetime.utcnow().date(),
            empathy=result["skill_scores"].get("empathy", 0.0),
            adaptability=result["skill_scores"].get("adaptability", 0.0),
            collaboration=result["skill_scores"].get("collaboration", 0.0),
            communication=result["skill_scores"].get("communication", 0.0),
            self_regulation=result["skill_scores"].get("self_regulation", 0.0),
            confidence_empathy=result["confidence_scores"].get("empathy", 0.0),
            confidence_adaptability=result["confidence_scores"].get("adaptability", 0.0),
            confidence_collaboration=result["confidence_scores"].get("collaboration", 0.0),
            confidence_communication=result["confidence_scores"].get("communication", 0.0),
            confidence_self_regulation=result["confidence_scores"].get("self_regulation", 0.0),
        )
        session.add(assessment)
        await session.flush()  # Get the assessment_id

        # Create evidence records
        for evidence_data in result["evidence"][:20]:  # Limit to first 20 evidence spans
            evidence = Evidence(
                assessment_id=assessment.assessment_id,
                skill=evidence_data["skill"],
                text_span=evidence_data["text_span"],
                start_pos=evidence_data.get("start_pos", 0),
                end_pos=evidence_data.get("end_pos", 0),
                context=evidence_data.get("context", ""),
                score_contribution=evidence_data.get("score_contribution", 0.0),
                rationale=evidence_data.get("rationale", ""),
            )
            session.add(evidence)

        await session.commit()
        print(f"✅ Saved assessment ID: {assessment.assessment_id}")
        print(f"✅ Saved {len(result['evidence'][:20])} evidence spans")

    print("\n" + "="*60)
    print("✅ END-TO-END TEST COMPLETED SUCCESSFULLY")
    print("="*60)


if __name__ == '__main__':
    asyncio.run(test_nlp_pipeline())
