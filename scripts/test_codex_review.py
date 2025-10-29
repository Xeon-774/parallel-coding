"""
Test script for Codex document review functionality.

This script demonstrates the review system by reviewing project documents
with Codex from multiple perspectives.

Usage:
    python scripts/test_codex_review.py
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
from orchestrator.core.hierarchical.job_orchestrator import (
    HierarchicalJobOrchestrator,
)
from orchestrator.core.worker.codex_executor import (
    create_codex_executor_from_config,
)


async def main():
    """Main test function"""
    print("=" * 80)
    print("Codex Document Review System - Test Execution")
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

    # Create orchestrator and register provider
    print("4. Setting up orchestrator...")
    orchestrator = HierarchicalJobOrchestrator()
    orchestrator.register_review_provider(codex_provider, set_as_default=True)
    available_providers = orchestrator.get_available_review_providers()
    print(f"   - Available providers: {available_providers}")
    print()

    # Test 1: Review ROADMAP.md from Feasibility perspective
    print("=" * 80)
    print("TEST 1: Reviewing ROADMAP.md (Feasibility perspective)")
    print("=" * 80)
    print()

    roadmap_path = project_root / "docs" / "ROADMAP.md"
    if not roadmap_path.exists():
        print(f"⚠️  ROADMAP.md not found at {roadmap_path}")
        print("   Trying alternative location...")
        roadmap_path = project_root / "tools" / "parallel-coding" / "docs" / "ROADMAP.md"
        if not roadmap_path.exists():
            print(f"⚠️  ROADMAP.md not found at {roadmap_path}")
            print("   Skipping ROADMAP.md review")
        else:
            await review_document(
                orchestrator,
                roadmap_path,
                ReviewType.ROADMAP,
                ReviewPerspective.FEASIBILITY,
            )
    else:
        await review_document(
            orchestrator,
            roadmap_path,
            ReviewType.ROADMAP,
            ReviewPerspective.FEASIBILITY,
        )

    print()

    # Test 2: Review ARCHITECTURE.md from Architecture perspective
    print("=" * 80)
    print("TEST 2: Reviewing ARCHITECTURE.md (Architecture perspective)")
    print("=" * 80)
    print()

    arch_path = project_root / "docs" / "ARCHITECTURE.md"
    if not arch_path.exists():
        print(f"⚠️  ARCHITECTURE.md not found at {arch_path}")
        print("   Trying alternative location...")
        arch_path = project_root / "tools" / "parallel-coding" / "docs" / "ARCHITECTURE.md"
        if not arch_path.exists():
            # Try workspace location
            arch_path = (
                project_root
                / "tools"
                / "parallel-coding"
                / "workspace"
                / "worker_2"
                / "docs"
                / "ARCHITECTURE.md"
            )
            if not arch_path.exists():
                print(f"⚠️  ARCHITECTURE.md not found at {arch_path}")
                print("   Skipping ARCHITECTURE.md review")
            else:
                await review_document(
                    orchestrator,
                    arch_path,
                    ReviewType.ARCHITECTURE,
                    ReviewPerspective.ARCHITECTURE,
                )
        else:
            await review_document(
                orchestrator,
                arch_path,
                ReviewType.ARCHITECTURE,
                ReviewPerspective.ARCHITECTURE,
            )
    else:
        await review_document(
            orchestrator,
            arch_path,
            ReviewType.ARCHITECTURE,
            ReviewPerspective.ARCHITECTURE,
        )

    print()
    print("=" * 80)
    print("Review Tests Complete!")
    print("=" * 80)


async def review_document(
    orchestrator: HierarchicalJobOrchestrator,
    document_path: Path,
    review_type: ReviewType,
    perspective: ReviewPerspective,
):
    """Review a single document"""
    print(f"Document: {document_path}")
    print(f"Type: {review_type.value}")
    print(f"Perspective: {perspective.value}")
    print()

    # Create request
    request = ReviewRequest(
        document_path=str(document_path),
        review_type=review_type,
        perspective=perspective,
        context={
            "project": "AI_Investor - Parallel Coding System",
            "standard": "excellence_ai_standard",
        },
    )

    print("Executing review (this may take 1-5 minutes)...")
    print("Codex is analyzing the document...")
    print()

    # Execute review
    try:
        result = await orchestrator.review_document(request, provider="codex")

        # Display results
        print(f"✓ Review completed in {result.execution_time_seconds:.1f}s")
        print()
        print(f"Status: {result.status.value}")
        print(f"Overall Score: {result.overall_score:.1f}/100")
        print()

        if result.metadata.get("usage"):
            usage = result.metadata["usage"]
            print(f"Token Usage:")
            print(f"  - Input: {usage['input_tokens']:,} tokens")
            print(f"  - Output: {usage['output_tokens']:,} tokens")
            print()

        # Display feedback summary
        print(f"Feedback Summary:")
        print(f"  - Total items: {len(result.feedbacks)}")
        print(f"  - Critical: {len(result.critical_issues)}")
        print(f"  - Warnings: {len(result.warnings)}")
        print(f"  - Info: {len(result.info_items)}")
        print()

        # Display critical issues
        if result.critical_issues:
            print("🚨 Critical Issues:")
            for i, feedback in enumerate(result.critical_issues, 1):
                line_info = f"[Line {feedback.line_number}] " if feedback.line_number else ""
                print(f"  {i}. {line_info}{feedback.message}")
                if feedback.suggestion:
                    print(f"     → Suggestion: {feedback.suggestion}")
            print()

        # Display warnings
        if result.warnings:
            print("⚠️  Warnings:")
            for i, feedback in enumerate(result.warnings, 1):
                line_info = f"[Line {feedback.line_number}] " if feedback.line_number else ""
                print(f"  {i}. {line_info}{feedback.message}")
                if feedback.suggestion:
                    print(f"     → Suggestion: {feedback.suggestion}")
            print()

        # Display info items (limited to 5)
        if result.info_items:
            print("ℹ️  Information:")
            for i, feedback in enumerate(result.info_items[:5], 1):
                line_info = f"[Line {feedback.line_number}] " if feedback.line_number else ""
                print(f"  {i}. {line_info}{feedback.message}")
            if len(result.info_items) > 5:
                print(f"  ... and {len(result.info_items) - 5} more")
            print()

        # Show error if failed
        if result.error_message:
            print(f"❌ Error: {result.error_message}")
            print()

    except Exception as e:
        print(f"❌ Review failed with exception: {str(e)}")
        import traceback

        traceback.print_exc()
        print()


if __name__ == "__main__":
    asyncio.run(main())
