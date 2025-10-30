"""
Unit tests for CodexReviewProvider.

Tests cover:
- Provider initialization
- Review execution
- Prompt building
- Output parsing
- Score calculation
- Error handling

Coverage target: ≥90%
Excellence AI Standard: 100% Applied
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from orchestrator.core.ai_providers.base_review_provider import (
    FeedbackSeverity,
    ReviewPerspective,
    ReviewRequest,
    ReviewStatus,
    ReviewType,
)
from orchestrator.core.ai_providers.codex_review_provider import (
    PROVIDER_NAME,
    REVIEW_PROMPTS,
    CodexReviewProvider,
    create_codex_review_provider,
)
from orchestrator.core.worker.codex_executor import (
    CodexExecutionResult,
    CodexExecutor,
    ExecutionStatus,
    UsageInfo,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_executor() -> Mock:
    """Create mock CodexExecutor"""
    executor = Mock(spec=CodexExecutor)
    return executor


@pytest.fixture
def provider(mock_executor: Mock) -> CodexReviewProvider:
    """Create CodexReviewProvider with mock executor"""
    return CodexReviewProvider(mock_executor)


@pytest.fixture
def temp_document(tmp_path: Path) -> Path:
    """Create temporary test document"""
    doc = tmp_path / "test_design.md"
    content = """# Design Document

## Architecture
- Component A
- Component B

## Security
- Use HTTPS
- API key management
"""
    doc.write_text(content, encoding="utf - 8")
    return doc


@pytest.fixture
def sample_request(temp_document: Path) -> ReviewRequest:
    """Create sample review request"""
    return ReviewRequest(
        document_path=str(temp_document),
        review_type=ReviewType.DESIGN,
        perspective=ReviewPerspective.ARCHITECTURE,
        context={"project": "test"},
    )


# =============================================================================
# Provider Initialization Tests
# =============================================================================


def test_provider_initialization(mock_executor: Mock) -> None:
    """Test provider initialization"""
    provider = CodexReviewProvider(mock_executor)

    assert provider.provider_name == PROVIDER_NAME
    assert provider._executor is mock_executor


def test_provider_name() -> None:
    """Test provider name constant"""
    assert PROVIDER_NAME == "codex"


def test_create_codex_review_provider(mock_executor: Mock) -> None:
    """Test factory function"""
    provider = create_codex_review_provider(mock_executor)

    assert isinstance(provider, CodexReviewProvider)
    assert provider.provider_name == "codex"


# =============================================================================
# Availability Tests
# =============================================================================


def test_is_available_true(provider: CodexReviewProvider) -> None:
    """Test provider availability check (available)"""
    assert provider.is_available() is True


def test_is_available_none_executor() -> None:
    """Test provider availability with None executor"""
    provider = CodexReviewProvider(None)  # type: ignore
    assert provider.is_available() is False


# =============================================================================
# Prompt Building Tests
# =============================================================================


def test_build_review_prompt_architecture(
    provider: CodexReviewProvider, sample_request: ReviewRequest
) -> None:
    """Test prompt building for architecture perspective"""
    prompt = provider._build_review_prompt(sample_request)

    assert "architecture" in prompt.lower()
    assert sample_request.document_path in prompt
    assert "project: test" in prompt.lower()
    assert "Component A" in prompt
    assert "Component B" in prompt


def test_build_review_prompt_security(provider: CodexReviewProvider, temp_document: Path) -> None:
    """Test prompt building for security perspective"""
    request = ReviewRequest(
        document_path=str(temp_document),
        review_type=ReviewType.CODE,
        perspective=ReviewPerspective.SECURITY,
    )

    prompt = provider._build_review_prompt(request)

    assert "security" in prompt.lower()
    assert "vulnerabilities" in prompt.lower() or "authentication" in prompt.lower()


def test_build_review_prompt_all_perspectives(
    provider: CodexReviewProvider, temp_document: Path
) -> None:
    """Test prompt building for all perspectives"""
    for perspective in ReviewPerspective:
        request = ReviewRequest(
            document_path=str(temp_document),
            review_type=ReviewType.DESIGN,
            perspective=perspective,
        )

        prompt = provider._build_review_prompt(request)
        assert len(prompt) > 100
        assert str(temp_document) in prompt


def test_review_prompts_completeness() -> None:
    """Test that all perspectives have prompts"""
    for perspective in ReviewPerspective:
        assert perspective in REVIEW_PROMPTS
        assert len(REVIEW_PROMPTS[perspective]) > 50


# =============================================================================
# Output Parsing Tests
# =============================================================================


def test_parse_review_output_single_feedback(provider: CodexReviewProvider) -> None:
    """Test parsing single feedback item"""
    output = """
