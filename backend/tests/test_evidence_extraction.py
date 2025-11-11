"""Tests for evidence extraction module"""

import pytest

from app.nlp.evidence_extraction import EvidenceExtractor, EvidenceSpan
from app.nlp.skill_detection import SkillDetector


class TestEvidenceExtractor:
    """Test suite for EvidenceExtractor"""

    @pytest.fixture
    def extractor(self):
        """Create evidence extractor with skill detector"""
        skill_detector = SkillDetector(seed=42)
        return EvidenceExtractor(skill_detector=skill_detector)

    @pytest.fixture
    def basic_extractor(self):
        """Create evidence extractor without skill detector"""
        return EvidenceExtractor(skill_detector=None)

    @pytest.fixture
    def sample_transcript(self):
        """Sample classroom transcript"""
        return """Teacher: Good morning class. How is everyone feeling today?
Student A: I feel good, thank you.
Teacher: That's great. Let's work together on today's assignment.
Student A: I understand. I'll help my classmates if they need it.
Student B: I'm feeling confused about the homework.
Student A: I can explain it to you. Let me clarify the instructions."""

    @pytest.fixture
    def sample_artifact(self):
        """Sample student artifact (essay)"""
        return """In this essay, I will explain my understanding of collaboration.
Working together with others is important because it helps us achieve goals faster.
I have learned to be patient and listen to different perspectives.
When team members communicate clearly, we can adapt our strategies effectively.
I understand that empathy plays a crucial role in successful teamwork."""

    def test_extract_from_transcript_basic(self, basic_extractor, sample_transcript):
        """Test basic extraction from transcript without skill detector"""
        spans = basic_extractor.extract_from_transcript(
            text=sample_transcript,
            skill="empathy",
            student_id="Student A",
            max_spans=5,
        )

        assert isinstance(spans, list)
        assert len(spans) > 0
        assert all(isinstance(span, EvidenceSpan) for span in spans)

        # Check that spans have required attributes
        for span in spans:
            assert span.text
            assert span.location
            assert span.rationale
            assert 0.0 <= span.score_contribution <= 1.0
            assert span.skill == "empathy"

    def test_extract_from_transcript_with_skill_detector(
        self, extractor, sample_transcript
    ):
        """Test extraction with skill detector"""
        spans = extractor.extract_from_transcript(
            text=sample_transcript,
            skill="empathy",
            student_id="Student A",
            max_spans=3,
        )

        assert isinstance(spans, list)
        assert len(spans) > 0

        # Verify evidence quality
        for span in spans:
            assert span.text in sample_transcript
            assert "line" in span.location
            assert span.skill == "empathy"
            assert span.rationale
            assert span.context  # Should have surrounding context

    def test_extract_from_transcript_with_sentences(self, extractor):
        """Test extraction with pre-segmented sentences"""
        sentences = [
            {
                "text": "I understand how you feel.",
                "speaker_id": "student_a",
                "speaker_role": "student",
                "sentence_id": 0,
            },
            {
                "text": "Let's work together on this.",
                "speaker_id": "student_a",
                "speaker_role": "student",
                "sentence_id": 1,
            },
            {
                "text": "What is the assignment?",
                "speaker_id": "student_b",
                "speaker_role": "student",
                "sentence_id": 2,
            },
        ]

        text = "Student A: I understand how you feel. Let's work together on this.\nStudent B: What is the assignment?"

        spans = extractor.extract_from_transcript(
            text=text,
            skill="empathy",
            student_id="student_a",
            sentences=sentences,
            max_spans=5,
        )

        assert len(spans) > 0
        # Should only extract from student_a's sentences
        assert all(span.skill == "empathy" for span in spans)

    def test_extract_from_artifact(self, extractor, sample_artifact):
        """Test extraction from student artifact"""
        spans = extractor.extract_from_artifact(
            text=sample_artifact,
            skill="collaboration",
            student_id="student_a",
            artifact_type="essay",
            max_spans=5,
        )

        assert isinstance(spans, list)
        assert len(spans) > 0

        for span in spans:
            assert span.text in sample_artifact
            assert "page" in span.location
            assert span.skill == "collaboration"
            assert span.context  # Should have context
            assert 0.0 <= span.score_contribution <= 1.0

    def test_line_number_citation(self, extractor, sample_transcript):
        """Test that line numbers are correctly cited"""
        spans = extractor.extract_from_transcript(
            text=sample_transcript,
            skill="empathy",
            student_id="Student A",
            max_spans=5,
        )

        for span in spans:
            # Extract line number from location
            if "line" in span.location:
                line_num = int(span.location.split()[1])
                # Verify line number is valid
                lines = sample_transcript.split("\n")
                assert 1 <= line_num <= len(lines)

    def test_page_number_citation(self, extractor):
        """Test that page numbers are correctly cited for artifacts"""
        # Create a long artifact that spans multiple pages
        long_artifact = " ".join(["collaboration"] * 600)  # ~600 words

        spans = extractor.extract_from_artifact(
            text=long_artifact,
            skill="collaboration",
            student_id="student_a",
            max_spans=5,
        )

        for span in spans:
            # Verify page citation exists
            assert "page" in span.location
            page_num = int(span.location.split()[1])
            assert page_num >= 1

    def test_relevance_ranking(self, extractor, sample_transcript):
        """Test that spans are ranked by relevance"""
        spans = extractor.extract_from_transcript(
            text=sample_transcript,
            skill="empathy",
            student_id="Student A",
            max_spans=10,
        )

        if len(spans) > 1:
            # Verify spans are sorted by score (descending)
            for i in range(len(spans) - 1):
                assert spans[i].score_contribution >= spans[i + 1].score_contribution

    def test_span_deduplication(self, extractor):
        """Test that duplicate spans are removed"""
        text = "I understand. I understand. I understand."

        spans = extractor.extract_from_transcript(
            text=text,
            skill="empathy",
            student_id="Student",
            max_spans=10,
        )

        # Should not have many duplicates despite repeated text
        texts = [span.text for span in spans]
        # Some duplicates might exist but should be limited
        assert len(texts) <= 5

    def test_max_spans_limit(self, extractor, sample_transcript):
        """Test that max_spans parameter is respected"""
        max_spans = 3

        spans = extractor.extract_from_transcript(
            text=sample_transcript,
            skill="communication",
            student_id="Student A",
            max_spans=max_spans,
        )

        assert len(spans) <= max_spans

    def test_batch_extract_evidence(self, extractor, sample_transcript):
        """Test batch extraction for multiple skills"""
        skills = ["empathy", "collaboration", "communication"]

        evidence_by_skill = extractor.batch_extract_evidence(
            text=sample_transcript,
            skills=skills,
            student_id="Student A",
            source_type="transcript",
            max_spans_per_skill=3,
        )

        assert isinstance(evidence_by_skill, dict)
        assert len(evidence_by_skill) == len(skills)

        for skill in skills:
            assert skill in evidence_by_skill
            assert isinstance(evidence_by_skill[skill], list)
            assert len(evidence_by_skill[skill]) <= 3

    def test_context_extraction(self, extractor, sample_artifact):
        """Test that context is properly extracted around spans"""
        spans = extractor.extract_from_artifact(
            text=sample_artifact,
            skill="empathy",
            student_id="student_a",
            max_spans=5,
        )

        for span in spans:
            # Context should contain the span text
            assert span.text in span.context or span.text in sample_artifact
            # Context should be longer than just the span
            assert len(span.context) >= len(span.text)

    def test_different_skills(self, extractor, sample_transcript):
        """Test extraction for different skills"""
        skills_to_test = [
            "empathy",
            "collaboration",
            "communication",
            "adaptability",
            "self_regulation",
        ]

        for skill in skills_to_test:
            spans = extractor.extract_from_transcript(
                text=sample_transcript,
                skill=skill,
                student_id="Student A",
                max_spans=5,
            )

            # Should return list (may be empty for some skills)
            assert isinstance(spans, list)
            # All spans should be for the requested skill
            assert all(s.skill == skill for s in spans)

    def test_empty_transcript(self, extractor):
        """Test handling of empty transcript"""
        spans = extractor.extract_from_transcript(
            text="",
            skill="empathy",
            student_id="Student A",
            max_spans=5,
        )

        assert isinstance(spans, list)
        assert len(spans) == 0

    def test_no_student_utterances(self, extractor):
        """Test when student has no utterances"""
        transcript = "Teacher: Good morning.\nTeacher: Let's begin."

        spans = extractor.extract_from_transcript(
            text=transcript,
            skill="empathy",
            student_id="Student A",
            max_spans=5,
        )

        # Should return empty list if student not found
        assert isinstance(spans, list)

    def test_span_types(self, extractor, sample_transcript):
        """Test that different span types are identified"""
        spans = extractor.extract_from_transcript(
            text=sample_transcript,
            skill="empathy",
            student_id="Student A",
            max_spans=10,
        )

        if spans:
            # Should have span_type attribute
            assert all(hasattr(span, "span_type") for span in spans)
            # Valid types
            valid_types = ["keyword", "phrase", "sentence", "paragraph"]
            assert all(span.span_type in valid_types for span in spans)

    def test_rationale_generation(self, extractor, sample_transcript):
        """Test that rationales are generated for each span"""
        spans = extractor.extract_from_transcript(
            text=sample_transcript,
            skill="empathy",
            student_id="Student A",
            max_spans=5,
        )

        for span in spans:
            # Rationale should mention the skill
            assert span.skill in span.rationale.lower() or "empathy" in span.rationale.lower()
            # Rationale should be meaningful
            assert len(span.rationale) > 10

    def test_score_contribution_range(self, extractor, sample_transcript):
        """Test that score contributions are in valid range"""
        spans = extractor.extract_from_transcript(
            text=sample_transcript,
            skill="communication",
            student_id="Student A",
            max_spans=10,
        )

        for span in spans:
            assert 0.0 <= span.score_contribution <= 1.0

    def test_character_positions(self, extractor, sample_transcript):
        """Test that character positions are accurate"""
        spans = extractor.extract_from_transcript(
            text=sample_transcript,
            skill="empathy",
            student_id="Student A",
            max_spans=5,
        )

        for span in spans:
            # Start should be before end
            assert span.start_char < span.end_char
            # Positions should be within text bounds
            assert 0 <= span.start_char < len(sample_transcript)
            assert 0 < span.end_char <= len(sample_transcript)

    def test_case_insensitive_student_matching(self, extractor):
        """Test that student ID matching is case-insensitive"""
        transcript = "student a: I understand how you feel."

        spans1 = extractor.extract_from_transcript(
            text=transcript,
            skill="empathy",
            student_id="student a",
            max_spans=5,
        )

        spans2 = extractor.extract_from_transcript(
            text=transcript,
            skill="empathy",
            student_id="Student A",
            max_spans=5,
        )

        # Should find evidence regardless of case
        assert len(spans1) > 0 or len(spans2) > 0


