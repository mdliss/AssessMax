"""LLM-based evidence extraction for SEL skills"""

import json
import logging
import os
from typing import Dict, List, Optional
from dataclasses import dataclass

from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class SELEvidence:
    """Evidence of a SEL skill demonstration"""
    skill: str
    quote: str
    rationale: str
    score_contribution: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0


class LLMEvidenceExtractor:
    """
    Use OpenAI (GPT-4) to extract and score SEL skill evidence from conversation transcripts.

    This provides much more nuanced and context-aware analysis than keyword matching.
    """

    SKILL_DEFINITIONS = {
        "empathy": "Understanding and sharing others' feelings, showing care and concern for others' emotional experiences",
        "adaptability": "Adjusting to new situations, being flexible when plans change, trying different approaches when needed",
        "collaboration": "Working effectively with others, sharing ideas, helping teammates, contributing to group success",
        "communication": "Expressing ideas clearly, actively listening, asking clarifying questions, articulating thoughts effectively",
        "self_regulation": "Managing emotions appropriately, staying calm under pressure, maintaining focus, controlling impulses"
    }

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize LLM evidence extractor.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use (default: gpt-4o)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def extract_evidence_for_student(
        self,
        transcript_text: str,
        student_name: str,
        skills: Optional[List[str]] = None
    ) -> Dict[str, List[SELEvidence]]:
        """
        Extract SEL skill evidence for a specific student from a transcript.

        Args:
            transcript_text: Full conversation transcript
            student_name: Name of student to analyze
            skills: List of skills to analyze (defaults to all 5 SEL skills)

        Returns:
            Dictionary mapping skill names to lists of evidence
        """
        if skills is None:
            skills = list(self.SKILL_DEFINITIONS.keys())

        logger.info(f"Extracting SEL evidence for {student_name} using OpenAI {self.model}")

        # Build the analysis prompt
        prompt = self._build_analysis_prompt(transcript_text, student_name, skills)

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in Social-Emotional Learning (SEL) assessment. You analyze classroom conversations to identify evidence of SEL skills."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )

            # Parse response
            response_text = response.choices[0].message.content
            evidence_dict = self._parse_response(response_text, student_name)

            logger.info(f"Successfully extracted evidence for {student_name}: {len(evidence_dict)} skills analyzed")
            return evidence_dict

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            # Return empty evidence on error
            return {skill: [] for skill in skills}

    def _build_analysis_prompt(
        self,
        transcript_text: str,
        student_name: str,
        skills: List[str]
    ) -> str:
        """Build the prompt for OpenAI to analyze the transcript"""

        skill_descriptions = "\n".join([
            f"- **{skill.upper()}**: {self.SKILL_DEFINITIONS[skill]}"
            for skill in skills
        ])

        prompt = f"""Analyze the following classroom conversation transcript and identify specific evidence of SEL skills demonstrated by the student "{student_name}".

SEL Skills to assess:
{skill_descriptions}

TRANSCRIPT:
{transcript_text}

INSTRUCTIONS:
1. For each SEL skill, identify 2-5 specific quotes where {student_name} demonstrates that skill
2. Provide a clear rationale explaining WHY each quote demonstrates the skill
3. Rate each piece of evidence with a score_contribution (0.0-1.0) indicating how strongly it demonstrates the skill
4. Rate your confidence (0.0-1.0) in each assessment
5. ONLY include quotes that are actually spoken by {student_name}
6. If {student_name} doesn't demonstrate a particular skill, return an empty list for that skill

Return your response as a JSON object with this structure:
{{
  "empathy": [
    {{
      "quote": "exact quote from {student_name}",
      "rationale": "explanation of why this demonstrates empathy",
      "score_contribution": 0.85,
      "confidence": 0.90
    }}
  ],
  "adaptability": [...],
  "collaboration": [...],
  "communication": [...],
  "self_regulation": [...]
}}"""

        return prompt

    def _parse_response(self, response_text: str, student_name: str) -> Dict[str, List[SELEvidence]]:
        """Parse Claude's JSON response into structured evidence"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            data = json.loads(response_text)

            evidence_dict = {}

            for skill in self.SKILL_DEFINITIONS.keys():
                evidence_list = []

                if skill in data and isinstance(data[skill], list):
                    for item in data[skill]:
                        try:
                            evidence = SELEvidence(
                                skill=skill,
                                quote=item.get("quote", ""),
                                rationale=item.get("rationale", ""),
                                score_contribution=float(item.get("score_contribution", 0.5)),
                                confidence=float(item.get("confidence", 0.5))
                            )
                            evidence_list.append(evidence)
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Skipping invalid evidence item: {e}")
                            continue

                evidence_dict[skill] = evidence_list

            return evidence_dict

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            logger.debug(f"Response text: {response_text}")
            return {skill: [] for skill in self.SKILL_DEFINITIONS.keys()}
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return {skill: [] for skill in self.SKILL_DEFINITIONS.keys()}

    def calculate_skill_scores(
        self,
        evidence_dict: Dict[str, List[SELEvidence]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate overall skill scores from evidence.

        Args:
            evidence_dict: Dictionary of skill -> evidence list

        Returns:
            Dictionary with skill scores and confidence levels
        """
        scores = {}

        for skill, evidence_list in evidence_dict.items():
            if not evidence_list:
                # No evidence = neutral score
                scores[skill] = {
                    "score": 5.0,  # Neutral on 0-10 scale
                    "confidence": 0.3,
                    "evidence_count": 0
                }
            else:
                # Calculate weighted average based on score_contribution
                total_contribution = sum(e.score_contribution for e in evidence_list)
                avg_contribution = total_contribution / len(evidence_list)

                # Scale to 0-10 (0.5 contribution = 5.0, 1.0 contribution = 10.0)
                score = avg_contribution * 10.0

                # Confidence is average of individual confidences
                avg_confidence = sum(e.confidence for e in evidence_list) / len(evidence_list)

                # Boost confidence slightly with more evidence
                confidence_boost = min(0.1 * len(evidence_list), 0.2)
                final_confidence = min(avg_confidence + confidence_boost, 1.0)

                scores[skill] = {
                    "score": round(score, 1),
                    "confidence": round(final_confidence, 2),
                    "evidence_count": len(evidence_list)
                }

        return scores

    def extract_and_score_student(
        self,
        transcript_text: str,
        student_name: str,
        skills: Optional[List[str]] = None
    ) -> tuple[Dict[str, List[SELEvidence]], Dict[str, Dict[str, float]]]:
        """
        Extract evidence and calculate scores in one call.

        Returns:
            Tuple of (evidence_dict, scores_dict)
        """
        evidence_dict = self.extract_evidence_for_student(transcript_text, student_name, skills)
        scores_dict = self.calculate_skill_scores(evidence_dict)

        return evidence_dict, scores_dict
