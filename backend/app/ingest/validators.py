"""File format validation utilities"""

import csv
import json
from io import StringIO
from typing import Any

from app.ingest.models import FileFormat


class ValidationError(Exception):
    """Custom exception for validation errors"""

    pass


class FileValidator:
    """Validates file formats and content structure"""

    @staticmethod
    def validate_jsonl(content: str) -> dict[str, Any]:
        """
        Validate JSONL (JSON Lines) format.

        Expected format:
        {"speaker": "Student A", "text": "...", "timestamp": "HH:MM:SS"}
        {"speaker": "Teacher", "text": "...", "timestamp": "HH:MM:SS"}

        Args:
            content: File content as string

        Returns:
            Validation result with line count and sample

        Raises:
            ValidationError: If format is invalid
        """
        if not content.strip():
            raise ValidationError("JSONL file is empty")

        lines = content.strip().split("\n")
        parsed_lines = []

        for i, line in enumerate(lines, 1):
            if not line.strip():
                continue

            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    raise ValidationError(f"Line {i}: Expected JSON object, got {type(obj)}")
                parsed_lines.append(obj)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Line {i}: Invalid JSON - {e}")

        if not parsed_lines:
            raise ValidationError("JSONL file contains no valid lines")

        # Check for common required fields (flexible validation)
        sample = parsed_lines[0]
        recommended_fields = {"speaker", "text", "timestamp"}
        missing_fields = recommended_fields - set(sample.keys())

        return {
            "valid": True,
            "format": "jsonl",
            "line_count": len(parsed_lines),
            "sample": parsed_lines[0],
            "missing_recommended_fields": list(missing_fields) if missing_fields else [],
            "message": f"Valid JSONL with {len(parsed_lines)} records",
        }

    @staticmethod
    def validate_csv(content: str) -> dict[str, Any]:
        """
        Validate CSV format.

        Expected columns: speaker, text, timestamp (or similar)

        Args:
            content: File content as string

        Returns:
            Validation result with row count and columns

        Raises:
            ValidationError: If format is invalid
        """
        if not content.strip():
            raise ValidationError("CSV file is empty")

        try:
            reader = csv.DictReader(StringIO(content))
            rows = list(reader)

            if not rows:
                raise ValidationError("CSV file contains no data rows")

            columns = reader.fieldnames or []
            if not columns:
                raise ValidationError("CSV file has no header row")

            # Check for common required fields (flexible validation)
            recommended_fields = {"speaker", "text", "timestamp"}
            columns_lower = {col.lower() for col in columns}
            missing_fields = recommended_fields - columns_lower

            return {
                "valid": True,
                "format": "csv",
                "row_count": len(rows),
                "columns": columns,
                "sample": rows[0],
                "missing_recommended_fields": list(missing_fields) if missing_fields else [],
                "message": f"Valid CSV with {len(rows)} rows and {len(columns)} columns",
            }

        except csv.Error as e:
            raise ValidationError(f"Invalid CSV format: {e}")

    @staticmethod
    def validate_txt(content: str) -> dict[str, Any]:
        """
        Validate plain text format.

        Accepts freeform text. Optionally looks for speaker patterns like:
        "Speaker Name: text here"
        "[HH:MM:SS] Speaker: text"

        Args:
            content: File content as string

        Returns:
            Validation result with line count

        Raises:
            ValidationError: If format is invalid
        """
        if not content.strip():
            raise ValidationError("Text file is empty")

        lines = [line for line in content.split("\n") if line.strip()]

        if not lines:
            raise ValidationError("Text file contains no content")

        # Try to detect if it has speaker patterns
        speaker_patterns = 0
        for line in lines[:10]:  # Check first 10 lines
            if ":" in line and len(line.split(":", 1)[0]) < 50:
                speaker_patterns += 1

        has_structure = speaker_patterns >= 3

        return {
            "valid": True,
            "format": "txt",
            "line_count": len(lines),
            "char_count": len(content),
            "has_speaker_structure": has_structure,
            "message": f"Valid text file with {len(lines)} lines",
        }

    @staticmethod
    def validate_file_format(file_format: FileFormat, content: str) -> dict[str, Any]:
        """
        Validate file content based on format.

        Args:
            file_format: Expected file format
            content: File content as string

        Returns:
            Validation result

        Raises:
            ValidationError: If validation fails
        """
        validators = {
            FileFormat.JSONL: FileValidator.validate_jsonl,
            FileFormat.CSV: FileValidator.validate_csv,
            FileFormat.TXT: FileValidator.validate_txt,
        }

        validator = validators.get(file_format)
        if not validator:
            raise ValidationError(
                f"Format {file_format} validation not implemented. "
                f"Binary formats (PDF, DOCX, images) validated by S3 upload only."
            )

        return validator(content)

    @staticmethod
    def get_content_type(file_format: FileFormat) -> str:
        """
        Get MIME content type for file format.

        Args:
            file_format: File format

        Returns:
            MIME content type
        """
        content_types = {
            FileFormat.JSONL: "application/jsonl",
            FileFormat.CSV: "text/csv",
            FileFormat.TXT: "text/plain",
            FileFormat.PDF: "application/pdf",
            FileFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            FileFormat.PNG: "image/png",
            FileFormat.JPG: "image/jpeg",
            FileFormat.JPEG: "image/jpeg",
        }
        return content_types.get(file_format, "application/octet-stream")

    @staticmethod
    def is_transcript_format(file_format: FileFormat) -> bool:
        """
        Check if format is for transcripts (vs artifacts).

        Args:
            file_format: File format

        Returns:
            True if transcript format
        """
        return file_format in [FileFormat.JSONL, FileFormat.CSV, FileFormat.TXT]

    @staticmethod
    def is_artifact_format(file_format: FileFormat) -> bool:
        """
        Check if format is for artifacts (vs transcripts).

        Args:
            file_format: File format

        Returns:
            True if artifact format
        """
        return file_format in [
            FileFormat.PDF,
            FileFormat.DOCX,
            FileFormat.PNG,
            FileFormat.JPG,
            FileFormat.JPEG,
        ]
