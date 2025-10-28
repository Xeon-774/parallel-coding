"""
Integration Test: Claude-Codex Collaboration

This script tests the real collaboration between Claude (orchestrator)
and Codex (worker) using the ClaudeCodexManager.

Test Scenario:
    1. Claude decomposes user task
    2. Claude generates detailed prompts with excellence_ai_standard
    3. Codex executes code generation
    4. Claude validates output
    5. Report results

Usage:
    python test_integration_claude_codex.py

Author: Claude (Sonnet 4.5)
Created: 2025-10-27
"""

import asyncio
import sys
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.core.manager.claude_codex_manager import (
    ClaudeCodexManager,
    ClaudeCodexManagerConfig,
    CodexProviderConfig,
)


async def test_simple_task():
    """Test simple task: email validator"""
    print("=" * 70)
    print("🧪 Integration Test: Claude-Codex Collaboration")
    print("=" * 70)
    print()

    try:
        # Step 1: Initialize Manager
        print("📦 Step 1: Initializing Claude-Codex Manager...")
        # Create test workspace
        workspace_dir = Path("./test_workspace")
        workspace_dir.mkdir(parents=True, exist_ok=True)

        config = ClaudeCodexManagerConfig(
            codex_provider_config=CodexProviderConfig(
                timeout_seconds=60,  # 1 minute timeout
                max_retries=2,
                workspace_root=str(workspace_dir.absolute())
            ),
            enable_validation=True,
            enable_websocket_events=False,
            validation_strict_mode=False
        )

        manager = ClaudeCodexManager(config)
        print("✅ Manager initialized successfully")
        print(f"   Codex available: {manager.codex_provider.is_available}")
        print()

        # Step 2: Define test task
        print("📝 Step 2: Defining test task...")
        user_task = (
            "Write a Python function that validates email addresses using regex. "
            "Include comprehensive docstrings with examples, type hints, and "
            "proper error handling."
        )
        print(f"   Task: {user_task}")
        print()

        # Step 3: Execute task
        print("🚀 Step 3: Executing task (Claude orchestrates, Codex generates)...")
        print("   This may take 30-60 seconds...")
        print()

        results = await manager.execute_task(user_task)

        # Step 4: Analyze results
        print("=" * 70)
        print("📊 Step 4: Results Analysis")
        print("=" * 70)
        print()

        for i, result in enumerate(results, 1):
            print(f"--- Subtask {i}: {result.task.description[:50]}... ---")
            print(f"   Complexity: {result.task.complexity.value}")
            print(f"   Execution time: {result.execution_time_seconds:.2f}s")
            print(f"   Validated: {'✅ PASS' if result.validated else '❌ FAIL'}")

            if result.validation_errors:
                print(f"   Errors ({len(result.validation_errors)}):")
                for error in result.validation_errors[:3]:
                    print(f"      - {error}")

            if result.validation_warnings:
                print(f"   Warnings ({len(result.validation_warnings)}):")
                for warning in result.validation_warnings[:3]:
                    print(f"      - {warning}")

            print()

            # Show output snippet
            if result.codex_response.is_success:
                output = result.codex_response.output
                print("   Generated Output (first 300 chars):")
                print("   " + "-" * 66)
                for line in output[:300].split('\n')[:10]:
                    print(f"   {line}")
                if len(output) > 300:
                    print("   ...")
                print()

        # Step 5: Summary
        print("=" * 70)
        print("📈 Test Summary")
        print("=" * 70)
        total_tasks = len(results)
        validated_tasks = sum(1 for r in results if r.validated)
        success_rate = (validated_tasks / total_tasks * 100) if total_tasks > 0 else 0

        print(f"   Total subtasks: {total_tasks}")
        print(f"   Validated: {validated_tasks}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Total execution time: {sum(r.execution_time_seconds for r in results):.2f}s")
        print()

        # Final verdict
        if success_rate >= 80:
            print("✅ INTEGRATION TEST PASSED")
            print("   Claude-Codex collaboration is working correctly!")
        else:
            print("⚠️  INTEGRATION TEST NEEDS REVIEW")
            print(f"   Success rate {success_rate:.1f}% is below 80% threshold")

        print("=" * 70)

        return results

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def main():
    """Main test execution"""
    print()
    print("🤖 Testing Claude (Orchestrator) + Codex (Worker) Collaboration")
    print()

    results = await test_simple_task()

    print()
    print("✅ Integration test completed successfully!")
    print()

    # Save results for analysis
    print("💾 Saving results...")
    import json
    from datetime import datetime

    report = {
        "timestamp": datetime.now().isoformat(),
        "test_type": "claude_codex_integration",
        "results": [
            {
                "task_description": r.task.description,
                "complexity": r.task.complexity.value,
                "validated": r.validated,
                "execution_time_seconds": r.execution_time_seconds,
                "errors": r.validation_errors,
                "warnings": r.validation_warnings,
                "output_length": len(r.codex_response.output),
            }
            for r in results
        ]
    }

    report_file = Path("./test_results/claude_codex_integration.json")
    report_file.parent.mkdir(parents=True, exist_ok=True)

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"   Report saved: {report_file}")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        sys.exit(1)