[SEVERITY:CRITICAL] [LINE:42] API keys should not be hardcoded
Suggestion: Use environment variables or secrets manager
---
"""

    feedbacks = provider._parse_review_output(output, ReviewPerspective.SECURITY)

    assert len(feedbacks) == 1
    assert feedbacks[0].severity == FeedbackSeverity.CRITICAL
    assert feedbacks[0].line_number == 42
    assert "API keys" in feedbacks[0].message
    assert "environment variables" in feedbacks[0].suggestion


def test_parse_review_output_multiple_feedbacks(provider: CodexReviewProvider) -> None:
    """Test parsing multiple feedback items"""
    output = """
[SEVERITY:CRITICAL] [LINE:10] Security issue
Suggestion: Fix immediately
---
[SEVERITY:WARNING] [LINE:25] Performance concern
Suggestion: Optimize algorithm
---
[SEVERITY:INFO] Documentation could be improved
Suggestion: Add more examples
---
"""

    feedbacks = provider._parse_review_output(output, ReviewPerspective.ARCHITECTURE)

    assert len(feedbacks) == 3
    assert feedbacks[0].severity == FeedbackSeverity.CRITICAL
    assert feedbacks[1].severity == FeedbackSeverity.WARNING
    assert feedbacks[2].severity == FeedbackSeverity.INFO
    assert feedbacks[2].line_number is None  # No line number


def test_parse_review_output_no_line_number(provider: CodexReviewProvider) -> None:
    """Test parsing feedback without line number"""
    output = """
[SEVERITY:WARNING] General architecture concern
Suggestion: Consider microservices pattern
---
"""

    feedbacks = provider._parse_review_output(output, ReviewPerspective.ARCHITECTURE)

    assert len(feedbacks) == 1
    assert feedbacks[0].line_number is None
    assert feedbacks[0].message == "General architecture concern"


def test_parse_review_output_empty(provider: CodexReviewProvider) -> None:
    """Test parsing empty output"""
    output = ""

    feedbacks = provider._parse_review_output(output, ReviewPerspective.SECURITY)

    assert len(feedbacks) == 0


def test_parse_review_output_malformed(provider: CodexReviewProvider) -> None:
    """Test parsing malformed output"""
    output = """
This is some random text without proper formatting.
No severity markers or structure.
"""

    feedbacks = provider._parse_review_output(output, ReviewPerspective.ARCHITECTURE)

    # Should handle gracefully and return empty list
    assert len(feedbacks) == 0


# =============================================================================
# Score Calculation Tests
# =============================================================================


def test_calculate_score_perfect(provider: CodexReviewProvider) -> None:
    """Test score calculation with no issues"""
    feedbacks = []

    score = provider._calculate_score(feedbacks)

    assert score == 100.0


def test_calculate_score_critical_issues(provider: CodexReviewProvider) -> None:
    """Test score calculation with critical issues"""
    from orchestrator.core.ai_providers.base_review_provider import ReviewFeedback

    feedbacks = [
        ReviewFeedback(
            category=ReviewPerspective.SECURITY,
            severity=FeedbackSeverity.CRITICAL,
            message="Critical issue 1",
        ),
        ReviewFeedback(
            category=ReviewPerspective.SECURITY,
            severity=FeedbackSeverity.CRITICAL,
            message="Critical issue 2",
        ),
    ]

    score = provider._calculate_score(feedbacks)

    # 100 - (20 * 2) = 60
    assert score == 60.0


def test_calculate_score_mixed_severity(provider: CodexReviewProvider) -> None:
    """Test score calculation with mixed severity"""
    from orchestrator.core.ai_providers.base_review_provider import ReviewFeedback

    feedbacks = [
        ReviewFeedback(
            category=ReviewPerspective.ARCHITECTURE,
            severity=FeedbackSeverity.CRITICAL,
            message="Critical",
        ),  # -20
        ReviewFeedback(
            category=ReviewPerspective.ARCHITECTURE,
            severity=FeedbackSeverity.WARNING,
            message="Warning",
        ),  # -10
        ReviewFeedback(
            category=ReviewPerspective.ARCHITECTURE,
            severity=FeedbackSeverity.INFO,
            message="Info",
        ),  # -2
    ]

    score = provider._calculate_score(feedbacks)

    # 100 - 20 - 10 - 2 = 68
    assert score == 68.0


def test_calculate_score_minimum_zero(provider: CodexReviewProvider) -> None:
    """Test score cannot go below zero"""
    from orchestrator.core.ai_providers.base_review_provider import ReviewFeedback

    feedbacks = [
        ReviewFeedback(
            category=ReviewPerspective.SECURITY,
            severity=FeedbackSeverity.CRITICAL,
            message=f"Critical issue {i}",
        )
        for i in range(10)  # 10 * 20 = 200 points
    ]

    score = provider._calculate_score(feedbacks)

    assert score == 0.0


# =============================================================================
# Review Execution Tests
# =============================================================================


@pytest.mark.asyncio
async def test_review_document_success(
    provider: CodexReviewProvider,
    mock_executor: Mock,
    sample_request: ReviewRequest,
) -> None:
    """Test successful review execution"""
    # Mock successful execution
    mock_result = CodexExecutionResult(
        status=ExecutionStatus.SUCCESS,
        exit_code=0,
        stdout="""
