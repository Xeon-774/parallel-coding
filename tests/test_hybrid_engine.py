"""
Test Hybrid Decision Engine

Tests the combination of rule - based safety engine + AI judgment + template fallback.
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.core.hybrid_engine import (
    ConfirmationRequest,
    ConfirmationType,
    HybridDecisionEngine,
)


@pytest.fixture
def test_workspace(tmp_path):
    """Create a temporary workspace for testing"""
    workspace = tmp_path / "test_workspace"
    workspace.mkdir(exist_ok=True)
    return workspace


@pytest.mark.asyncio
async def test_rule_based_approval(test_workspace):
    """Test rule - based approval for safe operations"""
    print("\n" + "=" * 70)
    print("TEST 1: Rule - based Approval - Safe File Creation")
    print("=" * 70)

    engine = HybridDecisionEngine(
        workspace_root=test_workspace,
        verbose=True,
    )

    request = ConfirmationRequest(
        confirmation_type=ConfirmationType.FILE_WRITE,
        message="I want to create a file 'models / user.py' with database model code.",
        details={"file": "workspace / models / user.py"},
    )

    decision = await engine.decide("worker_001", request)

    print(f"\n{'='*70}")
    print("RESULT:")
    print(f"  Action: {decision.action}")
    print(f"  Decided by: {decision.decided_by}")
    print(f"  Reasoning: {decision.reasoning}")
    print(f"  Latency: {decision.latency_ms:.1f}ms")
    print(f"  Fallback: {decision.is_fallback}")
    print(f"{'='*70}\n")

    # Assertions
    assert decision.action == "approve", f"Expected approve, got {decision.action}"
    assert decision.decided_by == "rules", f"Expected rules, got {decision.decided_by}"
    assert decision.latency_ms < 10, f"Rules should be fast, got {decision.latency_ms}ms"
    assert not decision.is_fallback, "Should not be fallback"

    print("✅ Test 1 PASSED")
    return decision


@pytest.mark.asyncio
async def test_rule_based_denial(test_workspace):
    """Test rule - based denial for dangerous operations"""
    print("\n" + "=" * 70)
    print("TEST 2: Rule - based Denial - Important File Deletion")
    print("=" * 70)

    engine = HybridDecisionEngine(
        workspace_root=test_workspace,
        verbose=True,
    )

    request = ConfirmationRequest(
        confirmation_type=ConfirmationType.FILE_DELETE,
        message="I want to delete config.py",
        details={"file": "config.py"},
    )

    decision = await engine.decide("worker_002", request)

    print(f"\n{'='*70}")
    print("RESULT:")
    print(f"  Action: {decision.action}")
    print(f"  Decided by: {decision.decided_by}")
    print(f"  Reasoning: {decision.reasoning}")
    print(f"  Latency: {decision.latency_ms:.1f}ms")
    print(f"  Fallback: {decision.is_fallback}")
    print(f"{'='*70}\n")

    # Assertions
    assert decision.action == "deny", f"Expected deny, got {decision.action}"
    assert decision.decided_by == "rules", f"Expected rules, got {decision.decided_by}"
    assert decision.latency_ms < 10, f"Rules should be fast, got {decision.latency_ms}ms"
    assert not decision.is_fallback, "Should not be fallback"

    print("✅ Test 2 PASSED")
    return decision


@pytest.mark.asyncio
async def test_dangerous_command_denial(test_workspace):
    """Test rule - based denial for dangerous commands"""
    print("\n" + "=" * 70)
    print("TEST 3: Rule - based Denial - Dangerous Command")
    print("=" * 70)

    engine = HybridDecisionEngine(
        workspace_root=test_workspace,
        verbose=True,
    )

    request = ConfirmationRequest(
        confirmation_type=ConfirmationType.COMMAND_EXECUTE,
        message="I want to run 'rm -rf /' to clean up",
        details={"command": "rm -rf /"},
    )

    decision = await engine.decide("worker_003", request)

    print(f"\n{'='*70}")
    print("RESULT:")
    print(f"  Action: {decision.action}")
    print(f"  Decided by: {decision.decided_by}")
    print(f"  Reasoning: {decision.reasoning}")
    print(f"  Latency: {decision.latency_ms:.1f}ms")
    print(f"  Fallback: {decision.is_fallback}")
    print(f"{'='*70}\n")

    # Assertions
    assert decision.action == "deny", f"Expected deny, got {decision.action}"
    assert decision.decided_by == "rules", f"Expected rules, got {decision.decided_by}"
    assert decision.latency_ms < 10, f"Rules should be fast, got {decision.latency_ms}ms"

    print("✅ Test 3 PASSED")
    return decision


@pytest.mark.asyncio
async def test_ai_judgment(test_workspace):
    """Test AI judgment for complex decisions"""
    print("\n" + "=" * 70)
    print("TEST 4: AI Judgment - Complex Refactoring Decision")
    print("=" * 70)

    engine = HybridDecisionEngine(
        workspace_root=test_workspace,
        verbose=True,
    )

    request = ConfirmationRequest(
        confirmation_type=ConfirmationType.GENERAL,
        message="I want to refactor the database connection pooling to use asyncio. This will require modifying several files. Is this a good idea?",
        details={"scope": "multiple files", "complexity": "high"},
    )

    decision = await engine.decide("worker_004", request)

    print(f"\n{'='*70}")
    print("RESULT:")
    print(f"  Action: {decision.action}")
    print(f"  Decided by: {decision.decided_by}")
    print(f"  Reasoning: {decision.reasoning[:200]}...")
    print(f"  Latency: {decision.latency_ms:.1f}ms")
    print(f"  Fallback: {decision.is_fallback}")
    print(f"{'='*70}\n")

    # Assertions
    assert decision.action in ["approve", "deny"], f"Invalid action: {decision.action}"
    assert decision.decided_by in [
        "ai",
        "template",
    ], f"Expected ai or template, got {decision.decided_by}"
    # AI should take more time than rules
    if decision.decided_by == "ai":
        assert decision.latency_ms > 100, f"AI should take more time, got {decision.latency_ms}ms"

    print("✅ Test 4 PASSED")
    return decision


@pytest.mark.asyncio
async def test_package_install_from_requirements(test_workspace):
    """Test package installation from requirements.txt"""
    print("\n" + "=" * 70)
    print("TEST 5: Package Install from requirements.txt")
    print("=" * 70)

    engine = HybridDecisionEngine(
        workspace_root=test_workspace, verbose=True
    )

    # This package is in requirements.txt
    request = ConfirmationRequest(
        confirmation_type=ConfirmationType.PACKAGE_INSTALL,
        message="I need to install pytest for running tests",
        details={"package": "pytest"},
    )

    decision = await engine.decide("worker_005", request)

    print(f"\n{'='*70}")
    print("RESULT:")
    print(f"  Action: {decision.action}")
    print(f"  Decided by: {decision.decided_by}")
    print(f"  Reasoning: {decision.reasoning}")
    print(f"  Latency: {decision.latency_ms:.1f}ms")
    print(f"  Fallback: {decision.is_fallback}")
    print(f"{'='*70}\n")

    # Assertions
    assert decision.action == "approve", f"Expected approve, got {decision.action}"
    assert decision.decided_by == "rules", f"Expected rules, got {decision.decided_by}"
    assert decision.latency_ms < 10, f"Rules should be fast, got {decision.latency_ms}ms"

    print("✅ Test 5 PASSED")
    return decision


@pytest.mark.asyncio
async def test_statistics(test_workspace):
    """Test statistics tracking"""
    print("\n" + "=" * 70)
    print("TEST 6: Statistics Tracking")
    print("=" * 70)

    engine = HybridDecisionEngine(
        workspace_root=test_workspace,
        verbose=False,  # Disable verbose for cleaner output
    )

    # Run multiple decisions
    requests = [
        # Rule - based approvals
        ConfirmationRequest(
            confirmation_type=ConfirmationType.FILE_WRITE,
            message="Create file A",
            details={"file": "workspace / a.py"},
        ),
        ConfirmationRequest(
            confirmation_type=ConfirmationType.FILE_READ,
            message="Read file B",
            details={"file": "workspace / b.py"},
        ),
        # Rule - based denials
        ConfirmationRequest(
            confirmation_type=ConfirmationType.FILE_DELETE,
            message="Delete config",
            details={"file": "config.py"},
        ),
        ConfirmationRequest(
            confirmation_type=ConfirmationType.FILE_DELETE,
            message="Delete .env",
            details={"file": ".env"},
        ),
    ]

    for i, request in enumerate(requests):
        decision = await engine.decide(f"worker_{i:03d}", request)
        print(f"  Decision {i + 1}: {decision.decided_by} -> {decision.action}")

    # Get statistics
    stats = engine.get_stats()

    print(f"\n{'='*70}")
    print("STATISTICS:")
    print(f"  Total decisions: {stats['total_decisions']}")
    print(f"  Rules decisions: {stats['rules_decisions']} ({stats['rules_percentage']:.1f}%)")
    print(f"  AI decisions: {stats['ai_decisions']}")
    print(f"  Template fallbacks: {stats['template_fallbacks']}")
    print(f"  Average latency: {stats['average_latency_ms']:.1f}ms")
    print(f"{'='*70}\n")

    # Assertions
    assert stats["total_decisions"] == 4, f"Expected 4 decisions, got {stats['total_decisions']}"
    assert (
        stats["rules_decisions"] == 4
    ), f"All should be rule - based, got {stats['rules_decisions']}"
    assert stats["ai_decisions"] == 0, f"No AI decisions expected, got {stats['ai_decisions']}"
    assert (
        stats["template_fallbacks"] == 0
    ), f"No fallbacks expected, got {stats['template_fallbacks']}"
    assert stats["rules_percentage"] == 100.0, f"Expected 100%, got {stats['rules_percentage']}"
    assert (
        stats["average_latency_ms"] < 10
    ), f"Rules should be fast, got {stats['average_latency_ms']}ms"

    print("✅ Test 6 PASSED")
    return stats


async def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("HYBRID ENGINE TEST SUITE")
    print("=" * 70)

    try:
        # Run tests
        result1 = await test_rule_based_approval()
        result2 = await test_rule_based_denial()
        result3 = await test_dangerous_command_denial()
        result4 = await test_ai_judgment()
        result5 = await test_package_install_from_requirements()
        result6 = await test_statistics()

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Test 1 (Rule approval): {result1.action.upper()} by {result1.decided_by}")
        print(f"Test 2 (Rule denial): {result2.action.upper()} by {result2.decided_by}")
        print(f"Test 3 (Dangerous command): {result3.action.upper()} by {result3.decided_by}")
        print(f"Test 4 (AI judgment): {result4.action.upper()} by {result4.decided_by}")
        print(f"Test 5 (Package install): {result5.action.upper()} by {result5.decided_by}")
        print(f"Test 6 (Statistics): {result6['total_decisions']} decisions tracked")
        print("=" * 70)
        print("\n✅ ALL TESTS PASSED\n")

        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
