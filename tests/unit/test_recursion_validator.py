"""Unit tests for recursion validator module.

Tests recursion depth validation, timeout calculation, and circular reference detection.
"""

import pytest

from orchestrator.recursive.recursion_validator import (
    RecursionValidator,
    RecursionValidationResult,
)


class TestRecursionValidationResult:
    """Test RecursionValidationResult model."""

    def test_create_valid_result(self):
        """Test creating valid result."""
        result = RecursionValidationResult(
            is_valid=True,
            adjusted_timeout=450,
            max_workers=3
        )
        assert result.is_valid is True
        assert result.adjusted_timeout == 450
        assert result.max_workers == 3
        assert result.error_message is None

    def test_create_invalid_result(self):
        """Test creating invalid result with error message."""
        result = RecursionValidationResult(
            is_valid=False,
            error_message="Test error"
        )
        assert result.is_valid is False
        assert result.error_message == "Test error"
        assert result.adjusted_timeout is None
        assert result.max_workers is None


class TestRecursionValidator:
    """Test RecursionValidator functionality."""

    def test_validate_depth_success(self):
        """Test successful depth validation."""
        result = RecursionValidator.validate_depth(
            current_depth=0,
            max_depth=3,
            workers_by_depth={1: 5, 2: 3, 3: 1}
        )

        assert result.is_valid is True
        assert result.error_message is None
        assert result.max_workers == 5  # For depth 1
        assert result.adjusted_timeout > 0

    def test_validate_depth_at_max_depth(self):
        """Test validation fails when at max depth."""
        result = RecursionValidator.validate_depth(
            current_depth=3,
            max_depth=3,
            workers_by_depth={1: 5, 2: 3, 3: 1}
        )

        assert result.is_valid is False
        assert "Max recursion depth" in result.error_message
        assert result.max_workers is None

    def test_validate_depth_negative_current_depth(self):
        """Test validation fails with negative current depth."""
        result = RecursionValidator.validate_depth(
            current_depth=-1,
            max_depth=3,
            workers_by_depth={1: 5}
        )

        assert result.is_valid is False
        assert "Current depth cannot be negative" in result.error_message

    def test_validate_depth_negative_max_depth(self):
        """Test validation fails with negative max depth."""
        result = RecursionValidator.validate_depth(
            current_depth=0,
            max_depth=-1,
            workers_by_depth={1: 5}
        )

        assert result.is_valid is False
        assert "Max depth cannot be negative" in result.error_message

    def test_validate_depth_timeout_calculation(self):
        """Test timeout grows exponentially with depth."""
        result_depth_0 = RecursionValidator.validate_depth(
            current_depth=0,
            max_depth=5,
            workers_by_depth={1: 5, 2: 3}
        )

        result_depth_1 = RecursionValidator.validate_depth(
            current_depth=1,
            max_depth=5,
            workers_by_depth={1: 5, 2: 3}
        )

        result_depth_2 = RecursionValidator.validate_depth(
            current_depth=2,
            max_depth=5,
            workers_by_depth={1: 5, 2: 3, 3: 2}
        )

        # Timeout should grow exponentially: int(300 * 1.5^depth)
        assert result_depth_0.adjusted_timeout == int(300 * (1.5 ** 1))  # 450
        assert result_depth_1.adjusted_timeout == int(300 * (1.5 ** 2))  # 675
        assert result_depth_2.adjusted_timeout == int(300 * (1.5 ** 3))  # 1012

    def test_validate_depth_default_workers(self):
        """Test default workers when depth not in workers_by_depth."""
        result = RecursionValidator.validate_depth(
            current_depth=0,
            max_depth=5,
            workers_by_depth={2: 5, 3: 3}  # No entry for depth 1
        )

        assert result.is_valid is True
        assert result.max_workers == 1  # Default value

    def test_validate_depth_edge_case_depth_0(self):
        """Test validation at depth 0 (root level)."""
        result = RecursionValidator.validate_depth(
            current_depth=0,
            max_depth=0,
            workers_by_depth={}
        )

        assert result.is_valid is False
        assert "Max recursion depth" in result.error_message

    def test_validate_depth_large_depth(self):
        """Test validation with large depth values."""
        result = RecursionValidator.validate_depth(
            current_depth=8,
            max_depth=10,
            workers_by_depth={9: 1}
        )

        assert result.is_valid is True
        assert result.max_workers == 1
        # Timeout should be very large due to exponential growth
        assert result.adjusted_timeout > 10000


class TestCircularReferenceDetection:
    """Test circular reference detection."""

    def test_detect_circular_reference_found(self):
        """Test circular reference is detected."""
        parent_ids = ["job-a", "job-b", "job-c"]
        current_id = "job-b"  # Already in parents

        result = RecursionValidator.detect_circular_reference(parent_ids, current_id)

        assert result is True

    def test_detect_circular_reference_not_found(self):
        """Test no circular reference when ID is unique."""
        parent_ids = ["job-a", "job-b", "job-c"]
        current_id = "job-d"  # Not in parents

        result = RecursionValidator.detect_circular_reference(parent_ids, current_id)

        assert result is False

    def test_detect_circular_reference_empty_parents(self):
        """Test no circular reference with empty parent list."""
        parent_ids = []
        current_id = "job-a"

        result = RecursionValidator.detect_circular_reference(parent_ids, current_id)

        assert result is False

    def test_detect_circular_reference_self_reference(self):
        """Test circular reference with same ID."""
        parent_ids = ["job-a"]
        current_id = "job-a"

        result = RecursionValidator.detect_circular_reference(parent_ids, current_id)

        assert result is True

    def test_detect_circular_reference_long_chain(self):
        """Test circular reference in long parent chain."""
        parent_ids = ["job-1", "job-2", "job-3", "job-4", "job-5", "job-6", "job-7"]
        current_id = "job-4"  # In the middle of chain

        result = RecursionValidator.detect_circular_reference(parent_ids, current_id)

        assert result is True


class TestRecursionValidatorConstants:
    """Test RecursionValidator constants."""

    def test_base_timeout_constant(self):
        """Test base timeout constant."""
        assert RecursionValidator._BASE_TIMEOUT == 300

    def test_timeout_growth_constant(self):
        """Test timeout growth constant."""
        assert RecursionValidator._TIMEOUT_GROWTH == 1.5
