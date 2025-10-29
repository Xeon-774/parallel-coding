"""
Unit tests for HierarchicalJobOrchestrator review functionality.

Tests cover:
- Provider registration
- Review document execution
- Parallel multi-perspective review
- Provider selection logic
- Result aggregation
- Error handling

Coverage target: ≥90%
Excellence AI Standard: 100% Applied
"""

from pathlib import Path
from typing import List
from unittest.mock import AsyncMock, Mock

import pytest

from orchestrator.core.ai_providers.base_review_provider import (
    BaseReviewProvider,
    FeedbackSeverity,
    ReviewFeedback,
    ReviewPerspective,
    ReviewRequest,
    ReviewResult,
    ReviewStatus,
    ReviewType,
)
from orchestrator.core.hierarchical.job_orchestrator import (
    HierarchicalJobOrchestrator,
)

# =============================================================================
# Mock Provider
# =============================================================================


class MockReviewProvider(BaseReviewProvider):
    """Mock review provider for testing"""

    def __init__(
        self,
        name: str = "mock",
        available: bool = True,
        score: float = 85.0,
        feedbacks: List[ReviewFeedback] = None,
    ):
        self._name = name
        self._available = available
        self._score = score
        self._feedbacks = feedbacks or []
        self.review_calls = []

    @property
    def provider_name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        return self._available

    async def review_document(self, request: ReviewRequest) -> ReviewResult:
        self.review_calls.append(request)

        return ReviewResult(
            job_id=f"mock-job-{len(self.review_calls)}",
            document_path=request.document_path,
            review_type=request.review_type,
            perspective=request.perspective,
            status=ReviewStatus.SUCCESS,
            feedbacks=self._feedbacks,
            overall_score=self._score,
            execution_time_seconds=1.0,
            provider_name=self._name,
        )


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def orchestrator() -> HierarchicalJobOrchestrator:
    """Create orchestrator instance"""
    return HierarchicalJobOrchestrator()


@pytest.fixture
def mock_provider() -> MockReviewProvider:
    """Create mock provider"""
    return MockReviewProvider(name="test_provider", score=90.0)


@pytest.fixture
def temp_document(tmp_path: Path) -> Path:
    """Create temporary test document"""
    doc = tmp_path / "test_roadmap.md"
    doc.write_text("# Roadmap\n\n- Task 1\n- Task 2", encoding="utf-8")
    return doc


@pytest.fixture
def sample_request(temp_document: Path) -> ReviewRequest:
    """Create sample review request"""
    return ReviewRequest(
        document_path=str(temp_document),
        review_type=ReviewType.ROADMAP,
        perspective=ReviewPerspective.FEASIBILITY,
    )


# =============================================================================
# Provider Registration Tests
# =============================================================================


def test_register_review_provider(
    orchestrator: HierarchicalJobOrchestrator, mock_provider: MockReviewProvider
) -> None:
    """Test registering a review provider"""
    orchestrator.register_review_provider(mock_provider)

    assert "test_provider" in orchestrator._review_providers
    assert orchestrator._review_providers["test_provider"] is mock_provider


def test_register_multiple_providers(
    orchestrator: HierarchicalJobOrchestrator,
) -> None:
    """Test registering multiple providers"""
    provider1 = MockReviewProvider(name="provider1")
    provider2 = MockReviewProvider(name="provider2")

    orchestrator.register_review_provider(provider1)
    orchestrator.register_review_provider(provider2)

    assert len(orchestrator._review_providers) == 2
    assert "provider1" in orchestrator._review_providers
    assert "provider2" in orchestrator._review_providers


def test_register_provider_as_default(
    orchestrator: HierarchicalJobOrchestrator, mock_provider: MockReviewProvider
) -> None:
    """Test registering provider as default"""
    orchestrator.register_review_provider(mock_provider, set_as_default=True)

    assert orchestrator._default_review_provider == "test_provider"


def test_register_provider_default_auto_set(
    orchestrator: HierarchicalJobOrchestrator, mock_provider: MockReviewProvider
) -> None:
    """Test first provider automatically becomes default"""
    orchestrator.register_review_provider(mock_provider)

    assert orchestrator._default_review_provider == "test_provider"


# =============================================================================
# Get Available Providers Tests
# =============================================================================


def test_get_available_providers_all_available(
    orchestrator: HierarchicalJobOrchestrator,
) -> None:
    """Test getting available providers when all are available"""
    provider1 = MockReviewProvider(name="provider1", available=True)
    provider2 = MockReviewProvider(name="provider2", available=True)

    orchestrator.register_review_provider(provider1)
    orchestrator.register_review_provider(provider2)

    available = orchestrator.get_available_review_providers()

    assert len(available) == 2
    assert "provider1" in available
    assert "provider2" in available


