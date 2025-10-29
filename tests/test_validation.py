"""Tests for validation module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from orchestrator.validation.proof_of_change import (
    ProofOfChange,
    ProofOfChangeGenerator,
)
from orchestrator.validation.validator import (
    LintValidator,
    SecurityValidator,
    TestValidator,
    TypeCheckValidator,
    ValidationPipeline,
    ValidationResult,
    ValidationStatus,
)


class TestProofOfChange:
    """Test ProofOfChange class."""

    def test_to_dict(self) -> None:
        """Test converting PoC to dictionary."""
        poc = ProofOfChange(
            change_id="test123",
            timestamp="2025-10-29T00:00:00Z",
            files_changed=["file1.py", "file2.py"],
            diff="--- a/file1.py\n+++ b/file1.py\n",
            rationale="Test change",
            tests_added=["test_file1.py"],
            tests_passed=True,
            validation_hash="abc123",
            metadata={"author": "test"},
        )

        data = poc.to_dict()

        assert data["change_id"] == "test123"
        assert data["timestamp"] == "2025-10-29T00:00:00Z"
        assert data["files_changed"] == ["file1.py", "file2.py"]
        assert data["rationale"] == "Test change"
        assert data["tests_passed"] is True
        assert data["metadata"]["author"] == "test"

    def test_to_json(self) -> None:
        """Test converting PoC to JSON."""
        poc = ProofOfChange(
            change_id="test123",
            timestamp="2025-10-29T00:00:00Z",
            files_changed=["file1.py"],
            diff="test diff",
            rationale="Test",
            tests_added=[],
            tests_passed=True,
            validation_hash="abc123",
        )

        json_str = poc.to_json()
        assert "test123" in json_str
        assert "2025-10-29" in json_str

    def test_from_dict(self) -> None:
        """Test creating PoC from dictionary."""
        data = {
            "change_id": "test123",
            "timestamp": "2025-10-29T00:00:00Z",
            "files_changed": ["file1.py"],
            "diff": "test diff",
            "rationale": "Test",
            "tests_added": [],
            "tests_passed": True,
            "validation_hash": "abc123",
            "metadata": {},
        }

        poc = ProofOfChange.from_dict(data)

        assert poc.change_id == "test123"
        assert poc.timestamp == "2025-10-29T00:00:00Z"
        assert poc.files_changed == ["file1.py"]

    def test_from_json(self) -> None:
        """Test creating PoC from JSON."""
        json_str = """
        {
            "change_id": "test123",
            "timestamp": "2025-10-29T00:00:00Z",
            "files_changed": ["file1.py"],
            "diff": "test diff",
            "rationale": "Test",
            "tests_added": [],
            "tests_passed": true,
            "validation_hash": "abc123",
            "metadata": {}
        }
        """

        poc = ProofOfChange.from_json(json_str)

        assert poc.change_id == "test123"
        assert poc.tests_passed is True


class TestProofOfChangeGenerator:
    """Test ProofOfChangeGenerator class."""

    def test_init(self) -> None:
        """Test generator initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ProofOfChangeGenerator(
                repo_path=tmpdir, output_dir=f"{tmpdir}/poc"
            )

            assert generator.repo_path == Path(tmpdir)
            assert generator.output_dir == Path(f"{tmpdir}/poc")
            assert generator.output_dir.exists()

    def test_compute_hash(self) -> None:
        """Test hash computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ProofOfChangeGenerator(tmpdir, f"{tmpdir}/poc")

            hash1 = generator._compute_hash("test content")
            hash2 = generator._compute_hash("test content")
            hash3 = generator._compute_hash("different content")

            assert hash1 == hash2
            assert hash1 != hash3
            assert len(hash1) == 64  # SHA256 hex length

    def test_generate_change_id(self) -> None:
        """Test change ID generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ProofOfChangeGenerator(tmpdir, f"{tmpdir}/poc")

            change_id1 = generator._generate_change_id("2025-10-29", "diff1")
            change_id2 = generator._generate_change_id("2025-10-29", "diff1")
            change_id3 = generator._generate_change_id("2025-10-29", "diff2")

            assert change_id1 == change_id2
            assert change_id1 != change_id3
            assert len(change_id1) == 16

    def test_list_artifacts(self) -> None:
        """Test listing artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "poc"
            output_dir.mkdir()

            # Create test artifacts
            (output_dir / "poc_abc123.json").write_text("{}")
            (output_dir / "poc_def456.json").write_text("{}")

            generator = ProofOfChangeGenerator(tmpdir, output_dir)
            artifacts = generator.list_artifacts()

            assert len(artifacts) == 2
            assert "abc123" in artifacts
            assert "def456" in artifacts

    def test_verify_artifact(self) -> None:
        """Test artifact verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ProofOfChangeGenerator(tmpdir, f"{tmpdir}/poc")

            # Create valid PoC
            poc = ProofOfChange(
                change_id="test123",
                timestamp="2025-10-29T00:00:00Z",
                files_changed=["file1.py"],
                diff="test diff",
                rationale="Test",
                tests_added=[],
                tests_passed=True,
                validation_hash="correct_hash",
            )

            # Recompute expected hash
            import json

            validation_data = {
                "files_changed": poc.files_changed,
                "diff": poc.diff,
                "tests_added": poc.tests_added,
                "tests_passed": poc.tests_passed,
            }
            expected_hash = generator._compute_hash(
                json.dumps(validation_data, sort_keys=True)
            )

            # Update PoC with correct hash
            poc.validation_hash = expected_hash

            assert generator.verify_artifact(poc) is True

            # Tamper with hash
            poc.validation_hash = "tampered_hash"
            assert generator.verify_artifact(poc) is False