[SEVERITY:WARNING] [LINE:5] Consider dependency injection
Suggestion: Use constructor injection pattern
---
""",
        stderr="",
        duration_seconds=10.5,
        events=[],
        file_changes=[],
        usage=UsageInfo(input_tokens=1000, output_tokens=500),
    )
    mock_executor.execute.return_value = mock_result

    result = await provider.review_document(sample_request)

    assert result.status == ReviewStatus.SUCCESS
    assert result.overall_score > 0
    assert len(result.feedbacks) == 1
    assert result.feedbacks[0].severity == FeedbackSeverity.WARNING
    assert result.provider_name == "codex"
    assert result.metadata["usage"]["input_tokens"] == 1000


@pytest.mark.asyncio
async def test_review_document_timeout(
    provider: CodexReviewProvider,
    mock_executor: Mock,
    sample_request: ReviewRequest,
) -> None:
    """Test review execution timeout"""
    mock_result = CodexExecutionResult(
        status=ExecutionStatus.TIMEOUT,
        exit_code=-1,
        stdout="",
        stderr="",
        duration_seconds=300.0,
        events=[],
        error_message="Execution timeout",
    )
    mock_executor.execute.return_value = mock_result

    result = await provider.review_document(sample_request)

    assert result.status == ReviewStatus.TIMEOUT
    assert result.overall_score == 0.0
    assert len(result.feedbacks) == 0
    assert result.error_message is not None
    assert "timed out" in result.error_message.lower()


@pytest.mark.asyncio
async def test_review_document_execution_failed(
    provider: CodexReviewProvider,
    mock_executor: Mock,
    sample_request: ReviewRequest,
) -> None:
    """Test review execution failure"""
    mock_result = CodexExecutionResult(
        status=ExecutionStatus.FAILED,
        exit_code=1,
        stdout="",
        stderr="Codex error",
        duration_seconds=5.0,
        events=[],
        error_message="Codex execution failed",
    )
    mock_executor.execute.return_value = mock_result

    result = await provider.review_document(sample_request)

    assert result.status == ReviewStatus.FAILED
    assert result.overall_score == 0.0
    assert result.error_message is not None


@pytest.mark.asyncio
async def test_review_document_exception_handling(
    provider: CodexReviewProvider,
    mock_executor: Mock,
    sample_request: ReviewRequest,
) -> None:
    """Test exception handling during review"""
    mock_executor.execute.side_effect = Exception("Unexpected error")

    result = await provider.review_document(sample_request)

    assert result.status == ReviewStatus.FAILED
    assert "Unexpected error" in result.error_message


@pytest.mark.asyncio
async def test_review_document_provider_unavailable(
    mock_executor: Mock, sample_request: ReviewRequest
) -> None:
    """Test review with unavailable provider"""
    from orchestrator.core.ai_providers.base_review_provider import (
        ProviderNotAvailableError,
    )

    provider = CodexReviewProvider(None)  # type: ignore

    with pytest.raises(ProviderNotAvailableError):
        await provider.review_document(sample_request)


# =============================================================================
# Integration - style Tests
# =============================================================================


@pytest.mark.asyncio
async def test_full_review_workflow(
    provider: CodexReviewProvider,
    mock_executor: Mock,
    temp_document: Path,
) -> None:
    """Test complete review workflow"""
    # Setup mock
    mock_result = CodexExecutionResult(
        status=ExecutionStatus.SUCCESS,
        exit_code=0,
        stdout="""
[SEVERITY:CRITICAL] [LINE:10] Security vulnerability found
Suggestion: Implement input validation
---
[SEVERITY:WARNING] [LINE:25] Performance bottleneck
Suggestion: Use caching
---
[SEVERITY:INFO] Documentation incomplete
Suggestion: Add API examples
---
""",
        stderr="",
        duration_seconds=15.2,
        events=[],
        usage=UsageInfo(input_tokens=2000, output_tokens=800),
    )
    mock_executor.execute.return_value = mock_result

    request = ReviewRequest(
        document_path=str(temp_document),
        review_type=ReviewType.DESIGN,
        perspective=ReviewPerspective.SECURITY,
        context={"project": "AI_Investor"},
    )

    result = await provider.review_document(request)

    # Verify result
    assert result.status == ReviewStatus.SUCCESS
    assert len(result.feedbacks) == 3
    assert len(result.critical_issues) == 1
    assert len(result.warnings) == 1
    assert len(result.info_items) == 1

    # Score: 100 - 20 (critical) - 10 (warning) - 2 (info) = 68
    assert result.overall_score == 68.0

    # Verify metadata
    assert result.metadata["usage"]["input_tokens"] == 2000
    assert result.metadata["codex_exit_code"] == 0
