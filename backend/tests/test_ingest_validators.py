"""Tests for file format validators"""

import pytest

from app.ingest.models import FileFormat
from app.ingest.validators import FileValidator, ValidationError


class TestJSONLValidator:
    """Test JSONL format validation"""

    def test_valid_jsonl(self) -> None:
        """Test valid JSONL format"""
        content = """{"speaker": "Student A", "text": "Hello", "timestamp": "00:00:01"}
{"speaker": "Teacher", "text": "Hi there", "timestamp": "00:00:02"}
{"speaker": "Student B", "text": "Good morning", "timestamp": "00:00:03"}"""

        result = FileValidator.validate_jsonl(content)
        assert result["valid"] is True
        assert result["format"] == "jsonl"
        assert result["line_count"] == 3
        assert "speaker" in result["sample"]

    def test_empty_jsonl(self) -> None:
        """Test empty JSONL file"""
        with pytest.raises(ValidationError, match="JSONL file is empty"):
            FileValidator.validate_jsonl("")

    def test_invalid_json_line(self) -> None:
        """Test JSONL with invalid JSON line"""
        content = """{"speaker": "Student A", "text": "Hello"}
{invalid json}"""

        with pytest.raises(ValidationError, match="Line 2: Invalid JSON"):
            FileValidator.validate_jsonl(content)

    def test_jsonl_missing_recommended_fields(self) -> None:
        """Test JSONL missing recommended fields"""
        content = """{"name": "Student A", "content": "Hello"}"""

        result = FileValidator.validate_jsonl(content)
        assert result["valid"] is True
        assert len(result["missing_recommended_fields"]) > 0


class TestCSVValidator:
    """Test CSV format validation"""

    def test_valid_csv(self) -> None:
        """Test valid CSV format"""
        content = """speaker,text,timestamp
Student A,Hello,00:00:01
Teacher,Hi there,00:00:02
Student B,Good morning,00:00:03"""

        result = FileValidator.validate_csv(content)
        assert result["valid"] is True
        assert result["format"] == "csv"
        assert result["row_count"] == 3
        assert len(result["columns"]) == 3

    def test_empty_csv(self) -> None:
        """Test empty CSV file"""
        with pytest.raises(ValidationError, match="CSV file is empty"):
            FileValidator.validate_csv("")

    def test_csv_no_data_rows(self) -> None:
        """Test CSV with header but no data"""
        content = "speaker,text,timestamp\n"

        with pytest.raises(ValidationError, match="contains no data rows"):
            FileValidator.validate_csv(content)

    def test_csv_missing_recommended_fields(self) -> None:
        """Test CSV missing recommended fields"""
        content = """name,content
Student A,Hello
Teacher,Hi there"""

        result = FileValidator.validate_csv(content)
        assert result["valid"] is True
        assert len(result["missing_recommended_fields"]) > 0


class TestTXTValidator:
    """Test plain text format validation"""

    def test_valid_text(self) -> None:
        """Test valid text format"""
        content = """Student A: Hello everyone
Teacher: Good morning class
Student B: How are you?"""

        result = FileValidator.validate_txt(content)
        assert result["valid"] is True
        assert result["format"] == "txt"
        assert result["line_count"] == 3
        assert result["has_speaker_structure"] is True

    def test_empty_text(self) -> None:
        """Test empty text file"""
        with pytest.raises(ValidationError, match="Text file is empty"):
            FileValidator.validate_txt("")

    def test_text_without_structure(self) -> None:
        """Test text without speaker structure"""
        content = """This is just plain text
without any speaker structure
or timestamps."""

        result = FileValidator.validate_txt(content)
        assert result["valid"] is True
        assert result["has_speaker_structure"] is False


class TestFileValidator:
    """Test general file validation"""

    def test_validate_file_format_jsonl(self) -> None:
        """Test validate_file_format with JSONL"""
        content = '{"speaker": "Test", "text": "Hello"}\n'
        result = FileValidator.validate_file_format(FileFormat.JSONL, content)
        assert result["valid"] is True

    def test_validate_file_format_csv(self) -> None:
        """Test validate_file_format with CSV"""
        content = "speaker,text\nTest,Hello\n"
        result = FileValidator.validate_file_format(FileFormat.CSV, content)
        assert result["valid"] is True

    def test_validate_file_format_txt(self) -> None:
        """Test validate_file_format with TXT"""
        content = "Test: Hello\n"
        result = FileValidator.validate_file_format(FileFormat.TXT, content)
        assert result["valid"] is True

    def test_validate_unsupported_format(self) -> None:
        """Test validation of binary format raises error"""
        with pytest.raises(ValidationError, match="validation not implemented"):
            FileValidator.validate_file_format(FileFormat.PDF, "dummy content")

    def test_get_content_type(self) -> None:
        """Test content type retrieval"""
        assert FileValidator.get_content_type(FileFormat.JSONL) == "application/jsonl"
        assert FileValidator.get_content_type(FileFormat.CSV) == "text/csv"
        assert FileValidator.get_content_type(FileFormat.PDF) == "application/pdf"
        assert FileValidator.get_content_type(FileFormat.PNG) == "image/png"

    def test_is_transcript_format(self) -> None:
        """Test transcript format detection"""
        assert FileValidator.is_transcript_format(FileFormat.JSONL) is True
        assert FileValidator.is_transcript_format(FileFormat.CSV) is True
        assert FileValidator.is_transcript_format(FileFormat.TXT) is True
        assert FileValidator.is_transcript_format(FileFormat.PDF) is False

    def test_is_artifact_format(self) -> None:
        """Test artifact format detection"""
        assert FileValidator.is_artifact_format(FileFormat.PDF) is True
        assert FileValidator.is_artifact_format(FileFormat.DOCX) is True
        assert FileValidator.is_artifact_format(FileFormat.PNG) is True
        assert FileValidator.is_artifact_format(FileFormat.JSONL) is False