class TestValidationResult:
    """Test ValidationResult class."""

    def test_bool_passed(self) -> None:
        """Test ValidationResult boolean for passed status."""
        result = ValidationResult(
            status=ValidationStatus.PASSED,
            validator_name="TestValidator",
            message="Test passed",
        )

        assert bool(result) is True

    def test_bool_failed(self) -> None:
        """Test ValidationResult boolean for failed status."""
        result = ValidationResult(
            status=ValidationStatus.FAILED,
            validator_name="TestValidator",
            message="Test failed",
        )

        assert bool(result) is False

    def test_to_dict(self) -> None:
        """Test converting ValidationResult to dictionary."""
        result = ValidationResult(
            status=ValidationStatus.PASSED,
            validator_name="TestValidator",
            message="Test passed",
            details={"count": 0},
            errors=None,
        )

        data = result.to_dict()

        assert data["status"] == "passed"
        assert data["validator_name"] == "TestValidator"
        assert data["message"] == "Test passed"
        assert data["details"] == {"count": 0}


class TestLintValidator:
    """Test LintValidator class."""

    def test_init(self) -> None:
        """Test lint validator initialization."""
        validator = LintValidator("/tmp/project", max_issues=10)

        assert validator.project_dir == Path("/tmp/project")
        assert validator.max_issues == 10
        assert validator.name == "LintValidator"

    @patch("subprocess.run")
    def test_validate_pass(self, mock_run: Mock) -> None:
        """Test lint validation passing."""
        mock_result = Mock()
        mock_result.stdout = "5\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        validator = LintValidator("/tmp/project", max_issues=10)
        result = validator.validate()

        assert result.status == ValidationStatus.PASSED
        assert result.details["issue_count"] == 5

    @patch("subprocess.run")
    def test_validate_fail(self, mock_run: Mock) -> None:
        """Test lint validation failing."""
        mock_result = Mock()
        mock_result.stdout = "15\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        validator = LintValidator("/tmp/project", max_issues=10)
        result = validator.validate()

        assert result.status == ValidationStatus.FAILED
        assert result.details["issue_count"] == 15


class TestTypeCheckValidator:
    """Test TypeCheckValidator class."""

    def test_init(self) -> None:
        """Test type check validator initialization."""
        validator = TypeCheckValidator("/tmp/project", strict=True)

        assert validator.project_dir == Path("/tmp/project")
        assert validator.strict is True

    @patch("subprocess.run")
    def test_validate_pass(self, mock_run: Mock) -> None:
        """Test type check validation passing."""
        mock_result = Mock()
        mock_result.stdout = "Success: no issues found\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        validator = TypeCheckValidator("/tmp/project")
        result = validator.validate()

        assert result.status == ValidationStatus.PASSED
        assert result.details["error_count"] == 0


class TestValidationPipeline:
    """Test ValidationPipeline class."""

    def test_init(self) -> None:
        """Test pipeline initialization."""
        pipeline = ValidationPipeline("/tmp/project")

        assert pipeline.project_dir == Path("/tmp/project")
        assert len(pipeline.validators) == 0

    def test_add_validator(self) -> None:
        """Test adding validators to pipeline."""
        pipeline = ValidationPipeline("/tmp/project")
        validator = LintValidator("/tmp/project")

        pipeline.add_validator(validator)

        assert len(pipeline.validators) == 1
        assert pipeline.validators[0] == validator

    def test_all_passed_true(self) -> None:
        """Test all_passed with all passing results."""
        pipeline = ValidationPipeline("/tmp/project")

        results = [
            ValidationResult(
                status=ValidationStatus.PASSED,
                validator_name="Test1",
                message="Passed",
            ),
            ValidationResult(
                status=ValidationStatus.PASSED,
                validator_name="Test2",
                message="Passed",
            ),
        ]

        assert pipeline.all_passed(results) is True

    def test_all_passed_false(self) -> None:
        """Test all_passed with some failing results."""
        pipeline = ValidationPipeline("/tmp/project")

        results = [
            ValidationResult(
                status=ValidationStatus.PASSED,
                validator_name="Test1",
                message="Passed",
            ),
            ValidationResult(
                status=ValidationStatus.FAILED,
                validator_name="Test2",
                message="Failed",
            ),
        ]

        assert pipeline.all_passed(results) is False
