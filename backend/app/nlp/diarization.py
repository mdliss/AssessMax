"""Speaker diarization mapping module"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DiarizationMapper:
    """
    Map speaker diarization to transcript segments.

    Handles:
    - Speaker identification and normalization
    - Timestamp-based speaker mapping
    - Student vs. Teacher classification
    - Multi-speaker conversation tracking
    """

    def __init__(self) -> None:
        """Initialize diarization mapper."""
        self.speaker_mapping = {}
        self.speaker_roles = {}  # teacher, student, unknown

    def map_speakers(
        self, sentences: List[Dict[str, str]], diarization_data: Optional[List[Dict]] = None
    ) -> List[Dict[str, str]]:
        """
        Map speaker information to sentence segments.

        Args:
            sentences: List of sentence dictionaries
            diarization_data: Optional external diarization data with timestamps

        Returns:
            Sentences with enhanced speaker information

        Example:
            >>> mapper = DiarizationMapper()
            >>> sentences = [
            ...     {'text': 'Good morning', 'speaker': 'Speaker_0', 'timestamp': '00:00:05'},
            ...     {'text': 'Hello', 'speaker': 'Speaker_1', 'timestamp': '00:00:08'}
            ... ]
            >>> result = mapper.map_speakers(sentences)
        """
        if diarization_data:
            return self._map_with_external_data(sentences, diarization_data)

        # Use existing speaker information from transcript
        for sentence in sentences:
            speaker = sentence.get("speaker", "unknown")
            sentence["speaker_id"] = self._normalize_speaker_id(speaker)
            sentence["speaker_role"] = self._classify_speaker_role(speaker)

        return sentences

    def _map_with_external_data(
        self, sentences: List[Dict[str, str]], diarization_data: List[Dict]
    ) -> List[Dict[str, str]]:
        """
        Map speakers using external diarization data (e.g., from audio processing).

        Args:
            sentences: Sentence segments
            diarization_data: External speaker timestamps

        Returns:
            Sentences with mapped speakers
        """
        for sentence in sentences:
            timestamp = sentence.get("timestamp", "")
            if timestamp:
                # Find matching speaker from diarization data
                speaker_info = self._find_speaker_at_timestamp(timestamp, diarization_data)
                if speaker_info:
                    sentence["speaker_id"] = speaker_info["speaker_id"]
                    sentence["speaker_role"] = speaker_info.get("role", "unknown")
                    sentence["diarization_confidence"] = speaker_info.get("confidence", 0.0)

        return sentences

    def _find_speaker_at_timestamp(
        self, timestamp: str, diarization_data: List[Dict]
    ) -> Optional[Dict]:
        """
        Find speaker information at given timestamp.

        Args:
            timestamp: Timestamp string (HH:MM:SS)
            diarization_data: Speaker timestamp data

        Returns:
            Speaker information or None
        """
        try:
            target_seconds = self._timestamp_to_seconds(timestamp)

            for diarization in diarization_data:
                start = self._timestamp_to_seconds(diarization["start"])
                end = self._timestamp_to_seconds(diarization["end"])

                if start <= target_seconds <= end:
                    return diarization

        except (ValueError, KeyError) as e:
            logger.warning(f"Error processing timestamp {timestamp}: {e}")

        return None

    def _timestamp_to_seconds(self, timestamp: str) -> float:
        """
        Convert timestamp string to seconds.

        Args:
            timestamp: Timestamp in HH:MM:SS or MM:SS format

        Returns:
            Time in seconds
        """
        parts = timestamp.strip().split(":")
        if len(parts) == 3:
            h, m, s = map(float, parts)
            return h * 3600 + m * 60 + s
        elif len(parts) == 2:
            m, s = map(float, parts)
            return m * 60 + s
        else:
            raise ValueError(f"Invalid timestamp format: {timestamp}")

    def _normalize_speaker_id(self, speaker: str) -> str:
        """
        Normalize speaker identifier.

        Args:
            speaker: Raw speaker string

        Returns:
            Normalized speaker ID

        Example:
            >>> mapper = DiarizationMapper()
            >>> mapper._normalize_speaker_id("Teacher Smith")
            'teacher'
            >>> mapper._normalize_speaker_id("Student A")
            'student_a'
        """
        speaker_lower = speaker.lower().strip()

        # Check if already normalized
        if speaker_lower in self.speaker_mapping:
            return self.speaker_mapping[speaker_lower]

        # Detect teacher
        if any(keyword in speaker_lower for keyword in ["teacher", "educator", "instructor", "prof"]):
            normalized = "teacher"
        # Detect specific student
        elif "student" in speaker_lower:
            # Extract student identifier (e.g., "Student A" -> "student_a")
            normalized = speaker_lower.replace(" ", "_")
        # Generic speaker label
        elif "speaker" in speaker_lower:
            normalized = speaker_lower.replace(" ", "_")
        else:
            normalized = speaker_lower.replace(" ", "_")

        self.speaker_mapping[speaker_lower] = normalized
        return normalized

    def _classify_speaker_role(self, speaker: str) -> str:
        """
        Classify speaker role (teacher, student, unknown).

        Args:
            speaker: Speaker identifier

        Returns:
            Role classification
        """
        speaker_lower = speaker.lower()

        if speaker_lower in self.speaker_roles:
            return self.speaker_roles[speaker_lower]

        # Determine role
        if any(keyword in speaker_lower for keyword in ["teacher", "educator", "instructor", "prof"]):
            role = "teacher"
        elif "student" in speaker_lower:
            role = "student"
        else:
            role = "unknown"

        self.speaker_roles[speaker_lower] = role
        return role

    def assign_roles(self, speaker_id: str, role: str) -> None:
        """
        Manually assign role to speaker.

        Args:
            speaker_id: Speaker identifier
            role: Role to assign (teacher, student, unknown)
        """
        if role not in ["teacher", "student", "unknown"]:
            raise ValueError(f"Invalid role: {role}")

        self.speaker_roles[speaker_id.lower()] = role
        logger.info(f"Assigned role '{role}' to speaker '{speaker_id}'")

    def get_speaker_statistics(self, sentences: List[Dict[str, str]]) -> Dict[str, Dict]:
        """
        Get statistics about speakers in the transcript.

        Args:
            sentences: Sentence segments with speaker information

        Returns:
            Dictionary of speaker statistics

        Example:
            >>> mapper = DiarizationMapper()
            >>> stats = mapper.get_speaker_statistics(sentences)
            >>> print(stats)
            {
                'teacher': {'count': 25, 'word_count': 450, 'role': 'teacher'},
                'student_a': {'count': 10, 'word_count': 85, 'role': 'student'}
            }
        """
        stats = {}

        for sentence in sentences:
            speaker_id = sentence.get("speaker_id", "unknown")
            speaker_role = sentence.get("speaker_role", "unknown")

            if speaker_id not in stats:
                stats[speaker_id] = {
                    "count": 0,
                    "word_count": 0,
                    "role": speaker_role,
                    "sentences": [],
                }

            stats[speaker_id]["count"] += 1
            stats[speaker_id]["word_count"] += len(sentence.get("text", "").split())
            stats[speaker_id]["sentences"].append(sentence.get("text", ""))

        return stats

    def identify_students(self, sentences: List[Dict[str, str]]) -> List[str]:
        """
        Identify all student speakers in the transcript.

        Args:
            sentences: Sentence segments

        Returns:
            List of student speaker IDs
        """
        students = set()

        for sentence in sentences:
            speaker_id = sentence.get("speaker_id", "")
            speaker_role = sentence.get("speaker_role", "unknown")

            if speaker_role == "student":
                students.add(speaker_id)

        return sorted(list(students))

    def merge_speaker_turns(self, sentences: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Merge consecutive sentences from the same speaker into turns.

        Args:
            sentences: Sentence segments

        Returns:
            List of speaker turns with merged text

        Example:
            >>> mapper = DiarizationMapper()
            >>> sentences = [
            ...     {'speaker_id': 'teacher', 'text': 'Hello.'},
            ...     {'speaker_id': 'teacher', 'text': 'How are you?'},
            ...     {'speaker_id': 'student_a', 'text': 'I am fine.'}
            ... ]
            >>> turns = mapper.merge_speaker_turns(sentences)
            >>> print(turns)
            [
                {'speaker_id': 'teacher', 'text': 'Hello. How are you?', 'sentence_count': 2},
                {'speaker_id': 'student_a', 'text': 'I am fine.', 'sentence_count': 1}
            ]
        """
        if not sentences:
            return []

        turns = []
        current_turn = {
            "speaker_id": sentences[0].get("speaker_id", "unknown"),
            "speaker_role": sentences[0].get("speaker_role", "unknown"),
            "text": sentences[0].get("text", ""),
            "sentence_count": 1,
            "sentences": [sentences[0].get("text", "")],
        }

        for sentence in sentences[1:]:
            speaker_id = sentence.get("speaker_id", "unknown")

            if speaker_id == current_turn["speaker_id"]:
                # Same speaker, merge
                current_turn["text"] += " " + sentence.get("text", "")
                current_turn["sentence_count"] += 1
                current_turn["sentences"].append(sentence.get("text", ""))
            else:
                # New speaker, save current turn and start new one
                turns.append(current_turn)
                current_turn = {
                    "speaker_id": speaker_id,
                    "speaker_role": sentence.get("speaker_role", "unknown"),
                    "text": sentence.get("text", ""),
                    "sentence_count": 1,
                    "sentences": [sentence.get("text", "")],
                }

        # Add last turn
        turns.append(current_turn)

        return turns
