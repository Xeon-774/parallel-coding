"""
Review Week 2 Design Documents with Codex.

This script reviews the Week 2 design documents (OpenAPI spec, State Machine,
Database Schema) to validate architecture, feasibility, and security.

Usage:
    python scripts / review_week2_design.py
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.config import OrchestratorConfig
from orchestrator.core.ai_providers.base_review_provider import (
    ReviewPerspective,
    ReviewRequest,
    ReviewResult,
    ReviewType,
)
from orchestrator.core.ai_providers.codex_review_provider import (
    CodexReviewProvider,
)
from orchestrator.core.ai_providers.review_time_estimator import (
    ExecutionStrategy,
    estimate_from_file,
)
from orchestrator.core.worker.codex_executor import (
    create_codex_executor_from_config,
)


async def review_document(
    provider: CodexReviewProvider,
    document_path: Path,
    review_type: ReviewType,
    perspective: ReviewPerspective,
) -> ReviewResult:
    """
    Review a document with specified perspective.

    Args:
        provider: CodexReviewProvider instance
        document_path: Path to document
        review_type: Type of review
        perspective: Review perspective

    Returns:
        ReviewResult with feedback
    """
    print(f"\n{'='*70}")
    print(f"Document: {document_path.name}")
    print(f"Type: {review_type.value}")
    print(f"Perspective: {perspective.value}")
    print(f"{'='*70}\n")

    request = ReviewRequest(
        document_path=str(document_path),
        review_type=review_type,
        perspective=perspective,
    )

    result = await provider.review_document(request)
    return result


def print_review_summary(document_name: str, result: ReviewResult) -> None:
    """
    Print review result summary.

    Args:
        document_name: Name of reviewed document
        result: ReviewResult to print
    """
    print(f"\n{'='*70}")
    print(f"Review Summary: {document_name}")
    print(f"{'='*70}")
    print(f"Overall Score: {result.overall_score:.1f}/100")
    print(
        f"Feedback Items: {len(result.feedback_items)} "
        f"(Critical: {result.critical_count}, "
        f"Warning: {result.warning_count}, "
        f"Info: {result.info_count})"
    )

    if result.feedback_items:
        print(f"\n{'─'*70}")
        print("Feedback Details:")
        print(f"{'─'*70}\n")

        for i, item in enumerate(result.feedback_items, 1):
            severity_emoji = {
                "CRITICAL": "🔴",
                "WARNING": "🟡",
                "INFO": "ℹ️",
            }
            emoji = severity_emoji.get(item.severity, "")

            print(f"{i}. {emoji} [{item.severity}] {item.category}")
            print(f"   Issue: {item.issue}")
            print(f"   Suggestion: {item.suggestion}")
            if item.line_number:
                print(f"   Location: Line {item.line_number}")
            print()
    else:
        print("\n✅ No issues found!\n")

    print(f"{'='*70}\n")


async def review_all_design_documents() -> Dict[str, List[ReviewResult]]:
    """
    Review all Week 2 design documents.

    Returns:
        Dictionary mapping document names to review results
    """
    # Initialize provider
    config = OrchestratorConfig()
    executor = create_codex_executor_from_config(config)
    provider = CodexReviewProvider(codex_executor=executor)

    docs_dir = project_root / "docs"
    documents = [
        {
            "path": docs_dir / "API_SPECIFICATION.yaml",
            "type": ReviewType.API_SPEC,
            "perspectives": [
                ReviewPerspective.ARCHITECTURE,
                ReviewPerspective.SECURITY,
            ],
        },
        {
            "path": docs_dir / "STATE_MACHINE_DESIGN.md",
            "type": ReviewType.DESIGN,
            "perspectives": [
                ReviewPerspective.ARCHITECTURE,
                ReviewPerspective.FEASIBILITY,
            ],
        },
        {
            "path": docs_dir / "DATABASE_SCHEMA_DESIGN.md",
            "type": ReviewType.DESIGN,
            "perspectives": [
                ReviewPerspective.ARCHITECTURE,
                ReviewPerspective.SECURITY,
            ],
        },
    ]

    all_results: Dict[str, List[ReviewResult]] = {}

    for doc in documents:
        doc_path = doc["path"]
        if not doc_path.exists():
            print(f"⚠️ Document not found: {doc_path}")
            continue

        doc_name = doc_path.name
        all_results[doc_name] = []

        for perspective in doc["perspectives"]:
            try:
                result = await review_document(
                    provider=provider,
                    document_path=doc_path,
                    review_type=doc["type"],
                    perspective=perspective,
                )
                all_results[doc_name].append(result)
                print_review_summary(f"{doc_name} ({perspective.value})", result)
            except Exception as e:
                print(f"❌ Error reviewing {doc_name}: {e}")

    return all_results


def print_aggregate_summary(all_results: Dict[str, List[ReviewResult]]) -> None:
    """
    Print aggregate summary across all documents.

    Args:
        all_results: Dictionary of review results
    """
    print(f"\n{'='*70}")
    print("AGGREGATE REVIEW SUMMARY")
    print(f"{'='*70}\n")

    total_critical = 0
    total_warning = 0
    total_info = 0
    total_feedback = 0
    avg_score = 0.0
    result_count = 0

    for doc_name, results in all_results.items():
        for result in results:
            total_critical += result.critical_count
            total_warning += result.warning_count
            total_info += result.info_count
            total_feedback += len(result.feedback_items)
            avg_score += result.overall_score
            result_count += 1

    if result_count > 0:
        avg_score /= result_count

    print(f"Documents Reviewed: {len(all_results)}")
    print(f"Total Reviews: {result_count}")
    print(f"Average Score: {avg_score:.1f}/100")
    print(f"Total Feedback Items: {total_feedback}")
    print(f"  🔴 Critical: {total_critical}")
    print(f"  🟡 Warning: {total_warning}")
    print(f"  ℹ️  Info: {total_info}")

    # Status determination
    if total_critical == 0 and total_warning <= 3:
        status = "✅ PASS - Ready for implementation"
    elif total_critical == 0:
        status = "⚠️ PASS WITH WARNINGS - Minor improvements recommended"
    else:
        status = "❌ NEEDS REVISION - Critical issues must be addressed"

    print(f"\nStatus: {status}")
    print(f"{'='*70}\n")


async def main() -> None:
    """Main entry point."""
    print("🔍 Week 2 Design Document Review")
    print("=" * 70)
    print("Perspectives: ARCHITECTURE, FEASIBILITY, SECURITY")
    print("=" * 70)

    # Estimate total review time
    docs_dir = project_root / "docs"
    documents = [
        (docs_dir / "API_SPECIFICATION.yaml", 2),
        (docs_dir / "STATE_MACHINE_DESIGN.md", 2),
        (docs_dir / "DATABASE_SCHEMA_DESIGN.md", 2),
    ]

    total_estimated_minutes = 0.0
    total_timeout_minutes = 0.0

    print("\n" + "=" * 70)
    print("TIME ESTIMATION")
    print("=" * 70)

    for doc_path, perspectives in documents:
        if doc_path.exists():
            estimate = estimate_from_file(str(doc_path), perspectives)
            total_estimated_minutes += estimate.estimated_minutes
            total_timeout_minutes += estimate.timeout_minutes

            print(f"\n{doc_path.name}:")
            print(f"  推定時間: {estimate.estimated_minutes}分")
            print(f"  タイムアウト: {estimate.timeout_minutes}分")
            print(f"  戦略: {estimate.strategy}")
            print(f"  {estimate.message}")
            if estimate.should_split:
                print(f"  ⚠️  {estimate.split_suggestion}")

    print(f"\n{'='*70}")
    print(f"合計推定時間: {total_estimated_minutes:.1f}分")
    print(f"合計タイムアウト: {total_timeout_minutes:.1f}分 (50% buffer)")
    print(f"{'='*70}\n")

    # Ask user confirmation
    print(f"⏱️  推定実行時間: {total_estimated_minutes:.1f}分")
    print("このレビューを実行しますか？ (y / n): ", end="")
    # Auto - proceed for now (in production, use input())
    print("y (auto - proceed)")
    print()

    try:
        all_results = await review_all_design_documents()
        print_aggregate_summary(all_results)

        # Exit code based on critical issues
        total_critical = sum(
            result.critical_count for results in all_results.values() for result in results
        )
        sys.exit(1 if total_critical > 0 else 0)

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
