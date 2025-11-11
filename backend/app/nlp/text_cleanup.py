"""Text cleanup and normalization module"""

import logging
import re
import unicodedata
from typing import Dict, List, Optional

import nltk
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)


class TextCleaner:
    """
    Clean and normalize text for NLP processing.

    Handles:
    - Unicode normalization
    - Whitespace standardization
    - Noise removal (URLs, emails, etc.)
    - Case normalization
    - Transcript-specific cleaning (timestamps, speaker tags)
    """

    def __init__(self, language: str = "en", preserve_case: bool = False) -> None:
        """
        Initialize text cleaner.

        Args:
            language: Language code for stopword removal
            preserve_case: If True, preserve original case
        """
        self.language = language
        self.preserve_case = preserve_case

        # Download NLTK data if not present
        try:
            self.stopwords = set(stopwords.words("english" if language == "en" else language))
        except LookupError:
            logger.warning("Stopwords not found, downloading...")
            nltk.download("stopwords", quiet=True)
            self.stopwords = set(stopwords.words("english" if language == "en" else language))

        # Compile regex patterns for efficiency
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile common regex patterns for text cleaning"""
        self.patterns = {
            "url": re.compile(
                r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
            ),
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "timestamp": re.compile(r"\[?\d{1,2}:\d{2}(?::\d{2})?\]?"),
            "speaker_tag": re.compile(r"^(?:Speaker|Student|Teacher|Educator)\s*[A-Z]?\d*:\s*", re.IGNORECASE),
            "multiple_spaces": re.compile(r"\s+"),
            "line_breaks": re.compile(r"\n+"),
            "special_chars": re.compile(r"[^\w\s\-.,!?;:()\[\]\"']"),
            "repeated_punct": re.compile(r"([.!?]){2,}"),
            "ellipsis": re.compile(r"\.{3,}"),
        }

    def clean(
        self,
        text: str,
        remove_urls: bool = True,
        remove_emails: bool = True,
        remove_timestamps: bool = True,
        remove_speaker_tags: bool = False,
        normalize_whitespace: bool = True,
        remove_stopwords: bool = False,
    ) -> str:
        """
        Clean and normalize text.

        Args:
            text: Input text to clean
            remove_urls: Remove URLs
            remove_emails: Remove email addresses
            remove_timestamps: Remove timestamps like [00:12:34]
            remove_speaker_tags: Remove speaker tags like "Speaker A:"
            normalize_whitespace: Normalize whitespace
            remove_stopwords: Remove common stopwords

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Unicode normalization (NFC form)
        text = unicodedata.normalize("NFC", text)

        # Remove URLs
        if remove_urls:
            text = self.patterns["url"].sub(" ", text)

        # Remove emails
        if remove_emails:
            text = self.patterns["email"].sub(" ", text)

        # Remove timestamps
        if remove_timestamps:
            text = self.patterns["timestamp"].sub(" ", text)

        # Remove speaker tags (for transcripts)
        if remove_speaker_tags:
            text = self.patterns["speaker_tag"].sub("", text)

        # Normalize repeated punctuation
        text = self.patterns["repeated_punct"].sub(r"\1", text)
        text = self.patterns["ellipsis"].sub("...", text)

        # Remove special characters (keep basic punctuation)
        text = self.patterns["special_chars"].sub(" ", text)

        # Normalize whitespace
        if normalize_whitespace:
            text = self.patterns["line_breaks"].sub(" ", text)
            text = self.patterns["multiple_spaces"].sub(" ", text)

        # Case normalization
        if not self.preserve_case:
            # Smart case normalization: lowercase except for proper nouns
            text = text.strip()
        else:
            text = text.strip()

        # Remove stopwords (optional, usually not needed for skill detection)
        if remove_stopwords:
            words = text.split()
            text = " ".join([w for w in words if w.lower() not in self.stopwords])

        return text

    def clean_transcript(self, text: str) -> str:
        """
        Clean transcript text with transcript-specific settings.

        Args:
            text: Raw transcript text

        Returns:
            Cleaned transcript
        """
        return self.clean(
            text,
            remove_urls=True,
            remove_emails=True,
            remove_timestamps=True,
            remove_speaker_tags=False,  # Keep for diarization
            normalize_whitespace=True,
            remove_stopwords=False,
        )

    def clean_artifact(self, text: str) -> str:
        """
        Clean artifact text (essays, documents) with appropriate settings.

        Args:
            text: Raw artifact text

        Returns:
            Cleaned artifact text
        """
        return self.clean(
            text,
            remove_urls=True,
            remove_emails=True,
            remove_timestamps=False,
            remove_speaker_tags=False,
            normalize_whitespace=True,
            remove_stopwords=False,
        )

    def extract_speaker_segments(self, text: str) -> List[Dict[str, str]]:
        """
        Extract speaker segments from transcript text.

        Args:
            text: Transcript text with speaker tags

        Returns:
            List of segments with speaker and text

        Example:
            >>> cleaner = TextCleaner()
            >>> text = "Teacher: Good morning class.\nStudent A: Good morning!"
            >>> segments = cleaner.extract_speaker_segments(text)
            >>> print(segments)
            [
                {'speaker': 'Teacher', 'text': 'Good morning class.'},
                {'speaker': 'Student A', 'text': 'Good morning!'}
            ]
        """
        segments = []
        lines = text.split("\n")

        for line in lines:
            match = self.patterns["speaker_tag"].search(line)
            if match:
                speaker = match.group(0).rstrip(":").strip()
                text_content = line[match.end():].strip()
                if text_content:
                    segments.append({"speaker": speaker, "text": text_content})
            elif segments:
                # Continuation of previous speaker
                segments[-1]["text"] += " " + line.strip()

        return segments

    def normalize_unicode(self, text: str) -> str:
        """
        Normalize unicode characters to standard forms.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Normalize to NFC (canonical composition)
        text = unicodedata.normalize("NFC", text)

        # Replace common unicode variations
        replacements = {
            "\u2018": "'",  # Left single quote
            "\u2019": "'",  # Right single quote
            "\u201C": '"',  # Left double quote
            "\u201D": '"',  # Right double quote
            "\u2013": "-",  # En dash
            "\u2014": "-",  # Em dash
            "\u2026": "...",  # Ellipsis
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def remove_noise(self, text: str, custom_patterns: Optional[List[re.Pattern]] = None) -> str:
        """
        Remove noise from text using custom patterns.

        Args:
            text: Input text
            custom_patterns: Additional regex patterns to remove

        Returns:
            Cleaned text
        """
        if custom_patterns:
            for pattern in custom_patterns:
                text = pattern.sub(" ", text)

        return self.patterns["multiple_spaces"].sub(" ", text).strip()