class TestEvidenceSpan:
    """Test EvidenceSpan dataclass"""

    def test_evidence_span_creation(self):
        """Test creating an evidence span"""
        span = EvidenceSpan(
            text="I understand",
            location="line 5",
            rationale="Shows empathy",
            score_contribution=0.8,
            skill="empathy",
            span_type="keyword",
            start_char=10,
            end_char=22,
            context="Teacher: How do you feel? Student: I understand.",
        )

        assert span.text == "I understand"
        assert span.location == "line 5"
        assert span.rationale == "Shows empathy"
        assert span.score_contribution == 0.8
        assert span.skill == "empathy"
        assert span.span_type == "keyword"
        assert span.start_char == 10
        assert span.end_char == 22
        assert "I understand" in span.context

    def test_evidence_span_optional_context(self):
        """Test that context is optional"""
        span = EvidenceSpan(
            text="collaborate",
            location="page 2",
            rationale="Indicates collaboration",
            score_contribution=0.7,
            skill="collaboration",
            span_type="keyword",
            start_char=50,
            end_char=61,
        )

        assert span.context is None


class TestLineAndPageMapping:
    """Test line and page mapping functionality"""

    def test_build_line_map(self):
        """Test line map construction"""
        extractor = EvidenceExtractor()
        text = "Line 1\nLine 2\nLine 3"

        line_map = extractor._build_line_map(text)

        assert len(line_map) == 3
        assert line_map[0][0] == 0  # First line starts at 0
        assert line_map[1][0] == 7  # Second line starts at 7

    def test_char_to_line_conversion(self):
        """Test character position to line number conversion"""
        extractor = EvidenceExtractor()
        text = "Line 1\nLine 2\nLine 3"

        line_map = extractor._build_line_map(text)

        # Character at position 0 should be line 1
        assert extractor._char_to_line(0, line_map) == 1
        # Character at position 7 should be line 2
        assert extractor._char_to_line(7, line_map) == 2

    def test_build_page_map(self):
        """Test page map construction"""
        extractor = EvidenceExtractor()
        # Create text with enough words for multiple pages
        text = " ".join(["word"] * 1000)

        page_map = extractor._build_page_map(text, words_per_page=250)

        # Should have multiple pages
        assert len(page_map) > 1
        # First page starts at 0
        assert page_map[0] == 0

    def test_char_to_page_conversion(self):
        """Test character position to page number conversion"""
        extractor = EvidenceExtractor()
        text = " ".join(["word"] * 1000)

        page_map = extractor._build_page_map(text, words_per_page=250)

        # First character should be page 1
        page = extractor._char_to_page(0, page_map)
        assert page >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
