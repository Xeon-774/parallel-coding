"""Recursion depth validator utilities.

Provides validation routines to ensure recursive orchestration is safe:
- Depth enforcement with resource calculation
- Circular reference detection
- Timeout adjustment by depth

All functions are small, typed, and documented with examples.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class RecursionValidationResult(BaseModel):
    """Result of recursion validation.

    Attributes:
        is_valid: Whether recursion is allowed at the next level.
        error_message: Optional reason when validation fails.
        adjusted_timeout: Timeout in seconds suitable for the next level.
        max_workers: Maximum workers allowed at the next level.

    Examples:
        >>> RecursionValidationResult(is_valid=True, adjusted_timeout=450, max_workers=3)
        RecursionValidationResult(is_valid=True, error_message=None, adjusted_timeout=450, max_workers=3)
    """

    is_valid: bool
    error_message: Optional[str] = None
    adjusted_timeout: Optional[int] = None
    max_workers: Optional[int] = None


class RecursionValidator:
    """Validates recursion depth and calculates resource limits.

    The validator ensures the next recursion step is permitted and provides
    derived resource values based on depth.
    """

    _BASE_TIMEOUT: int = 300  # 5 minutes base
    _TIMEOUT_GROWTH: float = 1.5

    @staticmethod
    def validate_depth(
        current_depth: int, max_depth: int, workers_by_depth: Dict[int, int]
    ) -> RecursionValidationResult:
        """Validate if recursion is allowed at current depth.

        Args:
            current_depth: Current recursion depth (0-based).
            max_depth: Maximum allowed depth (inclusive bound for last level).
            workers_by_depth: Worker limits per depth level.

        Returns:
            Validation result with resource limits for the next level.

        Examples:
            >>> RecursionValidator.validate_depth(0, 3, {1: 5, 2: 3, 3: 1}).is_valid
            True

        Notes:
            A call from depth D creates the next level at D+1. This function
            validates whether that step is allowed and returns limits for D+1.
        """
        if current_depth < 0:
            return RecursionValidationResult(
                is_valid=False, error_message="Current depth cannot be negative"
            )

        if max_depth < 0:
            return RecursionValidationResult(
                is_valid=False, error_message="Max depth cannot be negative"
            )

        # If the next level would exceed max, disallow.
        if current_depth >= max_depth:
            return RecursionValidationResult(
                is_valid=False,
                error_message=f"Max recursion depth ({max_depth}) reached",
            )

        # Calculate resource limits for next depth level.
        next_depth = current_depth + 1
        max_workers = workers_by_depth.get(next_depth, 1)

        # Exponential backoff for timeout by depth.
        adjusted_timeout = int(
            RecursionValidator._BASE_TIMEOUT
            * (RecursionValidator._TIMEOUT_GROWTH ** next_depth)
        )

        return RecursionValidationResult(
            is_valid=True,
            error_message=None,
            adjusted_timeout=adjusted_timeout,
            max_workers=max_workers,
        )

    @staticmethod
    def detect_circular_reference(
        parent_job_ids: List[str], current_job_id: str
    ) -> bool:
        """Detect if the current job creates a circular reference.

        Args:
            parent_job_ids: Ordered list of ancestor job IDs.
            current_job_id: The job ID being scheduled.

        Returns:
            True if a circular reference is detected, otherwise False.

        Examples:
            >>> RecursionValidator.detect_circular_reference(["a", "b"], "b")
            True
            >>> RecursionValidator.detect_circular_reference(["a", "b"], "c")
            False
        """
        return current_job_id in parent_job_ids

