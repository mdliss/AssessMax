"""Language detection module using spaCy and langdetect"""

import logging
from typing import Dict, List, Optional

import spacy
from langdetect import LangDetectException, detect_langs

logger = logging.getLogger(__name__)


class LanguageDetector:
    """
    Detect language of text using multiple methods for accuracy.

    Uses langdetect as primary method and spaCy as fallback.
    Supports English, Spanish, French, German, Chinese, and more.
    """

    def __init__(self, default_language: str = "en") -> None:
        """
        Initialize language detector.

        Args:
            default_language: Default language code if detection fails
        """
        self.default_language = default_language
        self.supported_languages = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic",
            "hi": "Hindi",
            "pt": "Portuguese",
        }

        # Pre-load common spaCy models for validation
        self.spacy_models = {}
        self._load_spacy_models()

    def _load_spacy_models(self) -> None:
        """Pre-load common spaCy models for language validation"""
        model_mapping = {
            "en": "en_core_web_sm",
            "es": "es_core_news_sm",
            "fr": "fr_core_news_sm",
            "de": "de_core_news_sm",
        }

        for lang_code, model_name in model_mapping.items():
            try:
                self.spacy_models[lang_code] = spacy.load(model_name)
                logger.info(f"Loaded spaCy model: {model_name}")
            except OSError:
                logger.warning(f"spaCy model {model_name} not available. Run: python -m spacy download {model_name}")

    def detect(self, text: str, min_confidence: float = 0.7) -> Dict[str, any]:
        """
        Detect the language of the given text.

        Args:
            text: Input text to detect language
            min_confidence: Minimum confidence threshold (0.0 to 1.0)

        Returns:
            Dictionary with language code, name, confidence, and method used

        Example:
            >>> detector = LanguageDetector()
            >>> result = detector.detect("Hello, how are you?")
            >>> print(result)
            {'language': 'en', 'name': 'English', 'confidence': 0.99, 'method': 'langdetect'}
        """
        if not text or len(text.strip()) < 3:
            logger.warning("Text too short for reliable language detection")
            return self._default_result(reason="text_too_short")

        # Primary method: langdetect (fast and accurate)
        try:
            lang_probs = detect_langs(text)
            if lang_probs:
                top_lang = lang_probs[0]
                lang_code = top_lang.lang
                confidence = top_lang.prob

                if confidence >= min_confidence:
                    return {
                        "language": lang_code,
                        "name": self.supported_languages.get(lang_code, "Unknown"),
                        "confidence": round(confidence, 3),
                        "method": "langdetect",
                        "alternatives": [
                            {"language": lp.lang, "confidence": round(lp.prob, 3)}
                            for lp in lang_probs[1:3]
                        ],
                    }
                else:
                    logger.info(f"Low confidence ({confidence:.2f}) for detected language: {lang_code}")

        except LangDetectException as e:
            logger.warning(f"langdetect failed: {e}")

        # Fallback: spaCy language detection (if available)
        spacy_result = self._detect_with_spacy(text)
        if spacy_result["confidence"] >= min_confidence:
            return spacy_result

        # Default fallback
        return self._default_result(reason="low_confidence")

    def _detect_with_spacy(self, text: str) -> Dict[str, any]:
        """
        Fallback language detection using spaCy models.

        Args:
            text: Input text

        Returns:
            Detection result dictionary
        """
        best_score = 0.0
        best_lang = None

        for lang_code, nlp in self.spacy_models.items():
            try:
                doc = nlp(text[:1000])  # Limit to first 1000 chars for speed
                # Simple heuristic: higher token count with valid POS tags = better match
                valid_tokens = sum(1 for token in doc if token.pos_ != "X")
                score = valid_tokens / len(doc) if len(doc) > 0 else 0

                if score > best_score:
                    best_score = score
                    best_lang = lang_code
            except Exception as e:
                logger.debug(f"spaCy detection failed for {lang_code}: {e}")

        if best_lang and best_score > 0.5:
            return {
                "language": best_lang,
                "name": self.supported_languages.get(best_lang, "Unknown"),
                "confidence": round(best_score, 3),
                "method": "spacy",
                "alternatives": [],
            }

        return self._default_result(reason="spacy_failed")

    def _default_result(self, reason: str = "unknown") -> Dict[str, any]:
        """
        Return default language result when detection fails.

        Args:
            reason: Reason for using default

        Returns:
            Default detection result
        """
        return {
            "language": self.default_language,
            "name": self.supported_languages.get(self.default_language, "English"),
            "confidence": 0.5,
            "method": "default",
            "reason": reason,
            "alternatives": [],
        }

    def detect_batch(self, texts: List[str], min_confidence: float = 0.7) -> List[Dict[str, any]]:
        """
        Detect language for multiple texts.

        Args:
            texts: List of input texts
            min_confidence: Minimum confidence threshold

        Returns:
            List of detection results
        """
        return [self.detect(text, min_confidence) for text in texts]

    def is_supported(self, language_code: str) -> bool:
        """
        Check if a language code is supported.

        Args:
            language_code: Two-letter ISO language code

        Returns:
            True if supported
        """
        return language_code in self.supported_languages
