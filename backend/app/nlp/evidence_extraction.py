"""Evidence extraction and ranking module"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class EvidenceSpan:
    """
    A single evidence span with metadata.

    Attributes:
        text: The actual text span
        location: Location reference (e.g., "line 132-168", "page 3")
        rationale: Explanation of why this supports the skill
        score_contribution: Relevance score (0.0-1.0)
        skill: The skill this evidence supports
        span_type: Type of evidence (keyword, phrase, sentence, paragraph)
        start_char: Character start position in source
        end_char: Character end position in source
        context: Surrounding context for better understanding
    """

    text: str
    location: str
    rationale: str
    score_contribution: float
    skill: str
    span_type: str
    start_char: int
    end_char: int
    context: Optional[str] = None


class EvidenceExtractor:
    """
    Extract and rank evidence spans from transcripts and artifacts.

    This module:
    1. Extracts text spans that support skill assessments
    2. Ranks spans by relevance and quality
    3. Provides citations with line/page numbers
    4. Generates rationales for each evidence piece
    """

    def __init__(self, skill_detector=None):
        """
        Initialize evidence extractor.

        Args:
            skill_detector: Optional SkillDetector instance for skill-specific patterns
        """
        self.skill_detector = skill_detector

    def extract_from_transcript(
        self,
        text: str,
        skill: str,
        student_id: str,
        sentences: Optional[List[Dict]] = None,
        max_spans: int = 5,
    ) -> List[EvidenceSpan]:
        """
        Extract evidence spans from a transcript with line number citations.

        Args:
            text: Full transcript text
            skill: Skill to extract evidence for
            student_id: Student identifier to focus on
            sentences: Optional pre-segmented sentences with speaker info
            max_spans: Maximum number of spans to return

        Returns:
            List of ranked evidence spans

        Example:
            >>> extractor = EvidenceExtractor()
            >>> spans = extractor.extract_from_transcript(
            ...     text="Teacher: How do you feel?\\nStudent A: I understand how you feel.",
            ...     skill="empathy",
            ...     student_id="student_a"
            ... )
        """
        logger.info(f"Extracting evidence for {skill} from transcript for student {student_id}")

        # Split text into lines for citation
        lines = text.split("\n")
        line_map = self._build_line_map(text)

        # Extract candidate spans
        candidate_spans = []

        if sentences:
            # Use pre-segmented sentences
            student_sentences = [
                s for s in sentences if s.get("speaker_id", "").lower() == student_id.lower()
            ]

            for sentence_data in student_sentences:
                sentence_text = sentence_data.get("text", "")
                sentence_id = sentence_data.get("sentence_id", 0)

                # Get skill-specific evidence if skill detector available
                if self.skill_detector:
                    skill_spans = self.skill_detector.extract_evidence_spans(
                        sentence_text, skill, max_spans=3
                    )

                    for span in skill_spans:
                        # Find line number for this span
                        char_pos = text.find(sentence_text)
                        if char_pos >= 0:
                            line_num = self._char_to_line(char_pos, line_map)
                            location = f"line {line_num}"

                            evidence = EvidenceSpan(
                                text=span["text"],
                                location=location,
                                rationale=span["rationale"],
                                score_contribution=self._calculate_relevance(span, skill),
                                skill=skill,
                                span_type=span["type"],
                                start_char=char_pos + span["start"],
                                end_char=char_pos + span["end"],
                                context=sentence_text,
                            )
                            candidate_spans.append(evidence)
                else:
                    # Basic keyword matching if no skill detector
                    spans = self._extract_basic_spans(sentence_text, skill)
                    for span in spans:
                        char_pos = text.find(sentence_text)
                        if char_pos >= 0:
                            line_num = self._char_to_line(char_pos, line_map)
                            location = f"line {line_num}"

                            evidence = EvidenceSpan(
                                text=span["text"],
                                location=location,
                                rationale=span["rationale"],
                                score_contribution=span["score"],
                                skill=skill,
                                span_type="keyword",
                                start_char=char_pos,
                                end_char=char_pos + len(span["text"]),
                                context=sentence_text,
                            )
                            candidate_spans.append(evidence)
        else:
            # Parse transcript directly
            for line_num, line in enumerate(lines, start=1):
                # Extract student utterances
                if self._is_student_line(line, student_id):
                    line_text = self._extract_utterance_text(line)

                    if self.skill_detector:
                        skill_spans = self.skill_detector.extract_evidence_spans(
                            line_text, skill, max_spans=3
                        )

                        for span in skill_spans:
                            evidence = EvidenceSpan(
                                text=span["text"],
                                location=f"line {line_num}",
                                rationale=span["rationale"],
                                score_contribution=self._calculate_relevance(span, skill),
                                skill=skill,
                                span_type=span["type"],
                                start_char=span["start"],
                                end_char=span["end"],
                                context=line_text,
                            )
                            candidate_spans.append(evidence)

        # Rank and filter spans
        ranked_spans = self._rank_spans(candidate_spans)

        logger.info(f"Extracted {len(ranked_spans)} evidence spans for {skill}")
        return ranked_spans[:max_spans]

    def extract_from_artifact(
        self,
        text: str,
        skill: str,
        student_id: str,
        artifact_type: str = "document",
        max_spans: int = 5,
    ) -> List[EvidenceSpan]:
        """
        Extract evidence spans from a student artifact with page citations.

        Args:
            text: Full artifact text
            skill: Skill to extract evidence for
            student_id: Student identifier
            artifact_type: Type of artifact (document, essay, pdf)
            max_spans: Maximum number of spans to return

        Returns:
            List of ranked evidence spans

        Example:
            >>> extractor = EvidenceExtractor()
            >>> spans = extractor.extract_from_artifact(
            ...     text="I understand the importance of collaboration...",
            ...     skill="collaboration",
            ...     student_id="student_a",
            ...     artifact_type="essay"
            ... )
        """
        logger.info(f"Extracting evidence for {skill} from {artifact_type} for student {student_id}")

        # Estimate pages (assuming ~500 words per page for text documents)
        page_map = self._build_page_map(text)

        candidate_spans = []

        if self.skill_detector:
            # Use skill detector to find evidence
            skill_spans = self.skill_detector.extract_evidence_spans(text, skill, max_spans=max_spans * 2)

            for span in skill_spans:
                # Determine page number
                page_num = self._char_to_page(span["start"], page_map)
                location = f"page {page_num}"

                # Extract context around span
                context = self._extract_context(text, span["start"], span["end"], context_size=100)

                evidence = EvidenceSpan(
                    text=span["text"],
                    location=location,
                    rationale=span["rationale"],
                    score_contribution=self._calculate_relevance(span, skill),
                    skill=skill,
                    span_type=span["type"],
                    start_char=span["start"],
                    end_char=span["end"],
                    context=context,
                )
                candidate_spans.append(evidence)
        else:
            # Basic extraction without skill detector
            spans = self._extract_basic_spans(text, skill)
            for span in spans:
                page_num = self._char_to_page(span["start"], page_map)
                location = f"page {page_num}"
                context = self._extract_context(text, span["start"], span["end"])

                evidence = EvidenceSpan(
                    text=span["text"],
                    location=location,
                    rationale=span["rationale"],
                    score_contribution=span["score"],
                    skill=skill,
                    span_type="keyword",
                    start_char=span["start"],
                    end_char=span["end"],
                    context=context,
                )
                candidate_spans.append(evidence)

        # Rank and return top spans
        ranked_spans = self._rank_spans(candidate_spans)

        logger.info(f"Extracted {len(ranked_spans)} evidence spans from artifact")
        return ranked_spans[:max_spans]

    def _build_line_map(self, text: str) -> List[Tuple[int, int]]:
        """
        Build a map of character positions to line numbers.

        Args:
            text: Input text

        Returns:
            List of (start_char, end_char) tuples for each line
        """
        line_map = []
        current_pos = 0

        for line in text.split("\n"):
            line_length = len(line) + 1  # +1 for newline
            line_map.append((current_pos, current_pos + line_length))
            current_pos += line_length

        return line_map

    def _build_page_map(self, text: str, words_per_page: int = 500) -> List[int]:
        """
        Build a map of character positions to page numbers.

        Args:
            text: Input text
            words_per_page: Estimated words per page

        Returns:
            List of character positions where each page starts
        """
        words = text.split()
        page_boundaries = [0]
        current_pos = 0
        word_count = 0

        for word in words:
            current_pos = text.find(word, current_pos)
            if current_pos == -1:
                break

            word_count += 1
            if word_count >= words_per_page:
                page_boundaries.append(current_pos)
                word_count = 0

            current_pos += len(word)

        return page_boundaries

    def _char_to_line(self, char_pos: int, line_map: List[Tuple[int, int]]) -> int:
        """
        Convert character position to line number.

        Args:
            char_pos: Character position
            line_map: Line map from _build_line_map

        Returns:
            Line number (1-indexed)
        """
        for line_num, (start, end) in enumerate(line_map, start=1):
            if start <= char_pos < end:
                return line_num
        return len(line_map)  # Return last line if not found

    def _char_to_page(self, char_pos: int, page_map: List[int]) -> int:
        """
        Convert character position to page number.

        Args:
            char_pos: Character position
            page_map: Page map from _build_page_map

        Returns:
            Page number (1-indexed)
        """
        for page_num, page_start in enumerate(page_map, start=1):
            if page_num < len(page_map):
                next_page_start = page_map[page_num]
                if page_start <= char_pos < next_page_start:
                    return page_num
            else:
                # Last page
                if char_pos >= page_start:
                    return page_num
        return 1  # Default to page 1 if not found

    def _is_student_line(self, line: str, student_id: str) -> bool:
        """
        Check if a transcript line belongs to the specified student.

        Args:
            line: Transcript line
            student_id: Student identifier

        Returns:
            True if line belongs to student
        """
        # Simple pattern: "Student A:" or "student_a:"
        pattern = rf"(?i)^{re.escape(student_id)}[\s:,]"
        return bool(re.match(pattern, line))

    def _extract_utterance_text(self, line: str) -> str:
        """
        Extract the utterance text from a transcript line.

        Args:
            line: Transcript line (e.g., "Student A: I feel happy")

        Returns:
            Utterance text without speaker label
        """
        # Remove speaker label (everything before first colon)
        parts = line.split(":", 1)
        if len(parts) > 1:
            return parts[1].strip()
        return line.strip()

    def _extract_basic_spans(self, text: str, skill: str) -> List[Dict]:
        """
        Extract basic keyword spans without skill detector.

        Args:
            text: Input text
            skill: Skill name

        Returns:
            List of basic span dictionaries
        """
        # Simplified skill keywords
        skill_keywords = {
            "empathy": ["understand", "feel", "sorry", "care", "support"],
            "collaboration": ["together", "team", "cooperate", "work with"],
            "communication": ["explain", "clarify", "discuss", "share"],
            "adaptability": ["change", "adapt", "adjust", "flexible"],
            "self_regulation": ["calm", "control", "focus", "patient"],
        }

        keywords = skill_keywords.get(skill, [])
        spans = []

        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                start = text_lower.find(keyword)
                spans.append({
                    "text": text[start : start + len(keyword)],
                    "start": start,
                    "end": start + len(keyword),
                    "rationale": f"Keyword '{keyword}' indicates {skill}",
                    "score": 0.5,
                })

        return spans

    def _extract_context(
        self, text: str, start: int, end: int, context_size: int = 100
    ) -> str:
        """
        Extract surrounding context for a span.

        Args:
            text: Full text
            start: Span start position
            end: Span end position
            context_size: Number of characters to include on each side

        Returns:
            Context string
        """
        context_start = max(0, start - context_size)
        context_end = min(len(text), end + context_size)

        context = text[context_start:context_end]

        # Add ellipsis if truncated
        if context_start > 0:
            context = "..." + context
        if context_end < len(text):
            context = context + "..."

        return context.strip()

    def _calculate_relevance(self, span: Dict, skill: str) -> float:
        """
        Calculate relevance score for an evidence span.

        Args:
            span: Span dictionary from skill detector
            skill: Target skill

        Returns:
            Relevance score (0.0-1.0)
        """
        base_score = 0.5

        # Phrases are more relevant than keywords
        if span["type"] == "phrase":
            base_score = 0.8
        elif span["type"] == "keyword":
            base_score = 0.6

        # Longer spans tend to be more meaningful
        span_length = span["end"] - span["start"]
        length_bonus = min(span_length / 50, 0.2)  # Up to 0.2 bonus

        return min(base_score + length_bonus, 1.0)

    def _rank_spans(self, spans: List[EvidenceSpan]) -> List[EvidenceSpan]:
        """
        Rank evidence spans by relevance and quality.

        Args:
            spans: List of evidence spans

        Returns:
            Sorted list of spans (highest relevance first)
        """
        # Remove duplicates
        unique_spans = self._deduplicate_spans(spans)

        # Sort by score contribution (descending), then by span length (descending)
        ranked = sorted(
            unique_spans,
            key=lambda s: (s.score_contribution, len(s.text)),
            reverse=True,
        )

        return ranked

    def _deduplicate_spans(self, spans: List[EvidenceSpan]) -> List[EvidenceSpan]:
        """
        Remove duplicate or overlapping spans.

        Args:
            spans: List of evidence spans

        Returns:
            Deduplicated list
        """
        if not spans:
            return []

        # Sort by start position
        sorted_spans = sorted(spans, key=lambda s: s.start_char)

        unique = [sorted_spans[0]]

        for span in sorted_spans[1:]:
            last_span = unique[-1]

            # Check for overlap
            if span.start_char >= last_span.end_char:
                # No overlap, add it
                unique.append(span)
            elif span.score_contribution > last_span.score_contribution:
                # Replace last span if this one is better
                unique[-1] = span

        return unique

    def batch_extract_evidence(
        self,
        text: str,
        skills: List[str],
        student_id: str,
        source_type: str = "transcript",
        sentences: Optional[List[Dict]] = None,
        max_spans_per_skill: int = 3,
    ) -> Dict[str, List[EvidenceSpan]]:
        """
        Extract evidence for multiple skills at once.

        Args:
            text: Source text
            skills: List of skills to extract evidence for
            student_id: Student identifier
            source_type: Type of source (transcript or artifact)
            sentences: Optional pre-segmented sentences
            max_spans_per_skill: Maximum spans per skill

        Returns:
            Dictionary mapping skills to evidence spans
        """
        logger.info(f"Batch extracting evidence for {len(skills)} skills")

        evidence_by_skill = {}

        for skill in skills:
            if source_type == "transcript":
                spans = self.extract_from_transcript(
                    text, skill, student_id, sentences, max_spans=max_spans_per_skill
                )
            else:
                spans = self.extract_from_artifact(
                    text, skill, student_id, max_spans=max_spans_per_skill
                )

            evidence_by_skill[skill] = spans

        return evidence_by_skill