def test_get_available_providers_some_unavailable(
    orchestrator: HierarchicalJobOrchestrator,
) -> None:
    """Test getting available providers when some are unavailable"""
    provider1 = MockReviewProvider(name="provider1", available=True)
    provider2 = MockReviewProvider(name="provider2", available=False)
    provider3 = MockReviewProvider(name="provider3", available=True)

    orchestrator.register_review_provider(provider1)
    orchestrator.register_review_provider(provider2)
    orchestrator.register_review_provider(provider3)

    available = orchestrator.get_available_review_providers()

    assert len(available) == 2
    assert "provider1" in available
    assert "provider3" in available
    assert "provider2" not in available


def test_get_available_providers_none_available(
    orchestrator: HierarchicalJobOrchestrator,
) -> None:
    """Test getting available providers when none are available"""
    provider1 = MockReviewProvider(name="provider1", available=False)
    provider2 = MockReviewProvider(name="provider2", available=False)

    orchestrator.register_review_provider(provider1)
    orchestrator.register_review_provider(provider2)

    available = orchestrator.get_available_review_providers()

    assert len(available) == 0


# =============================================================================
# Review Document Tests
# =============================================================================


@pytest.mark.asyncio
async def test_review_document_with_specific_provider(
    orchestrator: HierarchicalJobOrchestrator,
    mock_provider: MockReviewProvider,
    sample_request: ReviewRequest,
) -> None:
    """Test review with specific provider"""
    orchestrator.register_review_provider(mock_provider)

    result = await orchestrator.review_document(sample_request, provider="test_provider")

    assert result.status == ReviewStatus.SUCCESS
    assert result.provider_name == "test_provider"
    assert result.overall_score == 90.0
    assert len(mock_provider.review_calls) == 1


@pytest.mark.asyncio
async def test_review_document_auto_provider_selection(
    orchestrator: HierarchicalJobOrchestrator,
    mock_provider: MockReviewProvider,
    sample_request: ReviewRequest,
) -> None:
    """Test review with auto provider selection"""
    orchestrator.register_review_provider(mock_provider, set_as_default=True)

    result = await orchestrator.review_document(sample_request, provider="auto")

    assert result.status == ReviewStatus.SUCCESS
    assert result.provider_name == "test_provider"


@pytest.mark.asyncio
async def test_review_document_provider_not_found(
    orchestrator: HierarchicalJobOrchestrator, sample_request: ReviewRequest
) -> None:
    """Test review with non-existent provider"""
    with pytest.raises(ValueError, match="Review provider not found"):
        await orchestrator.review_document(sample_request, provider="nonexistent")


@pytest.mark.asyncio
async def test_review_document_provider_unavailable(
    orchestrator: HierarchicalJobOrchestrator, sample_request: ReviewRequest
) -> None:
    """Test review with unavailable provider"""
    provider = MockReviewProvider(name="unavailable", available=False)
    orchestrator.register_review_provider(provider)

    with pytest.raises(ValueError, match="Review provider not available"):
        await orchestrator.review_document(sample_request, provider="unavailable")


@pytest.mark.asyncio
async def test_review_document_no_providers_registered(
    orchestrator: HierarchicalJobOrchestrator, sample_request: ReviewRequest
) -> None:
    """Test review with no providers registered"""
    with pytest.raises(ValueError, match="No review providers available"):
        await orchestrator.review_document(sample_request, provider="auto")


# =============================================================================
# Parallel Review Tests
# =============================================================================


@pytest.mark.asyncio
async def test_parallel_review_multiple_perspectives(
    orchestrator: HierarchicalJobOrchestrator,
    mock_provider: MockReviewProvider,
    temp_document: Path,
) -> None:
    """Test parallel review from multiple perspectives"""
    orchestrator.register_review_provider(mock_provider)

    perspectives = [
        ReviewPerspective.ARCHITECTURE,
        ReviewPerspective.SECURITY,
        ReviewPerspective.PERFORMANCE,
    ]

    aggregated = await orchestrator.parallel_review(
        document_path=str(temp_document),
        review_type=ReviewType.DESIGN,
        perspectives=perspectives,
    )

    # Verify aggregation
    assert len(aggregated.results) == 3
    assert aggregated.overall_score == 90.0  # All same score
    assert len(aggregated.perspectives) == 3
    assert ReviewPerspective.ARCHITECTURE in aggregated.perspectives
    assert ReviewPerspective.SECURITY in aggregated.perspectives
    assert ReviewPerspective.PERFORMANCE in aggregated.perspectives

    # Verify provider was called 3 times
    assert len(mock_provider.review_calls) == 3


