"""Unit tests for base review provider module.

Tests BaseReviewProvider abstract class and related models.
"""

import tempfile
from pathlib import Path

import pytest

from orchestrator.core.ai_providers.base_review_provider import (
    AggregatedReview,
    FeedbackSeverity,
    ReviewFeedback,
    ReviewPerspective,
    ReviewRequest,
    ReviewResult,
    ReviewStatus,
    ReviewType,
)


class TestReviewRequestValidation:
    """Test ReviewRequest validation."""

    def test_document_path_traversal_blocked(self):
        """Test that path traversal is blocked."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            f.write("test")
            temp_path = f.name

        try:
            # Path traversal should be blocked
            with pytest.raises(ValueError, match="Path traversal not allowed"):
                ReviewRequest(
                    document_path="../../../etc/passwd",
                    review_type=ReviewType.DESIGN,
                    perspective=ReviewPerspective.ARCHITECTURE,
                )
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_document_not_found(self):
        """Test that non-existent document raises error."""
        with pytest.raises(ValueError, match="Document not found"):
            ReviewRequest(
                document_path="/nonexistent/file.md",
                review_type=ReviewType.DESIGN,
                perspective=ReviewPerspective.ARCHITECTURE,
            )

    def test_document_too_large(self):
        """Test that oversized document raises error."""
        # Create a large file (> 10MB)
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".md") as f:
            # Write 11MB of data
            f.write(b"x" * (11 * 1024 * 1024))
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Document too large"):
                ReviewRequest(
                    document_path=temp_path,
                    review_type=ReviewType.DESIGN,
                    perspective=ReviewPerspective.ARCHITECTURE,
                )
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestReviewResultValidation:
    """Test ReviewResult validation."""

    def test_too_many_feedbacks(self):
        """Test that too many feedback items raises error."""
        # Create more than 500 feedback items
        feedbacks = [
            ReviewFeedback(
                category=ReviewPerspective.ARCHITECTURE,
                severity=FeedbackSeverity.INFO,
                message=f"Feedback {i}",
                line_number=i + 1,  # line_number must be >= 1
            )
            for i in range(501)
        ]

        with pytest.raises(ValueError, match="Too many feedback items"):
            ReviewResult(
                job_id="test-job",
                document_path="test.md",
                review_type=ReviewType.DESIGN,
                perspective=ReviewPerspective.ARCHITECTURE,
                status=ReviewStatus.SUCCESS,
                feedbacks=feedbacks,
                overall_score=85.0,
                execution_time_seconds=1.0,
                provider_name="test",
                metadata={},
            )


class TestReviewResultProperties:
    """Test ReviewResult property methods."""

    def test_is_success_property(self):
        """Test is_success property."""
        result = ReviewResult(
            job_id="test-job",
            document_path="test.md",
            review_type=ReviewType.DESIGN,
            perspective=ReviewPerspective.ARCHITECTURE,
            status=ReviewStatus.SUCCESS,
            feedbacks=[],
            overall_score=85.0,
            execution_time_seconds=1.0,
            provider_name="test",
            metadata={},
        )

        assert result.is_success is True

    def test_critical_issues_property(self):
        """Test critical_issues property."""
        feedbacks = [
            ReviewFeedback(
                category=ReviewPerspective.SECURITY,
                severity=FeedbackSeverity.CRITICAL,
                message="Critical issue 1",
                line_number=10,
            ),
            ReviewFeedback(
                category=ReviewPerspective.SECURITY,
                severity=FeedbackSeverity.WARNING,
                message="Warning 1",
                line_number=20,
            ),
            ReviewFeedback(
                category=ReviewPerspective.SECURITY,
                severity=FeedbackSeverity.CRITICAL,
                message="Critical issue 2",
                line_number=30,
            ),
        ]

        result = ReviewResult(
            job_id="test-job",
            document_path="test.md",
            review_type=ReviewType.DESIGN,
            perspective=ReviewPerspective.ARCHITECTURE,
            status=ReviewStatus.SUCCESS,
            feedbacks=feedbacks,
            overall_score=70.0,
            execution_time_seconds=1.0,
            provider_name="test",
            metadata={},
        )

        critical = result.critical_issues
        assert len(critical) == 2
        assert all(f.severity == FeedbackSeverity.CRITICAL for f in critical)

    def test_warnings_property(self):
        """Test warnings property."""
        feedbacks = [
            ReviewFeedback(
                category=ReviewPerspective.PERFORMANCE,
                severity=FeedbackSeverity.WARNING,
                message="Warning 1",
                line_number=10,
            ),
            ReviewFeedback(
                category=ReviewPerspective.PERFORMANCE,
                severity=FeedbackSeverity.INFO,
                message="Info 1",
                line_number=20,
            ),
            ReviewFeedback(
                category=ReviewPerspective.PERFORMANCE,
                severity=FeedbackSeverity.WARNING,
                message="Warning 2",
                line_number=30,
            ),
        ]

        result = ReviewResult(
            job_id="test-job",
            document_path="test.md",
            review_type=ReviewType.DESIGN,
            perspective=ReviewPerspective.ARCHITECTURE,
            status=ReviewStatus.SUCCESS,
            feedbacks=feedbacks,
            overall_score=85.0,
            execution_time_seconds=1.0,
            provider_name="test",
            metadata={},
        )

        warnings = result.warnings
        assert len(warnings) == 2
        assert all(f.severity == FeedbackSeverity.WARNING for f in warnings)

    def test_info_items_property(self):
        """Test info_items property."""
        feedbacks = [
            ReviewFeedback(
                category=ReviewPerspective.MAINTAINABILITY,
                severity=FeedbackSeverity.INFO,
                message="Info 1",
                line_number=10,
            ),
            ReviewFeedback(
                category=ReviewPerspective.MAINTAINABILITY,
                severity=FeedbackSeverity.WARNING,
                message="Warning 1",
                line_number=20,
            ),
            ReviewFeedback(
                category=ReviewPerspective.MAINTAINABILITY,
                severity=FeedbackSeverity.INFO,
                message="Info 2",
                line_number=30,
            ),
        ]

        result = ReviewResult(
            job_id="test-job",
            document_path="test.md",
            review_type=ReviewType.DESIGN,
            perspective=ReviewPerspective.ARCHITECTURE,
            status=ReviewStatus.SUCCESS,
            feedbacks=feedbacks,
            overall_score=90.0,
            execution_time_seconds=1.0,
            provider_name="test",
            metadata={},
        )

        info = result.info_items
        assert len(info) == 2
        assert all(f.severity == FeedbackSeverity.INFO for f in info)


class TestAggregatedReview:
    """Test AggregatedReview functionality."""

    def test_all_feedbacks_property(self):
        """Test all_feedbacks property aggregates from all results."""
        result1 = ReviewResult(
            job_id="job1",
            document_path="test.md",
            review_type=ReviewType.DESIGN,
            perspective=ReviewPerspective.ARCHITECTURE,
            status=ReviewStatus.SUCCESS,
            feedbacks=[
                ReviewFeedback(
                    category=ReviewPerspective.ARCHITECTURE,
                    severity=FeedbackSeverity.INFO,
                    message="Feedback 1",
                    line_number=10,
                )
            ],
            overall_score=85.0,
            execution_time_seconds=1.0,
            provider_name="provider1",
            metadata={},
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
                    severity=FeedbackSeverity.WARNING,
                    message="Feedback 2",
                    line_number=20,
                ),
                ReviewFeedback(
                    category=ReviewPerspective.SECURITY,
                    severity=FeedbackSeverity.CRITICAL,
                    message="Feedback 3",
                    line_number=30,
                ),
            ],
            overall_score=70.0,
            execution_time_seconds=1.5,
            provider_name="provider2",
            metadata={},
        )

        aggregated = AggregatedReview(
            document_path="test.md",
            review_type=ReviewType.DESIGN,
            perspectives=[ReviewPerspective.ARCHITECTURE, ReviewPerspective.SECURITY],
            results=[result1, result2],
            overall_score=77.5,
            critical_count=1,
            warning_count=1,
            info_count=1,
            execution_time_seconds=2.5,
        )

        all_feedbacks = aggregated.all_feedbacks
        assert len(all_feedbacks) == 3
        assert all_feedbacks[0].message == "Feedback 1"
        assert all_feedbacks[1].message == "Feedback 2"
        assert all_feedbacks[2].message == "Feedback 3"
