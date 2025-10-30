"""Configuration validation for cross-project compatibility.

This module provides validation logic to ensure configuration values are
correct, paths exist, and required dependencies are available. It provides
clear, actionable error messages to guide users in fixing configuration issues.

Part of Phase 1: Cross-Project Compatibility Initiative
See: ROADMAP_CROSS_PROJECT_COMPATIBILITY.md, DEVELOPMENT_POLICY.md
"""

from pathlib import Path
from typing import Any, Optional

from orchestrator.config.defaults import (
    DOCS_CONFIGURATION,
    DOCS_INSTALLATION,
    DOCS_TROUBLESHOOTING,
    INSTALLATION_URLS,
)
import logging

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or incomplete."""

    pass


class ValidationResult:
    """Result of a configuration validation check."""

    def __init__(self, valid: bool, message: str = "", fix_suggestions: list[str] = None):
        """Initialize validation result.

        Args:
            valid: Whether validation passed
            message: Description of validation result
            fix_suggestions: List of suggestions to fix the issue
        """
        self.valid = valid
        self.message = message
        self.fix_suggestions = fix_suggestions or []

    def __bool__(self) -> bool:
        """Allow using ValidationResult in boolean context."""
        return self.valid

    def __str__(self) -> str:
        """Get string representation of validation result."""
        if self.valid:
            return f"✓ {self.message}"
        else:
            result = f"✗ {self.message}"
            if self.fix_suggestions:
                result += "\n\n" + "Suggestions to fix:\n"
                for i, suggestion in enumerate(self.fix_suggestions, 1):
                    result += f"  {i}. {suggestion}\n"
            return result


class ConfigValidator:
    """Validates configuration values and provides actionable error messages."""

    def __init__(self, strict: bool = False):
        """Initialize configuration validator.

        Args:
            strict: If True, treat warnings as errors
        """
        self.strict = strict
        self.errors: list[ValidationResult] = []
        self.warnings: list[ValidationResult] = []

    def validate_path_exists(
        self, path: Optional[Path], name: str, required: bool = True, create: bool = False
    ) -> ValidationResult:
        """Validate that a path exists.

        Args:
            path: Path to validate
            name: Human-readable name for error messages
            required: If True, path must exist
            create: If True, create directory if it doesn't exist

        Returns:
            ValidationResult indicating success or failure
        """
        if path is None:
            if required:
                return ValidationResult(
                    False,
                    f"{name} is not configured",
                    [
                        f"Set environment variable for {name}",
                        f"Check configuration file",
                        f"See: {DOCS_CONFIGURATION}",
                    ],
                )
            return ValidationResult(True, f"{name} not configured (optional)")

        if not path.exists():
            if create:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created directory: {path}")
                    return ValidationResult(True, f"{name} created at {path}")
                except Exception as e:
                    return ValidationResult(
                        False,
                        f"{name} could not be created: {e}",
                        [
                            f"Ensure parent directory exists and is writable",
                            f"Check permissions for: {path.parent}",
                        ],
                    )
            elif required:
                return ValidationResult(
                    False,
                    f"{name} does not exist: {path}",
                    [
                        f"Create directory: mkdir -p {path}",
                        f"Check path is correct in configuration",
                        f"See: {DOCS_TROUBLESHOOTING}",
                    ],
                )
            return ValidationResult(True, f"{name} not found (optional): {path}")

        return ValidationResult(True, f"{name} exists at {path}")

    def validate_file_exists(
        self, path: Optional[Path], name: str, required: bool = True
    ) -> ValidationResult:
        """Validate that a file exists.

        Args:
            path: Path to validate
            name: Human-readable name for error messages
            required: If True, file must exist

        Returns:
            ValidationResult indicating success or failure
        """
        if path is None:
            if required:
                return ValidationResult(
                    False,
                    f"{name} is not configured",
                    [
                        f"Set environment variable for {name}",
                        f"Run auto-detection",
                        f"See: {DOCS_CONFIGURATION}",
                    ],
                )
            return ValidationResult(True, f"{name} not configured (optional)")

        if not path.exists():
            if required:
                return ValidationResult(
                    False,
                    f"{name} not found: {path}",
                    [
                        f"Install {name}",
                        f"Check path is correct",
                        f"See: {DOCS_INSTALLATION}",
                    ],
                )
            return ValidationResult(True, f"{name} not found (optional): {path}")

        if not path.is_file():
            return ValidationResult(
                False,
                f"{name} is not a file: {path}",
                [f"Ensure {path} is a valid file", f"Check path configuration"],
            )

        return ValidationResult(True, f"{name} found at {path}")

    def validate_executable(
        self, path: Optional[Path], name: str, required: bool = True
    ) -> ValidationResult:
        """Validate that a binary is executable.

        Args:
            path: Path to binary
            name: Human-readable name for error messages
            required: If True, binary must exist and be executable

        Returns:
            ValidationResult indicating success or failure
        """
        # First check if file exists
        file_result = self.validate_file_exists(path, name, required)
        if not file_result.valid:
            # Add installation suggestion
            binary_key = name.lower().replace(" ", "").replace("cli", "")
            if binary_key in INSTALLATION_URLS:
                file_result.fix_suggestions.insert(
                    0, f"Install from: {INSTALLATION_URLS[binary_key]}"
                )
            return file_result

        # Check if executable (Unix-like systems)
        import os
        import platform

        if platform.system() != "Windows" and path is not None:
            if not os.access(path, os.X_OK):
                return ValidationResult(
                    False,
                    f"{name} is not executable: {path}",
                    [
                        f"Make executable: chmod +x {path}",
                        f"Check file permissions",
                    ],
                )

        return ValidationResult(True, f"{name} is executable at {path}")

    def validate_writable(self, path: Path, name: str) -> ValidationResult:
        """Validate that a path is writable.

        Args:
            path: Path to validate
            name: Human-readable name for error messages

        Returns:
            ValidationResult indicating success or failure
        """
        if not path.exists():
            # Check parent directory
            parent = path.parent
            if not parent.exists():
                return ValidationResult(
                    False,
                    f"{name} parent directory does not exist: {parent}",
                    [f"Create parent directory: mkdir -p {parent}"],
                )
            path = parent

        import os

        if not os.access(path, os.W_OK):
            return ValidationResult(
                False,
                f"{name} is not writable: {path}",
                [
                    f"Check permissions: ls -ld {path}",
                    f"Change permissions: chmod u+w {path}",
                    f"Ensure you have write access",
                ],
            )

        return ValidationResult(True, f"{name} is writable")

    def validate_integer_range(
        self, value: Any, name: str, min_val: Optional[int] = None, max_val: Optional[int] = None
    ) -> ValidationResult:
        """Validate that a value is an integer within a range.

        Args:
            value: Value to validate
            name: Human-readable name for error messages
            min_val: Minimum allowed value (inclusive)
            max_val: Maximum allowed value (inclusive)

        Returns:
            ValidationResult indicating success or failure
        """
        try:
            int_value = int(value)
        except (TypeError, ValueError):
            return ValidationResult(
                False,
                f"{name} must be an integer, got: {value}",
                [f"Set {name} to a valid integer value"],
            )

        if min_val is not None and int_value < min_val:
            return ValidationResult(
                False,
                f"{name} must be >= {min_val}, got: {int_value}",
                [f"Set {name} to at least {min_val}"],
            )

        if max_val is not None and int_value > max_val:
            return ValidationResult(
                False,
                f"{name} must be <= {max_val}, got: {int_value}",
                [f"Set {name} to at most {max_val}"],
            )

        return ValidationResult(True, f"{name} is valid: {int_value}")

    def validate_boolean(self, value: Any, name: str) -> ValidationResult:
        """Validate that a value is a boolean.

        Args:
            value: Value to validate
            name: Human-readable name for error messages

        Returns:
            ValidationResult indicating success or failure
        """
        if isinstance(value, bool):
            return ValidationResult(True, f"{name} is valid: {value}")

        if isinstance(value, str):
            if value.lower() in ("true", "yes", "1", "on"):
                return ValidationResult(True, f"{name} is valid: True")
            if value.lower() in ("false", "no", "0", "off"):
                return ValidationResult(True, f"{name} is valid: False")

        return ValidationResult(
            False,
            f"{name} must be a boolean, got: {value}",
            [f"Set {name} to 'true' or 'false'"],
        )

    def add_error(self, result: ValidationResult) -> None:
        """Add a validation error.

        Args:
            result: Validation result to add as error
        """
        self.errors.append(result)
        logger.error(result.message)

    def add_warning(self, result: ValidationResult) -> None:
        """Add a validation warning.

        Args:
            result: Validation result to add as warning
        """
        self.warnings.append(result)
        logger.warning(result.message)

    def validate_result(self, result: ValidationResult) -> None:
        """Process validation result, adding to errors or warnings.

        Args:
            result: Validation result to process
        """
        if not result.valid:
            if self.strict:
                self.add_error(result)
            else:
                self.add_warning(result)

    def raise_if_invalid(self) -> None:
        """Raise ConfigurationError if there are validation errors.

        Raises:
            ConfigurationError: If validation errors exist
        """
        if self.errors:
            error_messages = [str(error) for error in self.errors]
            raise ConfigurationError(
                "Configuration validation failed:\n\n"
                + "\n\n".join(error_messages)
                + f"\n\nFor help, see: {DOCS_TROUBLESHOOTING}"
            )

    def get_summary(self) -> str:
        """Get summary of validation results.

        Returns:
            String summary of errors and warnings
        """
        lines = []

        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for error in self.errors:
                lines.append(f"  {error}")

        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  {warning}")

        if not self.errors and not self.warnings:
            lines.append("✓ All validation checks passed")

        return "\n".join(lines)