@pytest.mark.asyncio
async def test_parallel_review_with_feedbacks(
    orchestrator: HierarchicalJobOrchestrator, temp_document: Path
) -> None:
    """Test parallel review aggregates feedbacks correctly"""
    feedbacks_arch = [
        ReviewFeedback(
            category=ReviewPerspective.ARCHITECTURE,
            severity=FeedbackSeverity.WARNING,
            message="Architecture issue",
        )
    ]
    feedbacks_security = [
        ReviewFeedback(
            category=ReviewPerspective.SECURITY,
            severity=FeedbackSeverity.CRITICAL,
            message="Security issue",
        ),
        ReviewFeedback(
            category=ReviewPerspective.SECURITY,
            severity=FeedbackSeverity.WARNING,
            message="Another security concern",
        ),
    ]

    provider = MockReviewProvider(
        name="multi_feedback",
        score=75.0,
        feedbacks=feedbacks_arch,  # Will be overridden per call
    )

    # Custom mock that returns different feedbacks per perspective
    original_review = provider.review_document

    async def custom_review(request: ReviewRequest) -> ReviewResult:
        result = await original_review(request)
        if request.perspective == ReviewPerspective.ARCHITECTURE:
            result.feedbacks = feedbacks_arch
        elif request.perspective == ReviewPerspective.SECURITY:
            result.feedbacks = feedbacks_security
        else:
            result.feedbacks = []
        return result

    provider.review_document = custom_review

    orchestrator.register_review_provider(provider)

    aggregated = await orchestrator.parallel_review(
        document_path=str(temp_document),
        review_type=ReviewType.CODE,
        perspectives=[ReviewPerspective.ARCHITECTURE, ReviewPerspective.SECURITY],
    )

    # Verify aggregated metrics
    all_feedbacks = aggregated.all_feedbacks
    assert len(all_feedbacks) == 3  # 1 arch + 2 security
    assert aggregated.critical_count == 1
    assert aggregated.warning_count == 2


@pytest.mark.asyncio
async def test_parallel_review_single_perspective(
    orchestrator: HierarchicalJobOrchestrator,
    mock_provider: MockReviewProvider,
    temp_document: Path,
) -> None:
    """Test parallel review with single perspective"""
    orchestrator.register_review_provider(mock_provider)

    aggregated = await orchestrator.parallel_review(
        document_path=str(temp_document),
        review_type=ReviewType.ROADMAP,
        perspectives=[ReviewPerspective.FEASIBILITY],
    )

    assert len(aggregated.results) == 1
    assert len(mock_provider.review_calls) == 1


# =============================================================================
# Provider Selection Logic Tests
# =============================================================================


@pytest.mark.asyncio
async def test_select_best_provider_default_available(
    orchestrator: HierarchicalJobOrchestrator,
) -> None:
    """Test best provider selection when default is available"""
    provider1 = MockReviewProvider(name="default", available=True)
    provider2 = MockReviewProvider(name="backup", available=True)

    orchestrator.register_review_provider(provider1, set_as_default=True)
    orchestrator.register_review_provider(provider2)

    selected = orchestrator._select_best_provider()

    assert selected == "default"


@pytest.mark.asyncio
async def test_select_best_provider_default_unavailable(
    orchestrator: HierarchicalJobOrchestrator,
) -> None:
    """Test best provider selection when default is unavailable"""
    provider1 = MockReviewProvider(name="default", available=False)
    provider2 = MockReviewProvider(name="backup", available=True)

    orchestrator.register_review_provider(provider1, set_as_default=True)
    orchestrator.register_review_provider(provider2)

    selected = orchestrator._select_best_provider()

    assert selected == "backup"


def test_select_best_provider_none_available(
    orchestrator: HierarchicalJobOrchestrator,
) -> None:
    """Test best provider selection when none available"""
    provider1 = MockReviewProvider(name="provider1", available=False)
    provider2 = MockReviewProvider(name="provider2", available=False)

    orchestrator.register_review_provider(provider1)
    orchestrator.register_review_provider(provider2)

    with pytest.raises(ValueError, match="No review providers available"):
        orchestrator._select_best_provider()


# =============================================================================
# Result Aggregation Tests
# =============================================================================


def test_aggregate_review_results(orchestrator: HierarchicalJobOrchestrator) -> None:
    """Test aggregating review results"""
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
                message="Warning 1",
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
                message="Critical 1",
            ),
            ReviewFeedback(
                category=ReviewPerspective.SECURITY,
                severity=FeedbackSeverity.WARNING,
                message="Warning 2",
            ),
        ],
        overall_score=60.0,
        execution_time_seconds=15.0,
        provider_name="test",
    )

    aggregated = orchestrator._aggregate_review_results(
        "test.md", ReviewType.DESIGN, [result1, result2]
    )

    assert aggregated.document_path == "test.md"
    assert aggregated.review_type == ReviewType.DESIGN
    assert len(aggregated.results) == 2
    assert aggregated.overall_score == 70.0  # (80 + 60) / 2
    assert aggregated.critical_count == 1
    assert aggregated.warning_count == 2
    assert aggregated.execution_time_seconds == 25.0


def test_aggregate_review_results_empty(
    orchestrator: HierarchicalJobOrchestrator,
) -> None:
    """Test aggregating empty results list"""
    with pytest.raises(ValueError, match="No review results to aggregate"):
        orchestrator._aggregate_review_results("test.md", ReviewType.CODE, [])
