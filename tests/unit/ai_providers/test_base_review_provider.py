"""
Unit tests for BaseReviewProvider and related models.

Tests cover:
- ReviewRequest validation
- ReviewFeedback creation
- ReviewResult properties
- AggregatedReview metrics
- Error classes

Coverage target: ≥90%
Excellence AI Standard: 100% Applied
"""

from pathlib import Path

import pytest

from orchestrator.core.ai_providers.base_review_provider import (
    MAX_DOCUMENT_SIZE_MB,
    MAX_FEEDBACK_ITEMS,
    AggregatedReview,
    BaseReviewProvider,
    FeedbackSeverity,
    ProviderNotAvailableError,
    ReviewExecutionError,
    ReviewFeedback,
    ReviewPerspective,
    ReviewProviderError,
    ReviewRequest,
    ReviewResult,
    ReviewStatus,
    ReviewTimeoutError,
    ReviewType,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_document(tmp_path: Path) -> Path:
    """Create a temporary test document"""
    doc = tmp_path / "test_doc.md"
    doc.write_text("# Test Document\n\nThis is a test document.", encoding="utf - 8")
    return doc


@pytest.fixture
def sample_feedback() -> ReviewFeedback:
    """Create sample feedback item"""
    return ReviewFeedback(
        category=ReviewPerspective.SECURITY,
        severity=FeedbackSeverity.CRITICAL,
        line_number=42,
        message="API keys should not be hardcoded",
        suggestion="Use environment variables",
    )


@pytest.fixture
def sample_result() -> ReviewResult:
    """Create sample review result"""
    return ReviewResult(
        job_id="test - job - 123",
        document_path="docs / test.md",
        review_type=ReviewType.DESIGN,
        perspective=ReviewPerspective.ARCHITECTURE,
        status=ReviewStatus.SUCCESS,
        feedbacks=[
            ReviewFeedback(
                category=ReviewPerspective.ARCHITECTURE,
                severity=FeedbackSeverity.WARNING,
                message="Consider using dependency injection",
            )
        ],
        overall_score=85.0,
        execution_time_seconds=12.5,
        provider_name="test_provider",
    )


# =============================================================================
# ReviewRequest Tests
# =============================================================================


def test_review_request_valid(temp_document: Path) -> None:
    """Test valid review request creation"""
    request = ReviewRequest(
        document_path=str(temp_document),
        review_type=ReviewType.DESIGN,
        perspective=ReviewPerspective.ARCHITECTURE,
    )

    assert request.document_path == str(temp_document)
    assert request.review_type == ReviewType.DESIGN
    assert request.perspective == ReviewPerspective.ARCHITECTURE
    assert request.timeout_seconds == 300  # Default
    assert isinstance(request.context, dict)


def test_review_request_with_context(temp_document: Path) -> None:
    """Test review request with context"""
    request = ReviewRequest(
        document_path=str(temp_document),
        review_type=ReviewType.ROADMAP,
        perspective=ReviewPerspective.FEASIBILITY,
        context={"project": "AI_Investor", "phase": "Week 2"},
        timeout_seconds=600,
    )

    assert request.context["project"] == "AI_Investor"
    assert request.context["phase"] == "Week 2"
    assert request.timeout_seconds == 600


def test_review_request_path_traversal_rejected() -> None:
    """Test path traversal is rejected"""
    with pytest.raises(ValueError, match="Path traversal not allowed"):
        ReviewRequest(
            document_path="../../../etc / passwd",
            review_type=ReviewType.CODE,
            perspective=ReviewPerspective.SECURITY,
        )


def test_review_request_nonexistent_file_rejected() -> None:
    """Test nonexistent file is rejected"""
    with pytest.raises(ValueError, match="Document not found"):
        ReviewRequest(
            document_path="nonexistent_file.md",
            review_type=ReviewType.DESIGN,
            perspective=ReviewPerspective.ARCHITECTURE,
        )


def test_review_request_large_file_rejected(tmp_path: Path) -> None:
    """Test file size limit enforcement"""
    large_doc = tmp_path / "large.md"
    # Create file larger than MAX_DOCUMENT_SIZE_MB
    large_content = "x" * ((MAX_DOCUMENT_SIZE_MB + 1) * 1024 * 1024)
    large_doc.write_text(large_content, encoding="utf - 8")

    with pytest.raises(ValueError, match="Document too large"):
        ReviewRequest(
            document_path=str(large_doc),
            review_type=ReviewType.CODE,
            perspective=ReviewPerspective.PERFORMANCE,
        )


def test_review_request_timeout_bounds() -> None:
    """Test timeout validation bounds"""
    with pytest.raises(ValueError):
        ReviewRequest(
            document_path="test.md",
            review_type=ReviewType.DESIGN,
            perspective=ReviewPerspective.ARCHITECTURE,
            timeout_seconds=5,  # Below minimum (10)
        )

    with pytest.raises(ValueError):
        ReviewRequest(
            document_path="test.md",
            review_type=ReviewType.DESIGN,
            perspective=ReviewPerspective.ARCHITECTURE,
            timeout_seconds=2000,  # Above maximum (1800)
        )


# =============================================================================
# ReviewFeedback Tests
# =============================================================================


def test_review_feedback_creation(sample_feedback: ReviewFeedback) -> None:
    """Test feedback creation"""
    assert sample_feedback.category == ReviewPerspective.SECURITY
    assert sample_feedback.severity == FeedbackSeverity.CRITICAL
    assert sample_feedback.line_number == 42
    assert sample_feedback.message == "API keys should not be hardcoded"
    assert sample_feedback.suggestion == "Use environment variables"


def test_review_feedback_optional_fields() -> None:
    """Test feedback with optional fields"""
    feedback = ReviewFeedback(
        category=ReviewPerspective.ARCHITECTURE,
        severity=FeedbackSeverity.INFO,
        message="Consider refactoring",
    )

    assert feedback.line_number is None
    assert feedback.section is None
    assert feedback.suggestion is None
    assert feedback.reference is None


def test_review_feedback_with_section() -> None:
    """Test feedback with section"""
    feedback = ReviewFeedback(
        category=ReviewPerspective.DOCUMENTATION,
        severity=FeedbackSeverity.WARNING,
        section="Installation Guide",
        message="Missing step 3",
        suggestion="Add npm install instructions",
    )

    assert feedback.section == "Installation Guide"


# =============================================================================
# ReviewResult Tests
# =============================================================================


def test_review_result_creation(sample_result: ReviewResult) -> None:
    """Test result creation"""
    assert sample_result.job_id == "test - job - 123"
    assert sample_result.status == ReviewStatus.SUCCESS
    assert sample_result.overall_score == 85.0
    assert len(sample_result.feedbacks) == 1


def test_review_result_is_success(sample_result: ReviewResult) -> None:
    """Test success property"""
    assert sample_result.is_success is True

    failed_result = ReviewResult(
        job_id="failed - job",
        document_path="test.md",
        review_type=ReviewType.CODE,
        perspective=ReviewPerspective.SECURITY,
        status=ReviewStatus.FAILED,
        feedbacks=[],
        overall_score=0.0,
        execution_time_seconds=5.0,
        provider_name="test",
    )
    assert failed_result.is_success is False


def test_review_result_critical_issues() -> None:
    """Test critical issues filtering"""
    result = ReviewResult(
        job_id="test",
        document_path="test.md",
        review_type=ReviewType.CODE,
        perspective=ReviewPerspective.SECURITY,
        status=ReviewStatus.SUCCESS,
        feedbacks=[
            ReviewFeedback(
                category=ReviewPerspective.SECURITY,
                severity=FeedbackSeverity.CRITICAL,
                message="Critical issue 1",
            ),
            ReviewFeedback(
                category=ReviewPerspective.SECURITY,
                severity=FeedbackSeverity.WARNING,
                message="Warning issue",
            ),
            ReviewFeedback(
                category=ReviewPerspective.SECURITY,
                severity=FeedbackSeverity.CRITICAL,
                message="Critical issue 2",
            ),
            ReviewFeedback(
                category=ReviewPerspective.SECURITY,
                severity=FeedbackSeverity.INFO,
                message="Info item",
            ),
        ],
        overall_score=50.0,
        execution_time_seconds=10.0,
        provider_name="test",
    )

    assert len(result.critical_issues) == 2
    assert len(result.warnings) == 1
    assert len(result.info_items) == 1


def test_review_result_max_feedbacks() -> None:
    """Test feedback limit validation"""
    # Create list exceeding MAX_FEEDBACK_ITEMS
    feedbacks = [
        ReviewFeedback(
            category=ReviewPerspective.ARCHITECTURE,
            severity=FeedbackSeverity.INFO,
            message=f"Issue {i}",
        )
        for i in range(MAX_FEEDBACK_ITEMS + 1)
    ]

    with pytest.raises(ValueError, match="Too many feedback items"):
        ReviewResult(
            job_id="test",
            document_path="test.md",
            review_type=ReviewType.CODE,
            perspective=ReviewPerspective.ARCHITECTURE,
            status=ReviewStatus.SUCCESS,
            feedbacks=feedbacks,
            overall_score=50.0,
            execution_time_seconds=10.0,
            provider_name="test",
        )


# =============================================================================
# AggregatedReview Tests
# =============================================================================


def test_aggregated_review_creation() -> None:
    """Test aggregated review creation"""
    result1 = ReviewResult(
        job_id="job1",
        document_path="test.md",
        review_type=ReviewType.DESIGN,
        perspective=ReviewPerspective.ARCHITECTURE,
        status=ReviewStatus.SUCCESS,
        feedbacks=[
            ReviewFeedback(
                category=ReviewPerspective.ARCHITECTURE,
                severity=FeedbackSeverity.WARNING,
                message="Issue 1",
            )
        ],
        overall_score=80.0,
        execution_time_seconds=10.0,
        provider_name="test",
    )

    result2 = ReviewResult(
        job_id="job2",
        document_path="test.md",
        review_type=ReviewType.DESIGN,
        perspective=ReviewPerspective.SECURITY,
        status=ReviewStatus.SUCCESS,
        feedbacks=[
            ReviewFeedback(
                category=ReviewPerspective.SECURITY,
                severity=FeedbackSeverity.CRITICAL,
                message="Issue 2",
            )
        ],
        overall_score=60.0,
        execution_time_seconds=15.0,
        provider_name="test",
    )

    aggregated = AggregatedReview(
        document_path="test.md",
        review_type=ReviewType.DESIGN,
        perspectives=[ReviewPerspective.ARCHITECTURE, ReviewPerspective.SECURITY],
        results=[result1, result2],
        overall_score=70.0,
        critical_count=1,
        warning_count=1,
        execution_time_seconds=25.0,
    )

    assert len(aggregated.results) == 2
    assert aggregated.overall_score == 70.0
    assert aggregated.critical_count == 1
    assert aggregated.warning_count == 1


def test_aggregated_review_all_feedbacks() -> None:
    """Test all_feedbacks property"""
    result1 = ReviewResult(
        job_id="job1",
        document_path="test.md",
        review_type=ReviewType.CODE,
        perspective=ReviewPerspective.ARCHITECTURE,
        status=ReviewStatus.SUCCESS,
        feedbacks=[
            ReviewFeedback(
                category=ReviewPerspective.ARCHITECTURE,
                severity=FeedbackSeverity.INFO,
                message="Feedback 1",
            ),
            ReviewFeedback(
                category=ReviewPerspective.ARCHITECTURE,
                severity=FeedbackSeverity.INFO,
                message="Feedback 2",
            ),
        ],
        overall_score=90.0,
        execution_time_seconds=5.0,
        provider_name="test",
    )

    result2 = ReviewResult(
        job_id="job2",
        document_path="test.md",
        review_type=ReviewType.CODE,
        perspective=ReviewPerspective.SECURITY,
        status=ReviewStatus.SUCCESS,
        feedbacks=[
            ReviewFeedback(
                category=ReviewPerspective.SECURITY,
                severity=FeedbackSeverity.WARNING,
                message="Feedback 3",
            )
        ],
        overall_score=85.0,
        execution_time_seconds=7.0,
        provider_name="test",
    )

    aggregated = AggregatedReview(
        document_path="test.md",
        review_type=ReviewType.CODE,
        perspectives=[ReviewPerspective.ARCHITECTURE, ReviewPerspective.SECURITY],
        results=[result1, result2],
        overall_score=87.5,
        critical_count=0,
        warning_count=1,
        execution_time_seconds=12.0,
    )

    all_fb = aggregated.all_feedbacks
    assert len(all_fb) == 3


# =============================================================================
# Error Classes Tests
# =============================================================================


def test_review_provider_error() -> None:
    """Test base error class"""
    error = ReviewProviderError("Test error")
    assert str(error) == "Test error"
    assert isinstance(error, Exception)


def test_review_timeout_error() -> None:
    """Test timeout error"""
    error = ReviewTimeoutError("Timeout after 300s")
    assert isinstance(error, ReviewProviderError)


def test_review_execution_error() -> None:
    """Test execution error"""
    error = ReviewExecutionError("Execution failed")
    assert isinstance(error, ReviewProviderError)


def test_provider_not_available_error() -> None:
    """Test provider not available error"""
    error = ProviderNotAvailableError("Codex CLI not found")
    assert isinstance(error, ReviewProviderError)


# =============================================================================
# BaseReviewProvider Interface Tests
# =============================================================================


class MockReviewProvider(BaseReviewProvider):
    """Mock provider for testing"""

    def __init__(self, available: bool = True):
        self._available = available

    async def review_document(self, request: ReviewRequest) -> ReviewResult:
        return ReviewResult(
            job_id="mock - job",
            document_path=request.document_path,
            review_type=request.review_type,
            perspective=request.perspective,
            status=ReviewStatus.SUCCESS,
            feedbacks=[],
            overall_score=100.0,
            execution_time_seconds=1.0,
            provider_name="mock",
        )

    def is_available(self) -> bool:
        return self._available

    @property
    def provider_name(self) -> str:
        return "mock"


@pytest.mark.asyncio
async def test_base_provider_interface(temp_document: Path) -> None:
    """Test BaseReviewProvider interface"""
    provider = MockReviewProvider()

    assert provider.provider_name == "mock"
    assert provider.is_available() is True

    request = ReviewRequest(
        document_path=str(temp_document),
        review_type=ReviewType.CODE,
        perspective=ReviewPerspective.ARCHITECTURE,
    )

    result = await provider.review_document(request)
    assert result.status == ReviewStatus.SUCCESS
    assert result.provider_name == "mock"


@pytest.mark.asyncio
async def test_base_provider_unavailable() -> None:
    """Test unavailable provider"""
    provider = MockReviewProvider(available=False)
    assert provider.is_available() is False
