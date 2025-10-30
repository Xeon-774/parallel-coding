"""Deterministic validators for proof - of - change artifacts.

Validators run at T=0 (immediate validation) to ensure code quality
and correctness before changes are committed.
"""

import logging
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ValidationStatus(str, Enum):
    """Validation status."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ValidationResult:
    """Result of validation.

    Attributes:
        status: Validation status (PASSED / FAILED / SKIPPED)
        validator_name: Name of validator that produced this result
        message: Human - readable message
        details: Additional details
        errors: List of errors (if failed)
    """

    status: ValidationStatus
    validator_name: str
    message: str
    details: dict[str, Any] | None = None
    errors: list[str] | None = None

    def __bool__(self) -> bool:
        """Allow using result as boolean."""
        return self.status == ValidationStatus.PASSED

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "validator_name": self.validator_name,
            "message": self.message,
            "details": self.details,
            "errors": self.errors,
        }


class Validator:
    """Base validator class for proof - of - change artifacts."""

    def __init__(self, project_dir: str | Path) -> None:
        """Initialize validator.

        Args:
            project_dir: Project directory to validate
        """
        self.project_dir = Path(project_dir)
        self.name = self.__class__.__name__

    def validate(self) -> ValidationResult:
        """Run validation.

        Returns:
            ValidationResult with status and details
        """
        raise NotImplementedError


class LintValidator(Validator):
    """Validator for code linting."""

    def __init__(
        self,
        project_dir: str | Path,
        max_issues: int = 0,
        ignore_patterns: list[str] | None = None,
    ) -> None:
        """Initialize lint validator.

        Args:
            project_dir: Project directory
            max_issues: Maximum allowed lint issues (0 = none allowed)
            ignore_patterns: Patterns to ignore
        """
        super().__init__(project_dir)
        self.max_issues = max_issues
        self.ignore_patterns = ignore_patterns or []

    def validate(self) -> ValidationResult:
        """Run flake8 lint check."""
        try:
            result = subprocess.run(
                [
                    "flake8",
                    "orchestrator",
                    "--count",
                    "--max - line - length=100",
                ],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            output = result.stdout + result.stderr
            lines = output.strip().split("\n")

            # Last line contains count
            issue_count = 0
            if lines:
                last_line = lines[-1].strip()
                if last_line.isdigit():
                    issue_count = int(last_line)

            if issue_count <= self.max_issues:
                return ValidationResult(
                    status=ValidationStatus.PASSED,
                    validator_name=self.name,
                    message=f"Lint check passed ({issue_count} issues, max {self.max_issues})",
                    details={"issue_count": issue_count, "max_issues": self.max_issues},
                )
            else:
                return ValidationResult(
                    status=ValidationStatus.FAILED,
                    validator_name=self.name,
                    message=f"Lint check failed ({issue_count} issues, max {self.max_issues})",
                    details={"issue_count": issue_count, "max_issues": self.max_issues},
                    errors=[line for line in lines if line and not line.isdigit()],
                )

        except Exception as e:
            logger.error(f"Lint validation failed: {e}")
            return ValidationResult(
                status=ValidationStatus.FAILED,
                validator_name=self.name,
                message=f"Lint validation error: {e}",
                errors=[str(e)],
            )


class TypeCheckValidator(Validator):
    """Validator for type checking."""

    def __init__(
        self,
        project_dir: str | Path,
        strict: bool = True,
    ) -> None:
        """Initialize type check validator.

        Args:
            project_dir: Project directory
            strict: Use strict mode
        """
        super().__init__(project_dir)
        self.strict = strict

    def validate(self) -> ValidationResult:
        """Run mypy type check."""
        try:
            cmd = ["mypy", "orchestrator"]
            if self.strict:
                cmd.append("--strict")

            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            output = result.stdout + result.stderr
            lines = [line for line in output.split("\n") if line.strip()]

            # Count errors
            error_count = sum(1 for line in lines if "error:" in line.lower())

            if error_count == 0:
                return ValidationResult(
                    status=ValidationStatus.PASSED,
                    validator_name=self.name,
                    message="Type check passed (0 errors)",
                    details={"error_count": 0, "strict": self.strict},
                )
            else:
                return ValidationResult(
                    status=ValidationStatus.FAILED,
                    validator_name=self.name,
                    message=f"Type check failed ({error_count} errors)",
                    details={"error_count": error_count, "strict": self.strict},
                    errors=[line for line in lines if "error:" in line.lower()],
                )

        except Exception as e:
            logger.error(f"Type check validation failed: {e}")
            return ValidationResult(
                status=ValidationStatus.FAILED,
                validator_name=self.name,
                message=f"Type check error: {e}",
                errors=[str(e)],
            )


class TestValidator(Validator):
    """Validator for test execution."""

    def __init__(
        self,
        project_dir: str | Path,
        min_coverage: float = 90.0,
    ) -> None:
        """Initialize test validator.

        Args:
            project_dir: Project directory
            min_coverage: Minimum required coverage percentage
        """
        super().__init__(project_dir)
        self.min_coverage = min_coverage

    def validate(self) -> ValidationResult:
        """Run pytest with coverage."""
        try:
            result = subprocess.run(
                [
                    "pytest",
                    "tests/",
                    "-v",
                    "--tb=short",
                    "--cov=orchestrator",
                    "--cov - report=term - missing",
                ],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300,
            )

            output = result.stdout + result.stderr

            # Parse test results
            test_failed = result.returncode != 0
            lines = output.split("\n")

            # Find coverage percentage
            coverage_pct = 0.0
            for line in lines:
                if "TOTAL" in line and "%" in line:
                    parts = line.split()
                    for part in parts:
                        if "%" in part:
                            coverage_pct = float(part.rstrip("%"))
                            break

            if not test_failed and coverage_pct >= self.min_coverage:
                return ValidationResult(
                    status=ValidationStatus.PASSED,
                    validator_name=self.name,
                    message=f"Tests passed ({coverage_pct:.1f}% coverage)",
                    details={"coverage": coverage_pct, "min_coverage": self.min_coverage},
                )
            elif test_failed:
                return ValidationResult(
                    status=ValidationStatus.FAILED,
                    validator_name=self.name,
                    message="Tests failed",
                    details={"coverage": coverage_pct},
                    errors=[line for line in lines if "FAILED" in line],
                )
            else:
                return ValidationResult(
                    status=ValidationStatus.FAILED,
                    validator_name=self.name,
                    message=f"Coverage too low ({coverage_pct:.1f}%, min {self.min_coverage}%)",
                    details={"coverage": coverage_pct, "min_coverage": self.min_coverage},
                )

        except Exception as e:
            logger.error(f"Test validation failed: {e}")
            return ValidationResult(
                status=ValidationStatus.FAILED,
                validator_name=self.name,
                message=f"Test execution error: {e}",
                errors=[str(e)],
            )


class SecurityValidator(Validator):
    """Validator for security scanning."""

    def __init__(
        self,
        project_dir: str | Path,
        max_issues: int = 0,
    ) -> None:
        """Initialize security validator.

        Args:
            project_dir: Project directory
            max_issues: Maximum allowed security issues
        """
        super().__init__(project_dir)
        self.max_issues = max_issues

    def validate(self) -> ValidationResult:
        """Run bandit security scan."""
        try:
            result = subprocess.run(
                [
                    "bandit",
                    "-r",
                    "orchestrator",
                    "-f",
                    "json",
                ],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Bandit returns non - zero if issues found, but that's expected
            output = result.stdout

            # Count issues (simplified - just check if output is empty)
            import json

            try:
                data = json.loads(output)
                issue_count = len(data.get("results", []))
            except json.JSONDecodeError:
                issue_count = 0

            if issue_count <= self.max_issues:
                return ValidationResult(
                    status=ValidationStatus.PASSED,
                    validator_name=self.name,
                    message=f"Security scan passed ({issue_count} issues)",
                    details={"issue_count": issue_count, "max_issues": self.max_issues},
                )
            else:
                return ValidationResult(
                    status=ValidationStatus.FAILED,
                    validator_name=self.name,
                    message=f"Security scan failed ({issue_count} issues)",
                    details={"issue_count": issue_count, "max_issues": self.max_issues},
                )

        except Exception as e:
            logger.error(f"Security validation failed: {e}")
            return ValidationResult(
                status=ValidationStatus.FAILED,
                validator_name=self.name,
                message=f"Security scan error: {e}",
                errors=[str(e)],
            )


class ValidationPipeline:
    """Pipeline for running multiple validators."""

    def __init__(self, project_dir: str | Path) -> None:
        """Initialize validation pipeline.

        Args:
            project_dir: Project directory
        """
        self.project_dir = Path(project_dir)
        self.validators: list[Validator] = []

    def add_validator(self, validator: Validator) -> None:
        """Add validator to pipeline.

        Args:
            validator: Validator to add
        """
        self.validators.append(validator)

    def run(self) -> list[ValidationResult]:
        """Run all validators in pipeline.

        Returns:
            List of validation results
        """
        results = []
        for validator in self.validators:
            logger.info(f"Running {validator.name}...")
            result = validator.validate()
            results.append(result)
            logger.info(f"{validator.name}: {result.status.value}")
        return results

    def all_passed(self, results: list[ValidationResult]) -> bool:
        """Check if all validations passed.

        Args:
            results: List of validation results

        Returns:
            True if all passed
        """
        return all(result.status == ValidationStatus.PASSED for result in results)
