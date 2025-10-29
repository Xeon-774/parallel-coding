"""
Base Review Provider - Abstract Interface for AI Document Review

This module provides a provider - agnostic interface for document review
functionality. It enables the orchestrator to delegate review tasks to
different AI providers (Codex, Claude Code, Claude API) seamlessly.

Key Features:
    - Provider - agnostic abstract interface
    - Type - safe request / response models with Pydantic
    - Multi - perspective review support (architecture, security, feasibility)
    - Extensible feedback categorization
    - Comprehensive error handling

Architecture:
    BaseReviewProvider (ABC)
    ├── review_document() - Main review execution
    ├── is_available() - Provider availability check
    └── provider_name - Provider identifier

    Concrete Implementations (separate files):
    ├── CodexReviewProvider
    ├── ClaudeCodeReviewProvider (future)
    └── ClaudeAPIReviewProvider (future)

Security:
    - Input validation via Pydantic
    - Path traversal prevention
    - File size limits
    - Timeout enforcement

Author: Claude (Sonnet 4.5)
Created: 2025 - 10 - 28
Version: 1.0.0
Excellence AI Standard: 100% Applied
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

# =============================================================================
# Constants
# =============================================================================

MAX_DOCUMENT_SIZE_MB: int = 10  # Maximum document size for review
MAX_FEEDBACK_ITEMS: int = 100  # Maximum feedback items per review
DEFAULT_TIMEOUT_SECONDS: int = 300  # 5 minutes


# =============================================================================
# Enums
# =============================================================================


class ReviewType(str, Enum):
    """Type of document being reviewed"""

    DESIGN = "design"
    ROADMAP = "roadmap"
    CODE = "code"
    ARCHITECTURE = "architecture"
    API_SPEC = "api_spec"
    DOCUMENTATION = "documentation"


class ReviewPerspective(str, Enum):
    """Perspective / focus area for review"""

    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    FEASIBILITY = "feasibility"
    PRIORITY = "priority"
    MAINTAINABILITY = "maintainability"
    TESTING = "testing"
    DOCUMENTATION = "documentation"


class FeedbackSeverity(str, Enum):
    """Severity level of review feedback"""

    CRITICAL = "critical"  # Must fix before proceeding
    WARNING = "warning"  # Should fix, but not blocking
    INFO = "info"  # Suggestion for improvement


class ReviewStatus(str, Enum):
    """Status of review execution"""

    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    INVALID_INPUT = "invalid_input"


# =============================================================================
# Request Models
# =============================================================================


class ReviewRequest(BaseModel):
    """
    Request for document review.

    Attributes:
        document_path: Path to document to review
        review_type: Type of review (design, roadmap, code, etc.)
        perspective: Focus area (architecture, security, etc.)
        context: Additional context (project info, standards, etc.)
        timeout_seconds: Maximum execution time

    Example:
        >>> request = ReviewRequest(
        ...     document_path="docs / ROADMAP.md",
        ...     review_type=ReviewType.ROADMAP,
        ...     perspective=ReviewPerspective.FEASIBILITY,
        ...     context={"project": "AI_Investor", "phase": "Week 2"}
        ... )
    """

    document_path: str = Field(
        min_length=1, max_length=500, description="Path to document to review"
    )

    review_type: ReviewType = Field(description="Type of review to perform")

    perspective: ReviewPerspective = Field(description="Review perspective / focus area")

    context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context for review"
    )

    timeout_seconds: int = Field(
        default=DEFAULT_TIMEOUT_SECONDS,
        ge=10,
        le=1800,
        description="Maximum execution time in seconds",
    )

    @field_validator("document_path")
    @classmethod
    def validate_document_path(cls, v: str) -> str:
        """
        Validate document path for security.

        Prevents path traversal attacks and ensures file exists.

        Args:
            v: Document path

        Returns:
            Validated path string

        Raises:
            ValueError: If path is invalid or dangerous
        """
        # Prevent path traversal
        if ".." in v:
            raise ValueError("Path traversal not allowed in document_path")

        # Check file exists
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Document not found: {v}")

        # Check file size
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > MAX_DOCUMENT_SIZE_MB:
            raise ValueError(f"Document too large: {size_mb:.1f}MB (max: {MAX_DOCUMENT_SIZE_MB}MB)")

        return v


# =============================================================================
# Response Models
# =============================================================================


class ReviewFeedback(BaseModel):
    """
    Single feedback item from review.

    Attributes:
        category: Feedback category (architecture, security, etc.)
        severity: Severity level (critical, warning, info)
        line_number: Optional line number in document
        section: Optional section / heading name
        message: Feedback message
        suggestion: Optional improvement suggestion
        reference: Optional reference to standards / docs

    Example:
        >>> feedback = ReviewFeedback(
        ...     category=ReviewPerspective.SECURITY,
        ...     severity=FeedbackSeverity.CRITICAL,
        ...     line_number=42,
        ...     message="API keys exposed in code",
        ...     suggestion="Use environment variables or secrets manager"
        ... )
    """

    category: ReviewPerspective = Field(description="Feedback category")

    severity: FeedbackSeverity = Field(description="Severity level")

    line_number: Optional[int] = Field(default=None, ge=1, description="Line number in document")

    section: Optional[str] = Field(
        default=None, max_length=200, description="Section / heading name"
    )

    message: str = Field(min_length=1, max_length=1000, description="Feedback message")

    suggestion: Optional[str] = Field(
        default=None, max_length=2000, description="Improvement suggestion"
    )

    reference: Optional[str] = Field(
        default=None, max_length=500, description="Reference to standards / docs"
    )


class ReviewResult(BaseModel):
    """
    Result of document review.

    Attributes:
        job_id: Unique job identifier
        document_path: Path to reviewed document
        review_type: Type of review performed
        perspective: Review perspective used
        status: Execution status
        feedbacks: List of feedback items
        overall_score: Overall quality score (0 - 100)
        execution_time_seconds: Total execution time
        provider_name: AI provider used
        metadata: Additional provider - specific metadata

    Example:
        >>> result = ReviewResult(
        ...     job_id="abc123",
        ...     document_path="docs / ROADMAP.md",
        ...     review_type=ReviewType.ROADMAP,
        ...     perspective=ReviewPerspective.FEASIBILITY,
        ...     status=ReviewStatus.SUCCESS,
        ...     feedbacks=[...],
        ...     overall_score=85.0,
        ...     execution_time_seconds=12.5,
        ...     provider_name="codex"
        ... )
    """

    job_id: str = Field(min_length=1, description="Unique job identifier")

    document_path: str = Field(description="Path to reviewed document")

    review_type: ReviewType = Field(description="Type of review performed")

    perspective: ReviewPerspective = Field(description="Review perspective used")

    status: ReviewStatus = Field(description="Execution status")

    feedbacks: List[ReviewFeedback] = Field(
        default_factory=list, description="List of feedback items"
    )

    overall_score: float = Field(ge=0.0, le=100.0, description="Overall quality score (0 - 100)")

    execution_time_seconds: float = Field(ge=0.0, description="Total execution time in seconds")

    provider_name: str = Field(description="AI provider used for review")

    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Provider - specific metadata"
    )

    error_message: Optional[str] = Field(default=None, description="Error message if review failed")

    @field_validator("feedbacks")
    @classmethod
    def validate_feedbacks(cls, v: List[ReviewFeedback]) -> List[ReviewFeedback]:
        """
        Validate feedback items.

        Args:
            v: List of feedback items

        Returns:
            Validated list

        Raises:
            ValueError: If too many feedback items
        """
        if len(v) > MAX_FEEDBACK_ITEMS:
            raise ValueError(f"Too many feedback items: {len(v)} (max: {MAX_FEEDBACK_ITEMS})")
        return v

    @property
    def is_success(self) -> bool:
        """Check if review was successful"""
        return self.status == ReviewStatus.SUCCESS

    @property
    def critical_issues(self) -> List[ReviewFeedback]:
        """Get critical severity feedback items"""
        return [f for f in self.feedbacks if f.severity == FeedbackSeverity.CRITICAL]

    @property
    def warnings(self) -> List[ReviewFeedback]:
        """Get warning severity feedback items"""
        return [f for f in self.feedbacks if f.severity == FeedbackSeverity.WARNING]

    @property
    def info_items(self) -> List[ReviewFeedback]:
        """Get info severity feedback items"""
        return [f for f in self.feedbacks if f.severity == FeedbackSeverity.INFO]


class AggregatedReview(BaseModel):
    """
    Aggregated result from multiple review perspectives.

    Attributes:
        document_path: Path to reviewed document
        review_type: Type of review
        perspectives: List of perspectives reviewed
        results: Individual review results
        overall_score: Weighted average score
        critical_count: Total critical issues
        warning_count: Total warnings
        execution_time_seconds: Total execution time

    Example:
        >>> aggregated = AggregatedReview(
        ...     document_path="docs / DESIGN.md",
        ...     review_type=ReviewType.DESIGN,
        ...     perspectives=[ReviewPerspective.ARCHITECTURE, ReviewPerspective.SECURITY],
        ...     results=[result1, result2],
        ...     overall_score=82.5
        ... )
    """

    document_path: str = Field(description="Path to reviewed document")

    review_type: ReviewType = Field(description="Type of review")

    perspectives: List[ReviewPerspective] = Field(description="List of perspectives reviewed")

    results: List[ReviewResult] = Field(description="Individual review results")

    overall_score: float = Field(ge=0.0, le=100.0, description="Weighted average score")

    critical_count: int = Field(ge=0, description="Total critical issues")

    warning_count: int = Field(ge=0, description="Total warnings")

    execution_time_seconds: float = Field(ge=0.0, description="Total execution time")

    @property
    def all_feedbacks(self) -> List[ReviewFeedback]:
        """Get all feedback items from all results"""
        feedbacks: List[ReviewFeedback] = []
        for result in self.results:
            feedbacks.extend(result.feedbacks)
        return feedbacks


# =============================================================================
# Abstract Base Class
# =============================================================================


class BaseReviewProvider(ABC):
    """
    Abstract base class for AI review providers.

    This class defines the interface that all review providers must implement,
    enabling seamless provider switching and extensibility.

    Concrete implementations:
        - CodexReviewProvider: OpenAI Codex CLI
        - ClaudeCodeReviewProvider: Claude Code (future)
        - ClaudeAPIReviewProvider: Claude API (future)

    Usage:
        >>> class MyReviewProvider(BaseReviewProvider):
        ...     async def review_document(self, request: ReviewRequest) -> ReviewResult:
        ...         # Implementation here
        ...         pass
        ...
        ...     def is_available(self) -> bool:
        ...         return True
        ...
        ...     @property
        ...     def provider_name(self) -> str:
        ...         return "my_provider"
    """

    @abstractmethod
    async def review_document(self, request: ReviewRequest) -> ReviewResult:
        """
        Execute document review.

        Args:
            request: Review request with document path and parameters

        Returns:
            ReviewResult with feedback and scores

        Raises:
            ValueError: If request is invalid
            TimeoutError: If review exceeds timeout
            RuntimeError: If provider execution fails

        Example:
            >>> request = ReviewRequest(
            ...     document_path="docs / ROADMAP.md",
            ...     review_type=ReviewType.ROADMAP,
            ...     perspective=ReviewPerspective.FEASIBILITY
            ... )
            >>> result = await provider.review_document(request)
        """

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is available.

        Returns:
            True if provider is installed and working, False otherwise

        Example:
            >>> if provider.is_available():
            ...     result = await provider.review_document(request)
            ... else:
            ...     print("Provider not available")
        """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Get provider identifier.

        Returns:
            Provider name string (e.g., "codex", "claude_code")

        Example:
            >>> provider.provider_name
            'codex'
        """


# =============================================================================
# Error Classes
# =============================================================================


class ReviewProviderError(Exception):
    """Base exception for review provider errors"""


class ReviewTimeoutError(ReviewProviderError):
    """Raised when review execution times out"""


class ReviewExecutionError(ReviewProviderError):
    """Raised when review execution fails"""


class ProviderNotAvailableError(ReviewProviderError):
    """Raised when provider is not available"""


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    # Example: Creating a review request
    request = ReviewRequest(
        document_path="docs / ROADMAP.md",
        review_type=ReviewType.ROADMAP,
        perspective=ReviewPerspective.FEASIBILITY,
        context={"project": "AI_Investor", "phase": "Week 2"},
    )

    # Example: Creating feedback
    feedback = ReviewFeedback(
        category=ReviewPerspective.SECURITY,
        severity=FeedbackSeverity.CRITICAL,
        line_number=42,
        message="API keys should not be hardcoded",
        suggestion="Use environment variables or secrets manager",
        reference="excellence_ai_standard: Security best practices",
    )

    print(f"Request: {request.document_path}")
    print(f"Feedback: {feedback.severity} - {feedback.message}")
