"""Main NLP Pipeline orchestrator"""

import logging
from typing import Dict, List, Optional

from app.nlp.diarization import DiarizationMapper
from app.nlp.language_detection import LanguageDetector
from app.nlp.sentence_segmentation import SentenceSegmenter
from app.nlp.skill_detection import SkillDetector
from app.nlp.text_cleanup import TextCleaner

logger = logging.getLogger(__name__)


class NLPPipeline:
    """
    Orchestrates the complete NLP pipeline for skill scoring.

    Pipeline stages:
    1. Language Detection
    2. Text Cleanup
    3. Sentence Segmentation
    4. Diarization Mapping
    5. Skill Cue Detection
    6. Scoring and Evidence Extraction
    """

    def __init__(self, config: Optional[Dict] = None, seed: int = 42) -> None:
        """
        Initialize NLP pipeline with all components.

        Args:
            config: Optional configuration dictionary
            seed: Random seed for reproducibility
        """
        self.config = config or {}
        self.seed = seed

        # Initialize pipeline components
        logger.info("Initializing NLP Pipeline components...")
        self.language_detector = LanguageDetector()
        self.text_cleaner = TextCleaner()
        self.sentence_segmenter = SentenceSegmenter()
        self.diarization_mapper = DiarizationMapper()
        self.skill_detector = SkillDetector(seed=seed)

        logger.info("NLP Pipeline initialized successfully")

    def process_transcript(
        self, text: str, metadata: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Process a complete transcript through the NLP pipeline.

        Args:
            text: Raw transcript text
            metadata: Optional metadata (class_id, date, student_roster, etc.)

        Returns:
            Dictionary with processed results and skill scores

        Example:
            >>> pipeline = NLPPipeline()
            >>> result = pipeline.process_transcript(
            ...     "Teacher: Good morning class. Student A: I understand the assignment.",
            ...     metadata={"class_id": "CS101", "date": "2024-01-15"}
            ... )
        """
        logger.info("Starting transcript processing...")

        # Stage 1: Language Detection
        language_result = self.language_detector.detect(text)
        detected_language = language_result["language"]
        logger.info(f"Detected language: {detected_language} (confidence: {language_result['confidence']})")

        # Stage 2: Text Cleanup
        cleaned_text = self.text_cleaner.clean_transcript(text)
        logger.info(f"Text cleaned: {len(text)} -> {len(cleaned_text)} characters")

        # Stage 3: Extract speaker segments
        speaker_segments = self.text_cleaner.extract_speaker_segments(cleaned_text)
        logger.info(f"Extracted {len(speaker_segments)} speaker segments")

        # Stage 4: Sentence Segmentation
        sentences = self.sentence_segmenter.segment_transcript(speaker_segments)
        logger.info(f"Segmented into {len(sentences)} sentences")

        # Stage 5: Diarization Mapping
        sentences_with_speakers = self.diarization_mapper.map_speakers(sentences)
        speaker_stats = self.diarization_mapper.get_speaker_statistics(sentences_with_speakers)
        student_ids = self.diarization_mapper.identify_students(sentences_with_speakers)
        logger.info(f"Identified {len(student_ids)} students")

        # Stage 6: Skill Detection and Scoring
        skill_scores = self.skill_detector.score_conversation(
            sentences_with_speakers, student_ids=student_ids
        )
        logger.info(f"Generated skill scores for {len(skill_scores)} students")

        # Compile results
        result = {
            "metadata": metadata or {},
            "language": language_result,
            "processing_stats": {
                "original_length": len(text),
                "cleaned_length": len(cleaned_text),
                "speaker_segments": len(speaker_segments),
                "sentence_count": len(sentences),
                "student_count": len(student_ids),
            },
            "speaker_statistics": speaker_stats,
            "student_ids": student_ids,
            "skill_scores": skill_scores,
            "sentences": sentences_with_speakers[:10],  # Include first 10 sentences as sample
            "pipeline_version": "1.0.0",
            "seed": self.seed,
        }

        logger.info("Transcript processing completed successfully")
        return result

    def process_artifact(
        self, text: str, student_id: str, metadata: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Process a student artifact (essay, document) through the NLP pipeline.

        Args:
            text: Raw artifact text
            student_id: Student identifier
            metadata: Optional metadata

        Returns:
            Dictionary with processed results and skill scores
        """
        logger.info(f"Starting artifact processing for student: {student_id}")

        # Stage 1: Language Detection
        language_result = self.language_detector.detect(text)
        detected_language = language_result["language"]
        logger.info(f"Detected language: {detected_language}")

        # Stage 2: Text Cleanup (artifact-specific)
        cleaned_text = self.text_cleaner.clean_artifact(text)

        # Stage 3: Sentence Segmentation
        sentences = self.sentence_segmenter.segment(cleaned_text)
        logger.info(f"Segmented into {len(sentences)} sentences")

        # Stage 4: Create sentence objects with student metadata
        sentence_objects = [
            {
                "text": sent,
                "speaker_id": student_id,
                "speaker_role": "student",
                "sentence_id": idx,
            }
            for idx, sent in enumerate(sentences)
        ]

        # Stage 5: Skill Detection
        skill_scores = self.skill_detector.score_conversation(
            sentence_objects, student_ids=[student_id]
        )

        result = {
            "student_id": student_id,
            "metadata": metadata or {},
            "language": language_result,
            "processing_stats": {
                "original_length": len(text),
                "cleaned_length": len(cleaned_text),
                "sentence_count": len(sentences),
            },
            "skill_scores": skill_scores.get(student_id, {}),
            "sentences": sentence_objects[:10],  # Sample sentences
            "pipeline_version": "1.0.0",
            "seed": self.seed,
        }

        logger.info("Artifact processing completed successfully")
        return result

    def batch_process_transcripts(
        self, transcripts: List[Dict[str, str]]
    ) -> List[Dict[str, any]]:
        """
        Process multiple transcripts in batch.

        Args:
            transcripts: List of transcript dictionaries with 'text' and optional 'metadata'

        Returns:
            List of processing results
        """
        logger.info(f"Starting batch processing of {len(transcripts)} transcripts")
        results = []

        for idx, transcript in enumerate(transcripts):
            logger.info(f"Processing transcript {idx + 1}/{len(transcripts)}")
            try:
                result = self.process_transcript(
                    text=transcript["text"],
                    metadata=transcript.get("metadata")
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing transcript {idx}: {e}")
                results.append({
                    "error": str(e),
                    "transcript_index": idx,
                    "metadata": transcript.get("metadata", {}),
                })

        logger.info(f"Batch processing completed: {len(results)} results")
        return results

    def extract_evidence_for_student(
        self, sentences: List[Dict[str, str]], student_id: str, skill: str
    ) -> List[Dict[str, any]]:
        """
        Extract evidence spans for a specific student and skill.

        Args:
            sentences: Sentence segments
            student_id: Student identifier
            skill: Skill to extract evidence for

        Returns:
            List of evidence spans with rationale
        """
        student_sentences = [
            s for s in sentences
            if s.get("speaker_id") == student_id
        ]

        all_evidence = []
        for sentence in student_sentences:
            evidence = self.skill_detector.extract_evidence_spans(
                text=sentence.get("text", ""),
                skill=skill,
                max_spans=3
            )

            for span in evidence:
                span["sentence_id"] = sentence.get("sentence_id", "")
                span["full_sentence"] = sentence.get("text", "")

            all_evidence.extend(evidence)

        # Sort by relevance and return top evidence
        all_evidence.sort(key=lambda x: (x["type"] == "phrase", x["end"] - x["start"]), reverse=True)

        return all_evidence[:5]  # Top 5 pieces of evidence

    def get_pipeline_info(self) -> Dict[str, any]:
        """
        Get information about the pipeline configuration.

        Returns:
            Pipeline metadata
        """
        return {
            "version": "1.0.0",
            "components": {
                "language_detector": "LanguageDetector",
                "text_cleaner": "TextCleaner",
                "sentence_segmenter": "SentenceSegmenter",
                "diarization_mapper": "DiarizationMapper",
                "skill_detector": "SkillDetector",
            },
            "supported_skills": self.skill_detector.get_supported_skills(),
            "skill_descriptions": {
                skill: self.skill_detector.get_skill_description(skill)
                for skill in self.skill_detector.get_supported_skills()
            },
            "seed": self.seed,
            "deterministic": True,
        }
