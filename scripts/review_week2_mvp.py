"""
Review Week 2 MVP Specification with Codex.

This script reviews the Week 2 MVP specification document to validate
feasibility, architecture decisions, and implementation estimates.

Usage:
    python scripts / review_week2_mvp.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.config import OrchestratorConfig
from orchestrator.core.ai_providers.base_review_provider import (
    ReviewPerspective,
    ReviewRequest,
    ReviewType,
)
from orchestrator.core.ai_providers.codex_review_provider import (
    CodexReviewProvider,
)
from orchestrator.core.worker.codex_executor import (
    create_codex_executor_from_config,
)


async def review_document(
    provider: CodexReviewProvider,
    document_path: Path,
    review_type: ReviewType,
    perspective: ReviewPerspective,
) -> None:
    """
    Review a document with specified perspective.

    Args:
        provider: CodexReviewProvider instance
        document_path: Path to document
        review_type: Type of review
        perspective: Review perspective
    """
    print(f"Document: {document_path}")
    print(f"Type: {review_type}")
    print(f"Perspective: {perspective}")
    print()

    request = ReviewRequest(
        document_path=str(document_path),
        review_type=review_type,
        perspective=perspective,
        context={
            "project": "Parallel AI Coding Tool - Week 2 MVP",
            "phase": "Supervisor API Implementation",
            "focus": "Validate feasibility of 50h estimate and technical decisions",
        },
    )

    print("Executing review (this may take 1 - 5 minutes)...")
    print("Codex is analyzing the document...")
    print()

    result = await provider.review_document(request)

    print(f"✓ Review completed in {result.execution_time_seconds:.1f}s")
    print()
    print(f"Status: {result.status}")
    print(f"Overall Score: {result.overall_score}/100")
    print()

    if result.metadata.get("token_usage"):
        usage = result.metadata["token_usage"]
        print("Token Usage:")
        print(f"  - Input: {usage.get('input_tokens', 0):,} tokens")
        print(f"  - Output: {usage.get('output_tokens', 0):,} tokens")
        print()

    print("Feedback Summary:")
    print(f"  - Total items: {len(result.feedbacks)}")
    print(f"  - Critical: {len(result.critical_issues)}")
    print(f"  - Warnings: {len(result.warnings)}")
    print(f"  - Info: {len(result.info_items)}")
    print()

    if result.feedbacks:
        print("=" * 80)
        print("Detailed Feedback")
        print("=" * 80)
        for i, feedback in enumerate(result.feedbacks, 1):
            print()
            print(f"[{i}] {feedback.severity.upper()} - {feedback.category}")
            if feedback.section:
                print(f"    Section: {feedback.section}")
            if feedback.line_number:
                print(f"    Line: {feedback.line_number}")
            print(f"    Message: {feedback.message}")
            if feedback.suggestion:
                print(f"    Suggestion: {feedback.suggestion}")
            if feedback.reference:
                print(f"    Reference: {feedback.reference}")


async def main():
    """Main review function"""
    print("=" * 80)
    print("Week 2 MVP Specification - Codex Review")
    print("=" * 80)
    print()

    # Initialize configuration
    print("1. Initializing configuration...")
    config = OrchestratorConfig.from_env()
    print(f"   - WSL Distribution: {config.wsl_distribution}")
    print(f"   - Codex path: {config.nvm_path}/{config.codex_command}")
    print()

    # Create Codex executor
    print("2. Creating Codex executor...")
    executor = create_codex_executor_from_config(config)
    print("   ✓ Executor created")
    print()

    # Create review provider
    print("3. Creating Codex review provider...")
    codex_provider = CodexReviewProvider(executor)
    print(f"   - Provider name: {codex_provider.provider_name}")
    print(f"   - Available: {codex_provider.is_available()}")
    print()

    # Review Week 2 MVP Specification
    print("=" * 80)
    print("Reviewing WEEK2_MVP_SPECIFICATION.md")
    print("=" * 80)
    print()

    mvp_spec_path = project_root / "docs" / "WEEK2_MVP_SPECIFICATION.md"
    if not mvp_spec_path.exists():
        print(f"⚠️  WEEK2_MVP_SPECIFICATION.md not found at {mvp_spec_path}")
        print("   Exiting...")
        return

    # Review from FEASIBILITY perspective
    await review_document(
        codex_provider,
        mvp_spec_path,
        ReviewType.DESIGN,
        ReviewPerspective.FEASIBILITY,
    )

    print()
    print("=" * 80)
    print("Review Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
