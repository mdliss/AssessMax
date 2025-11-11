"""Skill cue detection and scoring module"""

import logging
import random
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class SkillDetector:
    """
    Detect and score non-academic skills from text.

    Skills:
    - Empathy: Understanding and sharing others' feelings
    - Adaptability: Adjusting to new situations and changes
    - Collaboration: Working effectively with others
    - Communication: Expressing ideas clearly
    - Self-regulation: Managing emotions and behavior
    """

    # Skill keywords and patterns (simplified for MVP)
    SKILL_PATTERNS = {
        "empathy": {
            "keywords": [
                "understand", "feel", "sorry", "care", "help", "support",
                "sympathy", "compassion", "concern", "comfort", "listen"
            ],
            "phrases": [
                "i understand", "i feel", "must be hard", "can imagine",
                "how do you feel", "sorry to hear", "are you okay"
            ],
        },
        "adaptability": {
            "keywords": [
                "change", "adapt", "adjust", "flexible", "different", "new way",
                "try", "alternative", "modify", "switch", "pivot"
            ],
            "phrases": [
                "let's try", "different approach", "change our plan",
                "adapt to", "adjust our", "be flexible", "new strategy"
            ],
        },
        "collaboration": {
            "keywords": [
                "together", "team", "group", "cooperate", "work with", "help each other",
                "share", "collaborate", "partner", "join", "contribute"
            ],
            "phrases": [
                "let's work together", "as a team", "help each other",
                "work with", "collaborate on", "share ideas", "team effort"
            ],
        },
        "communication": {
            "keywords": [
                "explain", "clarify", "describe", "tell", "ask", "discuss",
                "share", "express", "articulate", "present", "communicate"
            ],
            "phrases": [
                "let me explain", "can you clarify", "what do you mean",
                "in other words", "to put it simply", "my point is"
            ],
        },
        "self_regulation": {
            "keywords": [
                "calm", "control", "patient", "wait", "focus", "manage",
                "think", "breathe", "relax", "compose", "steady"
            ],
            "phrases": [
                "need to focus", "stay calm", "take a breath", "control myself",
                "be patient", "think before", "manage my", "keep it together"
            ],
        },
    }

    def __init__(self, seed: int = 42) -> None:
        """
        Initialize skill detector with deterministic seed.

        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)

        # Pre-compute skill pattern sets for efficiency
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile skill patterns into efficient lookup structures"""
        self.keyword_sets = {}
        self.phrase_sets = {}

        for skill, patterns in self.SKILL_PATTERNS.items():
            self.keyword_sets[skill] = set(kw.lower() for kw in patterns["keywords"])
            self.phrase_sets[skill] = [phrase.lower() for phrase in patterns["phrases"]]

    def detect_skills(
        self, text: str, speaker_role: str = "student", context: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Detect skill cues in text and provide scores.

        Args:
            text: Input text to analyze
            speaker_role: Role of speaker (student, teacher, unknown)
            context: Additional context (previous sentences, topic, etc.)

        Returns:
            Dictionary with skill scores and evidence

        Example:
            >>> detector = SkillDetector()
            >>> result = detector.detect_skills(
            ...     "I understand how you feel. Let's work together on this.",
            ...     speaker_role="student"
            ... )
            >>> print(result)
            {
                'empathy': {'score': 0.85, 'confidence': 0.9, 'evidence': [...]},
                'collaboration': {'score': 0.75, 'confidence': 0.85, 'evidence': [...]}
            }
        """
        text_lower = text.lower()
        results = {}

        for skill in self.SKILL_PATTERNS.keys():
            skill_result = self._detect_single_skill(text, text_lower, skill, speaker_role)

            if skill_result["detected"]:
                results[skill] = {
                    "score": skill_result["score"],
                    "confidence": skill_result["confidence"],
                    "evidence": skill_result["evidence"],
                    "cue_count": skill_result["cue_count"],
                }

        return results

    def _detect_single_skill(
        self, text: str, text_lower: str, skill: str, speaker_role: str
    ) -> Dict[str, any]:
        """
        Detect a single skill in text.

        Args:
            text: Original text
            text_lower: Lowercased text
            skill: Skill to detect
            speaker_role: Speaker role

        Returns:
            Detection result
        """
        evidence = []
        cue_count = 0

        # Check for keyword matches
        words = text_lower.split()
        for word in words:
            if word in self.keyword_sets[skill]:
                evidence.append({
                    "type": "keyword",
                    "match": word,
                    "span": self._find_span(text_lower, word),
                })
                cue_count += 1

        # Check for phrase matches
        for phrase in self.phrase_sets[skill]:
            if phrase in text_lower:
                evidence.append({
                    "type": "phrase",
                    "match": phrase,
                    "span": self._find_span(text_lower, phrase),
                })
                cue_count += 1

        if cue_count == 0:
            return {"detected": False, "score": 0.0, "confidence": 0.0, "evidence": [], "cue_count": 0}

        # Calculate score based on cues and context
        base_score = min(0.5 + (cue_count * 0.15), 1.0)

        # Adjust for speaker role (students get higher weight)
        if speaker_role == "student":
            base_score = min(base_score * 1.1, 1.0)

        # Calculate confidence based on evidence strength
        confidence = min(0.6 + (cue_count * 0.1), 0.95)

        return {
            "detected": True,
            "score": round(base_score, 3),
            "confidence": round(confidence, 3),
            "evidence": evidence[:5],  # Limit to top 5 pieces of evidence
            "cue_count": cue_count,
        }

    def _find_span(self, text: str, pattern: str) -> Tuple[int, int]:
        """
        Find character span of pattern in text.

        Args:
            text: Text to search
            pattern: Pattern to find

        Returns:
            Tuple of (start, end) positions
        """
        start = text.find(pattern)
        if start == -1:
            return (0, 0)
        return (start, start + len(pattern))

    def score_conversation(
        self, sentences: List[Dict[str, str]], student_ids: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, any]]:
        """
        Score skills across an entire conversation.

        Args:
            sentences: List of sentence segments with speaker information
            student_ids: Optional list of student IDs to focus on

        Returns:
            Dictionary of student skill scores

        Example:
            >>> detector = SkillDetector()
            >>> sentences = [
            ...     {'text': 'I feel sorry for him', 'speaker_id': 'student_a', 'speaker_role': 'student'},
            ...     {'text': 'Let's help him together', 'speaker_id': 'student_b', 'speaker_role': 'student'}
            ... ]
            >>> scores = detector.score_conversation(sentences)
        """
        # Aggregate scores by student
        student_scores = {}

        for sentence in sentences:
            speaker_id = sentence.get("speaker_id", "unknown")
            speaker_role = sentence.get("speaker_role", "unknown")
            text = sentence.get("text", "")

            # Skip if not a student or not in focus list
            if speaker_role != "student":
                continue

            if student_ids and speaker_id not in student_ids:
                continue

            # Initialize student scores
            if speaker_id not in student_scores:
                student_scores[speaker_id] = {
                    "empathy": {"scores": [], "evidence": []},
                    "adaptability": {"scores": [], "evidence": []},
                    "collaboration": {"scores": [], "evidence": []},
                    "communication": {"scores": [], "evidence": []},
                    "self_regulation": {"scores": [], "evidence": []},
                }

            # Detect skills in this sentence
            detected_skills = self.detect_skills(text, speaker_role)

            # Accumulate evidence
            for skill, result in detected_skills.items():
                student_scores[speaker_id][skill]["scores"].append(result["score"])
                student_scores[speaker_id][skill]["evidence"].extend(result["evidence"])

        # Calculate final aggregated scores
        final_scores = {}
        for student_id, skills in student_scores.items():
            final_scores[student_id] = {}

            for skill, data in skills.items():
                if data["scores"]:
                    # Average score with slight boost for multiple demonstrations
                    avg_score = np.mean(data["scores"])
                    demonstration_count = len(data["scores"])
                    boosted_score = min(avg_score * (1 + demonstration_count * 0.02), 1.0)

                    final_scores[student_id][skill] = {
                        "score": round(boosted_score, 3),
                        "confidence": round(min(0.7 + demonstration_count * 0.05, 0.95), 3),
                        "demonstration_count": demonstration_count,
                        "evidence_count": len(data["evidence"]),
                        "top_evidence": data["evidence"][:3],  # Top 3 pieces of evidence
                    }
                else:
                    # No evidence for this skill
                    final_scores[student_id][skill] = {
                        "score": 0.0,
                        "confidence": 0.0,
                        "demonstration_count": 0,
                        "evidence_count": 0,
                        "top_evidence": [],
                    }

        return final_scores

    def extract_evidence_spans(
        self, text: str, skill: str, max_spans: int = 5
    ) -> List[Dict[str, any]]:
        """
        Extract evidence spans for a specific skill.

        Args:
            text: Input text
            skill: Skill to extract evidence for
            max_spans: Maximum number of spans to return

        Returns:
            List of evidence spans with rationale
        """
        text_lower = text.lower()
        spans = []

        # Find keyword matches
        for keyword in self.keyword_sets[skill]:
            if keyword in text_lower:
                start, end = self._find_span(text_lower, keyword)
                spans.append({
                    "text": text[start:end],
                    "start": start,
                    "end": end,
                    "type": "keyword",
                    "skill": skill,
                    "rationale": f"Keyword '{keyword}' indicates {skill}",
                })

        # Find phrase matches
        for phrase in self.phrase_sets[skill]:
            if phrase in text_lower:
                start, end = self._find_span(text_lower, phrase)
                spans.append({
                    "text": text[start:end],
                    "start": start,
                    "end": end,
                    "type": "phrase",
                    "skill": skill,
                    "rationale": f"Phrase '{phrase}' demonstrates {skill}",
                })

        # Sort by relevance (phrases are more relevant than keywords)
        spans.sort(key=lambda x: (x["type"] == "phrase", x["end"] - x["start"]), reverse=True)

        return spans[:max_spans]

    def get_supported_skills(self) -> List[str]:
        """
        Get list of supported skill names.

        Returns:
            List of skill identifiers
        """
        return list(self.SKILL_PATTERNS.keys())

    def get_skill_description(self, skill: str) -> str:
        """
        Get human-readable description of a skill.

        Args:
            skill: Skill identifier

        Returns:
            Skill description
        """
        descriptions = {
            "empathy": "Understanding and sharing others' feelings",
            "adaptability": "Adjusting to new situations and changes",
            "collaboration": "Working effectively with others",
            "communication": "Expressing ideas clearly and effectively",
            "self_regulation": "Managing emotions and behavior appropriately",
        }
        return descriptions.get(skill, "Unknown skill")
