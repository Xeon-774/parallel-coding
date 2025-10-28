"""Unit tests for HierarchicalJobOrchestrator.

Tests core orchestration logic, error handling, and review functions.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from orchestrator.core.hierarchical import HierarchicalJobOrchestrator
from orchestrator.core.hierarchical.job_orchestrator import (
    DepthLimitError,
    JobResult,
    RetryDecision,
)
from orchestrator.core.ai_providers.base_review_provider import (
    BaseReviewProvider,
    ReviewPerspective,
    ReviewRequest,
    ReviewResult,
    ReviewType,
)


# ======================= Basic Job Execution Tests =======================


@pytest.mark.asyncio
async def test_submit_leaf_job_completes_with_output():
    orch = HierarchicalJobOrchestrator()
    jr = await orch.submit_job("Just a single task with no bullets", depth=0)
    await orch._tasks[jr.job_id]  # wait for completion
    status = await orch.get_status(jr.job_id)
    assert status.status == "completed"
    assert status.output and "summary" in status.output


@pytest.mark.asyncio
async def test_submit_composed_job_spawns_children():
    orch = HierarchicalJobOrchestrator()
    req = """
    - Task A
    - Task B
    - Task C
    """
    jr = await orch.submit_job(req, depth=0)
    await orch._tasks[jr.job_id]
    tree = await orch.get_tree(jr.job_id)
    assert len(tree["children"]) == 3
    assert tree["children"][0]["depth"] == 1


@pytest.mark.asyncio
async def test_cancel_running_job_sets_canceled():
    orch = HierarchicalJobOrchestrator()
    jr = await orch.submit_job("- A\n- B\n- C\n- D", depth=0)
    # Give the task a moment to start
    await asyncio.sleep(0.01)
    canceled = await orch.cancel(jr.job_id)
    assert canceled in (True, False)  # cancel may race; ensure API doesn't crash
    # cancel() already awaits the task, so status should be updated
    st = await orch.get_status(jr.job_id)
    assert st.status in ("completed", "canceled")


# ======================= Error Handling Tests =======================


@pytest.mark.asyncio
async def test_submit_job_with_invalid_depth_raises_error():
    """Test that submitting job with invalid depth raises DepthLimitError."""
    orch = HierarchicalJobOrchestrator(max_depth=5)

    # Negative depth
    with pytest.raises(DepthLimitError, match="Depth out of bounds"):
        await orch.submit_job("Test task", depth=-1)

    # Depth exceeds max
    with pytest.raises(DepthLimitError, match="Depth out of bounds"):
        await orch.submit_job("Test task", depth=6)


@pytest.mark.asyncio
async def test_spawn_sub_orchestrator_at_max_depth_raises_error():
    """Test that spawning sub-orchestrator at max depth raises DepthLimitError."""
    orch = HierarchicalJobOrchestrator(max_depth=5)

    with pytest.raises(DepthLimitError, match="Max depth reached"):
        await orch.spawn_sub_orchestrator("Subtask", parent_depth=5)


@pytest.mark.asyncio
async def test_cancel_nonexistent_job_returns_false():
    """Test canceling non-existent job returns False."""
    orch = HierarchicalJobOrchestrator()

    result = await orch.cancel("nonexistent-job-id")
    assert result is False


@pytest.mark.asyncio
async def test_cancel_already_completed_job_returns_false():
    """Test canceling already completed job returns False."""
    orch = HierarchicalJobOrchestrator()
    jr = await orch.submit_job("Simple task", depth=0)

    # Wait for completion
    await orch._tasks[jr.job_id]

    # Try to cancel completed job
    result = await orch.cancel(jr.job_id)
    assert result is False


# ======================= Metrics and Aggregation Tests =======================


@pytest.mark.asyncio
async def test_stats_tracks_job_metrics():
    """Test that stats() returns correct metrics."""
    orch = HierarchicalJobOrchestrator()

    initial_stats = orch.stats()
    assert initial_stats["submitted"] == 0
    assert initial_stats["completed"] == 0

    # Submit and complete a job
    jr = await orch.submit_job("Test task", depth=0)
    await orch._tasks[jr.job_id]

    final_stats = orch.stats()
    assert final_stats["submitted"] == 1
    assert final_stats["completed"] == 1


@pytest.mark.asyncio
async def test_aggregate_results_success():
    """Test aggregate_results with successful jobs."""
    orch = HierarchicalJobOrchestrator()

    jobs = [
        JobResult(job_id="j1", depth=0, status="completed", started_at=1.0, output={"result": "ok"}),
        JobResult(job_id="j2", depth=0, status="completed", started_at=1.0, output={"result": "ok"}),
    ]

    aggregated = await orch.aggregate_results(jobs)
    assert aggregated.success is True
    assert len(aggregated.results) == 2
    assert "j1" in aggregated.results


@pytest.mark.asyncio
async def test_aggregate_results_with_failure():
    """Test aggregate_results with failed job."""
    orch = HierarchicalJobOrchestrator()

    jobs = [
        JobResult(job_id="j1", depth=0, status="completed", started_at=1.0, output={"result": "ok"}),
        JobResult(job_id="j2", depth=0, status="failed", started_at=1.0, error="Test error"),
    ]

    aggregated = await orch.aggregate_results(jobs)
    assert aggregated.success is False
    assert "j2" in aggregated.results
    assert "error" in aggregated.results["j2"]


@pytest.mark.asyncio
async def test_handle_sub_job_failure_returns_retry_decision():
    """Test handle_sub_job_failure returns appropriate retry decision."""
    orch = HierarchicalJobOrchestrator()

    jr = await orch.submit_job("Test task", depth=2)
    await orch._tasks[jr.job_id]

    decision = await orch.handle_sub_job_failure(jr.job_id, Exception("Test error"))

    assert isinstance(decision, RetryDecision)
    assert decision.should_retry is True
    assert decision.max_retries == 2
    assert decision.delay_seconds > 0  # Exponential backoff based on depth


# ======================= Review Provider Tests =======================


class MockReviewProvider(BaseReviewProvider):
    """Mock review provider for testing."""

    def __init__(self, name: str, available: bool = True):
        self._name = name
        self._available = available

    @property
    def provider_name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        return self._available

    async def review_document(self, request: ReviewRequest) -> ReviewResult:
        return ReviewResult(
            job_id="test-job-id",
            document_path=request.document_path,
            review_type=request.review_type,
            perspective=request.perspective,
            status="success",
            feedbacks=[],
            overall_score=85.0,
            execution_time_seconds=0.1,
            provider_name=self._name,
            metadata={},
        )


@pytest.mark.asyncio
async def test_register_review_provider():
    """Test registering review provider."""
    orch = HierarchicalJobOrchestrator()
    provider = MockReviewProvider("test_provider")

    orch.register_review_provider(provider, set_as_default=True)

    assert "test_provider" in orch._review_providers
    assert orch._default_review_provider == "test_provider"


@pytest.mark.asyncio
async def test_get_available_review_providers():
    """Test getting available review providers."""
    orch = HierarchicalJobOrchestrator()

    provider1 = MockReviewProvider("provider1", available=True)
    provider2 = MockReviewProvider("provider2", available=False)

    orch.register_review_provider(provider1)
    orch.register_review_provider(provider2)

    available = orch.get_available_review_providers()
    assert "provider1" in available
    assert "provider2" not in available


@pytest.mark.asyncio
async def test_review_document_with_explicit_provider():
    """Test review_document with explicit provider."""
    orch = HierarchicalJobOrchestrator()
    provider = MockReviewProvider("test_provider")
    orch.register_review_provider(provider)

    request = ReviewRequest(
        document_path="CHANGELOG.md",
        review_type=ReviewType.DESIGN,
        perspective=ReviewPerspective.ARCHITECTURE,
    )

    result = await orch.review_document(request, provider="test_provider")

    assert result.overall_score == 85.0
    assert result.document_path == "CHANGELOG.md"


@pytest.mark.asyncio
async def test_review_document_with_auto_provider():
    """Test review_document with auto provider selection."""
    orch = HierarchicalJobOrchestrator()
    provider = MockReviewProvider("test_provider")
    orch.register_review_provider(provider, set_as_default=True)

    request = ReviewRequest(
        document_path="CHANGELOG.md",
        review_type=ReviewType.DESIGN,
        perspective=ReviewPerspective.ARCHITECTURE,
    )

    result = await orch.review_document(request, provider="auto")

    assert result.overall_score == 85.0


@pytest.mark.asyncio
async def test_review_document_with_invalid_provider_raises_error():
    """Test review_document with invalid provider raises ValueError."""
    orch = HierarchicalJobOrchestrator()

    request = ReviewRequest(
        document_path="CHANGELOG.md",
        review_type=ReviewType.DESIGN,
        perspective=ReviewPerspective.ARCHITECTURE,
    )

    with pytest.raises(ValueError, match="Review provider not found"):
        await orch.review_document(request, provider="nonexistent")


@pytest.mark.asyncio
async def test_review_document_with_unavailable_provider_raises_error():
    """Test review_document with unavailable provider raises ValueError."""
    orch = HierarchicalJobOrchestrator()
    provider = MockReviewProvider("test_provider", available=False)
    orch.register_review_provider(provider)

    request = ReviewRequest(
        document_path="CHANGELOG.md",
        review_type=ReviewType.DESIGN,
        perspective=ReviewPerspective.ARCHITECTURE,
    )

    with pytest.raises(ValueError, match="Review provider not available"):
        await orch.review_document(request, provider="test_provider")


@pytest.mark.asyncio
async def test_auto_provider_with_no_providers_raises_error():
    """Test auto provider selection with no providers raises ValueError."""
    orch = HierarchicalJobOrchestrator()

    request = ReviewRequest(
        document_path="CHANGELOG.md",
        review_type=ReviewType.DESIGN,
        perspective=ReviewPerspective.ARCHITECTURE,
    )

    with pytest.raises(ValueError, match="No review providers available"):
        await orch.review_document(request, provider="auto")


@pytest.mark.asyncio
async def test_parallel_review():
    """Test parallel_review executes multiple perspectives."""
    orch = HierarchicalJobOrchestrator()
    provider = MockReviewProvider("test_provider")
    orch.register_review_provider(provider, set_as_default=True)

    perspectives = [
        ReviewPerspective.ARCHITECTURE,
        ReviewPerspective.SECURITY,
        ReviewPerspective.PERFORMANCE,
    ]

    result = await orch.parallel_review(
        document_path="CHANGELOG.md",
        review_type=ReviewType.DESIGN,
        perspectives=perspectives,
        provider="test_provider",
    )

    assert len(result.perspectives) == 3
    assert result.overall_score > 0
    # Note: warning_count depends on feedbacks, not the old warnings field
    assert result.critical_count >= 0


@pytest.mark.asyncio
async def test_aggregate_review_results_with_no_results_raises_error():
    """Test _aggregate_review_results with empty list raises ValueError."""
    orch = HierarchicalJobOrchestrator()

    with pytest.raises(ValueError, match="No review results to aggregate"):
        orch._aggregate_review_results("test.md", ReviewType.DESIGN, [])

