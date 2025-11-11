"""Pydantic models for NLP pipeline results"""

from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class LanguageDetectionResult(BaseModel):
    """Language detection result"""

    language: str = Field(..., description="Detected language code (e.g., 'en', 'es')")
    name: str = Field(..., description="Language name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    method: str = Field(..., description="Detection method used")
    alternatives: List[Dict[str, float]] = Field(default_factory=list)


class EvidenceSpan(BaseModel):
    """Evidence span for skill detection"""

    text: str = Field(..., description="Text span")
    start: int = Field(..., description="Character start position")
    end: int = Field(..., description="Character end position")
    type: str = Field(..., description="Evidence type (keyword, phrase)")
    skill: str = Field(..., description="Associated skill")
    rationale: str = Field(..., description="Why this is evidence")


class SkillScore(BaseModel):
    """Skill score with confidence and evidence"""

    score: float = Field(..., ge=0.0, le=1.0, description="Skill score (0-1)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in score")
    demonstration_count: int = Field(..., ge=0, description="Number of demonstrations")
    evidence_count: int = Field(..., ge=0, description="Number of evidence pieces")
    top_evidence: List[Dict] = Field(default_factory=list, description="Top evidence spans")


class StudentSkillScores(BaseModel):
    """Complete skill scores for a student"""

    student_id: str = Field(..., description="Student identifier")
    empathy: SkillScore
    adaptability: SkillScore
    collaboration: SkillScore
    communication: SkillScore
    self_regulation: SkillScore


class ProcessingStats(BaseModel):
    """Pipeline processing statistics"""

    original_length: int = Field(..., ge=0)
    cleaned_length: int = Field(..., ge=0)
    speaker_segments: Optional[int] = Field(None, ge=0)
    sentence_count: int = Field(..., ge=0)
    student_count: int = Field(..., ge=0)


class SpeakerStatistics(BaseModel):
    """Statistics for a speaker"""

    count: int = Field(..., ge=0, description="Number of sentences")
    word_count: int = Field(..., ge=0, description="Total words")
    role: str = Field(..., description="Speaker role")
    sentences: List[str] = Field(default_factory=list)


class TranscriptProcessingResult(BaseModel):
    """Complete transcript processing result"""

    metadata: Dict = Field(default_factory=dict)
    language: LanguageDetectionResult
    processing_stats: ProcessingStats
    speaker_statistics: Dict[str, SpeakerStatistics]
    student_ids: List[str]
    skill_scores: Dict[str, StudentSkillScores]
    sentences: List[Dict] = Field(default_factory=list)
    pipeline_version: str
    seed: int


class ArtifactProcessingResult(BaseModel):
    """Artifact processing result"""

    student_id: str
    metadata: Dict = Field(default_factory=dict)
    language: LanguageDetectionResult
    processing_stats: Dict
    skill_scores: Dict[str, SkillScore]
    sentences: List[Dict] = Field(default_factory=list)
    pipeline_version: str
    seed: int


class PipelineInfo(BaseModel):
    """Pipeline configuration information"""

    version: str
    components: Dict[str, str]
    supported_skills: List[str]
    skill_descriptions: Dict[str, str]
    seed: int
    deterministic: bool
