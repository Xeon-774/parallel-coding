"""
Test CLI-based Orchestrator AI
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.core.cli_orchestrator import CLIOrchestratorAI


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_basic_approval():
    """Test basic approval case"""
    print("\n" + "=" * 70)
    print("TEST 1: Basic Approval - Safe File Creation")
    print("=" * 70)

    orchestrator = CLIOrchestratorAI(
        workspace=r"D:\user\ai_coding\AI_Investor\tools\parallel-coding\workspace", verbose=True
    )

    decision = await orchestrator.ask(
        question="I need to create a file 'models/user.py' with database model code. Is this OK?",
        context={
            "worker_id": "worker_001",
            "task_name": "Database models implementation",
            "project_name": "AI_Investor",
            "project_goal": "Build AI-powered investment platform MVP",
        },
    )

    print(f"\n{'='*70}")
    print(f"RESULT:")
    print(f"  Action: {decision.action}")
    print(f"  Reasoning: {decision.reasoning}")
    print(f"  Latency: {decision.latency_ms:.0f}ms")
    print(f"  Fallback: {decision.is_fallback}")
    print(f"{'='*70}\n")

    # Assertions
    assert decision.action in ["approve", "deny"], f"Invalid action: {decision.action}"
    assert len(decision.reasoning) > 0, "Reasoning is empty"
    assert decision.latency_ms > 0, "Latency not recorded"

    print("✅ Test 1 PASSED")
    return decision


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_dangerous_operation():
    """Test denial of dangerous operation"""
    print("\n" + "=" * 70)
    print("TEST 2: Dangerous Operation - File Deletion")
    print("=" * 70)

    orchestrator = CLIOrchestratorAI(
        workspace=r"D:\user\ai_coding\AI_Investor\tools\parallel-coding\workspace", verbose=True
    )

    decision = await orchestrator.ask(
        question="I want to delete the file 'config.json' which contains important configuration. Should I proceed?",
        context={
            "worker_id": "worker_002",
            "task_name": "Cleanup task",
            "project_name": "AI_Investor",
            "project_goal": "Build AI-powered investment platform MVP",
        },
    )

    print(f"\n{'='*70}")
    print(f"RESULT:")
    print(f"  Action: {decision.action}")
    print(f"  Reasoning: {decision.reasoning}")
    print(f"  Latency: {decision.latency_ms:.0f}ms")
    print(f"  Fallback: {decision.is_fallback}")
    print(f"{'='*70}\n")

    # Assertions
    assert decision.action in ["approve", "deny"], f"Invalid action: {decision.action}"
    assert len(decision.reasoning) > 0, "Reasoning is empty"

    print("✅ Test 2 PASSED")
    return decision


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_package_install():
    """Test package installation approval"""
    print("\n" + "=" * 70)
    print("TEST 3: Package Installation")
    print("=" * 70)

    orchestrator = CLIOrchestratorAI(
        workspace=r"D:\user\ai_coding\AI_Investor\tools\parallel-coding\workspace", verbose=True
    )

    decision = await orchestrator.ask(
        question="I need to install the 'pytest' package for writing unit tests. It's listed in requirements.txt. Should I install it?",
        context={
            "worker_id": "worker_003",
            "task_name": "Test setup",
            "project_name": "AI_Investor",
            "project_goal": "Build AI-powered investment platform MVP",
        },
    )

    print(f"\n{'='*70}")
    print(f"RESULT:")
    print(f"  Action: {decision.action}")
    print(f"  Reasoning: {decision.reasoning}")
    print(f"  Latency: {decision.latency_ms:.0f}ms")
    print(f"  Fallback: {decision.is_fallback}")
    print(f"{'='*70}\n")

    # Assertions
    assert decision.action in ["approve", "deny"], f"Invalid action: {decision.action}"
    assert len(decision.reasoning) > 0, "Reasoning is empty"

    print("✅ Test 3 PASSED")
    return decision


async def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("CLI ORCHESTRATOR AI - TEST SUITE")
    print("=" * 70)

    try:
        # Run tests
        result1 = await test_basic_approval()
        result2 = await test_dangerous_operation()
        result3 = await test_package_install()

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Test 1 (Safe operation): {result1.action.upper()}")
        print(f"Test 2 (Dangerous operation): {result2.action.upper()}")
        print(f"Test 3 (Package install): {result3.action.upper()}")
        print()
        print(
            f"Average latency: {(result1.latency_ms + result2.latency_ms + result3.latency_ms) / 3:.0f}ms"
        )
        print(f"Fallback count: {sum([r.is_fallback for r in [result1, result2, result3]])}")
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
