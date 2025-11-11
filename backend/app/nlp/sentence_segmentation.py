"""Sentence segmentation module using spaCy"""

import logging
from typing import Dict, List, Optional

import spacy
from spacy.language import Language

logger = logging.getLogger(__name__)


class SentenceSegmenter:
    """
    Segment text into sentences using spaCy's sentence boundary detection.

    Handles:
    - Multi-language sentence segmentation
    - Custom sentence boundary rules
    - Metadata preservation (speaker, timestamps)
    """

    def __init__(self, language: str = "en", model_name: Optional[str] = None) -> None:
        """
        Initialize sentence segmenter.

        Args:
            language: Language code (en, es, fr, etc.)
            model_name: Optional specific spaCy model name
        """
        self.language = language
        self.model_name = model_name or self._get_default_model(language)
        self.nlp = self._load_model()

    def _get_default_model(self, language: str) -> str:
        """
        Get default spaCy model for language.

        Args:
            language: Language code

        Returns:
            Model name
        """
        model_mapping = {
            "en": "en_core_web_sm",
            "es": "es_core_news_sm",
            "fr": "fr_core_news_sm",
            "de": "de_core_news_sm",
            "zh": "zh_core_web_sm",
        }
        return model_mapping.get(language, "en_core_web_sm")

    def _load_model(self) -> Language:
        """
        Load spaCy model with error handling.

        Returns:
            Loaded spaCy Language model
        """
        try:
            nlp = spacy.load(self.model_name)
            logger.info(f"Loaded spaCy model: {self.model_name}")

            # Optimize for sentence segmentation only
            # Disable unnecessary pipeline components for speed
            nlp.disable_pipes([pipe for pipe in nlp.pipe_names if pipe not in ["sentencizer", "parser"]])

            return nlp
        except OSError:
            logger.error(
                f"Model {self.model_name} not found. "
                f"Run: python -m spacy download {self.model_name}"
            )
            # Fallback to blank model with sentencizer
            nlp = spacy.blank(self.language)
            nlp.add_pipe("sentencizer")
            logger.warning("Using fallback sentencizer")
            return nlp

    def segment(self, text: str, preserve_whitespace: bool = False) -> List[str]:
        """
        Segment text into sentences.

        Args:
            text: Input text to segment
            preserve_whitespace: If True, preserve leading/trailing whitespace

        Returns:
            List of sentence strings

        Example:
            >>> segmenter = SentenceSegmenter()
            >>> text = "Hello world. How are you? I'm fine."
            >>> sentences = segmenter.segment(text)
            >>> print(sentences)
            ['Hello world.', 'How are you?', "I'm fine."]
        """
        if not text or not text.strip():
            return []

        doc = self.nlp(text)
        sentences = [sent.text.strip() if not preserve_whitespace else sent.text for sent in doc.sents]

        # Filter out empty sentences
        return [s for s in sentences if s.strip()]

    def segment_with_metadata(
        self, text: str, speaker: Optional[str] = None, timestamp: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Segment text into sentences with metadata.

        Args:
            text: Input text
            speaker: Speaker identifier
            timestamp: Timestamp information

        Returns:
            List of sentence dictionaries with metadata

        Example:
            >>> segmenter = SentenceSegmenter()
            >>> result = segmenter.segment_with_metadata(
            ...     "Hello. How are you?",
            ...     speaker="Student A",
            ...     timestamp="00:01:23"
            ... )
            >>> print(result)
            [
                {'text': 'Hello.', 'speaker': 'Student A', 'timestamp': '00:01:23', 'index': 0},
                {'text': 'How are you?', 'speaker': 'Student A', 'timestamp': '00:01:23', 'index': 1}
            ]
        """
        sentences = self.segment(text)

        return [
            {
                "text": sent,
                "speaker": speaker or "unknown",
                "timestamp": timestamp or "",
                "index": idx,
                "char_start": text.find(sent),
                "char_end": text.find(sent) + len(sent),
            }
            for idx, sent in enumerate(sentences)
        ]

    def segment_transcript(self, segments: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Segment transcript with speaker information.

        Args:
            segments: List of speaker segments with 'speaker' and 'text' keys

        Returns:
            List of sentence-level segments with metadata

        Example:
            >>> segmenter = SentenceSegmenter()
            >>> transcript = [
            ...     {'speaker': 'Teacher', 'text': 'Good morning. Let us begin.'},
            ...     {'speaker': 'Student A', 'text': 'I have a question.'}
            ... ]
            >>> result = segmenter.segment_transcript(transcript)
        """
        all_sentences = []
        sentence_counter = 0

        for segment in segments:
            speaker = segment.get("speaker", "unknown")
            text = segment.get("text", "")
            timestamp = segment.get("timestamp", "")

            sentences = self.segment(text)

            for sent in sentences:
                all_sentences.append(
                    {
                        "text": sent,
                        "speaker": speaker,
                        "timestamp": timestamp,
                        "sentence_id": sentence_counter,
                        "segment_id": segment.get("id", ""),
                    }
                )
                sentence_counter += 1

        return all_sentences

    def segment_batch(self, texts: List[str]) -> List[List[str]]:
        """
        Segment multiple texts efficiently using spaCy's batch processing.

        Args:
            texts: List of input texts

        Returns:
            List of sentence lists for each text
        """
        results = []

        # Use spaCy's pipe for efficient batch processing
        for doc in self.nlp.pipe(texts):
            sentences = [sent.text.strip() for sent in doc.sents]
            results.append([s for s in sentences if s.strip()])

        return results

    def add_custom_boundaries(self, patterns: List[str]) -> None:
        """
        Add custom sentence boundary patterns.

        Args:
            patterns: List of regex patterns for sentence boundaries

        Example:
            >>> segmenter = SentenceSegmenter()
            >>> segmenter.add_custom_boundaries([r"\n\n", r"---"])
        """
        # Custom component to add sentence boundaries
        @Language.component("custom_sentence_boundaries")
        def custom_boundaries(doc):
            for token in doc[:-1]:
                for pattern in patterns:
                    if pattern in token.text:
                        doc[token.i + 1].is_sent_start = True
            return doc

        if "custom_sentence_boundaries" not in self.nlp.pipe_names:
            self.nlp.add_pipe("custom_sentence_boundaries", before="parser")

    def get_sentence_count(self, text: str) -> int:
        """
        Get the number of sentences in text.

        Args:
            text: Input text

        Returns:
            Sentence count
        """
        if not text or not text.strip():
            return 0

        doc = self.nlp(text)
        return sum(1 for _ in doc.sents)
