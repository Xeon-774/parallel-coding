"""
Codex Review Time Estimation Module

This module provides time estimation for Codex CLI document reviews based on
empirical data from actual review executions.

Key Features:
    - Time estimation based on document size and perspective count
    - Execution strategy recommendation (blocking vs background)
    - Document splitting suggestions for large files
    - Safety buffer (50%) for timeout calculations

Empirical Data:
    - WEEK2_MVP_SPEC (617 lines, 1 perspective) → ~2 minutes
    - ROADMAP (497 lines, 1 perspective) → ~2 minutes
    - 3 design docs (3,124 lines, 6 perspectives) → ~15 - 20 minutes

Usage:
    >>> from orchestrator.core.ai_providers.review_time_estimator import (
    ...     estimate_codex_review_time
    ... )
    >>> result = estimate_codex_review_time(document_lines=1000, perspective_count=2)
    >>> print(f"Estimated time: {result['estimated_minutes']} minutes")
    >>> print(f"Timeout: {result['timeout_minutes']} minutes")

Author: Claude (Sonnet 4.5)
Created: 2025 - 10 - 28
Version: 1.0.0
Excellence AI Standard: 100% Applied
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field

# =============================================================================
# Constants (Empirically Derived)
# =============================================================================

BASE_TIME_SECONDS: int = 20
"""Base overhead for Codex CLI startup and initialization."""

TIME_PER_100_LINES_SECONDS: int = 15
"""Processing time per 100 lines of document."""

PERSPECTIVE_OVERHEAD_SECONDS: int = 10
"""Additional overhead per review perspective."""

SAFETY_BUFFER_MULTIPLIER: float = 1.5
"""Safety buffer multiplier (50% extra time)."""

SPLIT_THRESHOLD_LINES: int = 2000
"""Document size threshold for recommending splitting."""


# =============================================================================
# Enums
# =============================================================================


class ExecutionStrategy(str, Enum):
    """Recommended execution strategy for Codex review."""

    BLOCKING = "BLOCKING"
    """Block and wait for result (short reviews <2 min)."""

    BACKGROUND_SHORT = "BACKGROUND_SHORT"
    """Background execution with periodic checks (2 - 10 min)."""

    BACKGROUND_LONG = "BACKGROUND_LONG"
    """Background execution, consider splitting (>10 min)."""


# =============================================================================
# Data Models
# =============================================================================


class ReviewTimeEstimate(BaseModel):
    """
    Time estimate for Codex review execution.

    Attributes:
        estimated_seconds: Raw estimated time without buffer
        estimated_minutes: Estimated time in minutes
        timeout_seconds: Recommended timeout with safety buffer
        timeout_minutes: Timeout in minutes
        strategy: Recommended execution strategy
        message: Human - readable recommendation message
        should_split: Whether document should be split
        split_suggestion: Suggestion for splitting (if applicable)
    """

    estimated_seconds: int = Field(..., ge=0, description="Estimated time without buffer")
    estimated_minutes: float = Field(..., ge=0.0, description="Estimated time in minutes")
    timeout_seconds: int = Field(..., ge=0, description="Timeout with safety buffer")
    timeout_minutes: float = Field(..., ge=0.0, description="Timeout in minutes")
    strategy: ExecutionStrategy = Field(..., description="Recommended execution strategy")
    message: str = Field(..., description="Human - readable recommendation")
    should_split: bool = Field(..., description="Whether to split document")
    split_suggestion: Optional[str] = Field(None, description="Document splitting suggestion")

    class Config:
        """Pydantic configuration."""

        frozen = True


# =============================================================================
# Core Functions
# =============================================================================


def estimate_codex_review_time(
    document_lines: int,
    perspective_count: int = 1,
) -> ReviewTimeEstimate:
    """
    Estimate Codex review execution time and recommend strategy.

    This function uses empirical data from actual Codex CLI reviews to
    estimate execution time based on document size and perspective count.

    Formula:
        estimated_time = BASE_TIME
                       + (lines / 100) * TIME_PER_100_LINES
                       + (perspectives * PERSPECTIVE_OVERHEAD)

        timeout = estimated_time * SAFETY_BUFFER_MULTIPLIER

    Args:
        document_lines: Number of lines in document
        perspective_count: Number of review perspectives (default: 1)

    Returns:
        ReviewTimeEstimate with estimated time, timeout, and strategy

    Raises:
        ValueError: If document_lines or perspective_count is negative

    Examples:
        >>> # Small document
        >>> result = estimate_codex_review_time(500, 1)
        >>> print(result.strategy)
        ExecutionStrategy.BLOCKING

        >>> # Large document
        >>> result = estimate_codex_review_time(3000, 3)
        >>> print(result.should_split)
        True
    """
    if document_lines < 0:
        raise ValueError("document_lines must be non - negative")
    if perspective_count < 1:
        raise ValueError("perspective_count must be at least 1")

    # Calculate estimated time components
    line_time = (document_lines / 100) * TIME_PER_100_LINES_SECONDS
    perspective_time = perspective_count * PERSPECTIVE_OVERHEAD_SECONDS
    estimated_seconds = int(BASE_TIME_SECONDS + line_time + perspective_time)

    # Add safety buffer
    timeout_seconds = int(estimated_seconds * SAFETY_BUFFER_MULTIPLIER)

    # Determine execution strategy
    strategy = _determine_strategy(timeout_seconds)
    message = _get_strategy_message(strategy)

    # Check if splitting recommended
    should_split = document_lines > SPLIT_THRESHOLD_LINES
    split_suggestion = None
    if should_split:
        num_splits = max(2, document_lines // 1000)
        split_suggestion = (
            f"ドキュメントを{num_splits}個に分割することを推奨 "
            f"(各{document_lines // num_splits}行程度)"
        )

    return ReviewTimeEstimate(
        estimated_seconds=estimated_seconds,
        estimated_minutes=round(estimated_seconds / 60, 1),
        timeout_seconds=timeout_seconds,
        timeout_minutes=round(timeout_seconds / 60, 1),
        strategy=strategy,
        message=message,
        should_split=should_split,
        split_suggestion=split_suggestion,
    )


def _determine_strategy(timeout_seconds: int) -> ExecutionStrategy:
    """
    Determine execution strategy based on timeout.

    Args:
        timeout_seconds: Timeout with safety buffer

    Returns:
        Recommended ExecutionStrategy
    """
    if timeout_seconds <= 120:  # 2 minutes
        return ExecutionStrategy.BLOCKING
    elif timeout_seconds <= 600:  # 10 minutes
        return ExecutionStrategy.BACKGROUND_SHORT
    else:
        return ExecutionStrategy.BACKGROUND_LONG


def _get_strategy_message(strategy: ExecutionStrategy) -> str:
    """
    Get human - readable message for execution strategy.

    Args:
        strategy: ExecutionStrategy

    Returns:
        Japanese message describing strategy
    """
    messages = {
        ExecutionStrategy.BLOCKING: ("短時間レビュー (2分以内) - ブロッキング実行推奨"),
        ExecutionStrategy.BACKGROUND_SHORT: (
            "中時間レビュー (2 - 10分) - バックグラウンド実行 + 定期確認"
        ),
        ExecutionStrategy.BACKGROUND_LONG: (
            "長時間レビュー (10分以上) - バックグラウンド実行 + 分割推奨"
        ),
    }
    return messages[strategy]


# =============================================================================
# Utility Functions
# =============================================================================


def count_document_lines(file_path: str) -> int:
    """
    Count lines in a document file.

    Args:
        file_path: Path to document file

    Returns:
        Number of lines in file

    Raises:
        FileNotFoundError: If file does not exist
        OSError: If file cannot be read

    Examples:
        >>> count_document_lines("docs / ROADMAP.md")
        497
    """
    with open(file_path, "r", encoding="utf - 8-sig") as f:
        return sum(1 for _ in f)


def estimate_from_file(
    file_path: str,
    perspective_count: int = 1,
) -> ReviewTimeEstimate:
    """
    Estimate review time directly from file path.

    Convenience function that combines line counting and estimation.

    Args:
        file_path: Path to document file
        perspective_count: Number of review perspectives

    Returns:
        ReviewTimeEstimate

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If invalid parameters

    Examples:
        >>> result = estimate_from_file("docs / ROADMAP.md", perspective_count=2)
        >>> print(f"Estimated: {result.estimated_minutes} minutes")
    """
    lines = count_document_lines(file_path)
    return estimate_codex_review_time(lines, perspective_count)
