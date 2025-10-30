"""
Test script to verify dialogue logging completeness

This test will:
1. Create a simple task for a worker
2. Verify that all dialogue (both directions) is logged
3. Check if logs are persisted to files
"""

import sys
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.config import OrchestratorConfig
from orchestrator.core.structured_logging import LogCategory, get_logger
from orchestrator.core.worker.worker_manager import WorkerManager


def test_dialogue_logging():
    """Test that all dialogue is logged"""

    print("=" * 70)
    print("DIALOGUE LOGGING TEST")
    print("=" * 70)

    # Setup
    config = OrchestratorConfig()
    config.workspace_root = r"D:\user\ai_coding\AI_Investor\tools\parallel - coding\test_workspace"

    # Create workspace
    workspace = Path(config.workspace_root)
    workspace.mkdir(parents=True, exist_ok=True)

    # Setup logger
    logger = get_logger("test_dialogue", category=LogCategory.WORKER, log_dir=workspace / "logs")

    # Create worker manager
    manager = WorkerManager(
        config=config,
        logger=logger,
        user_approval_callback=lambda req: True,  # Auto - approve for test
    )

    # Create simple task
    test_task = {
        "name": "Hello World Test",
        "prompt": "Print 'Hello, World!' and explain what you did.",
    }

    print(f"\n✓ Starting test with task: {test_task['name']}")
    print(f"✓ Workspace: {workspace}")

    # Spawn worker
    session = manager.spawn_worker("test_001", test_task, timeout=60)

    if not session:
        print("\n❌ Failed to spawn worker")
        return False

    print("\n✓ Worker spawned successfully")

    # Run interactive session
    print("\n✓ Running interactive session...")
    result = manager.run_interactive_session("worker_test_001", max_iterations=10)

    # Analyze results
    print("\n" + "=" * 70)
    print("RESULTS ANALYSIS")
    print("=" * 70)

    print(f"\nTask: {result.name}")
    print(f"Success: {result.success}")
    print(f"Duration: {result.duration:.2f}s")
    print(f"\nOutput length: {len(result.output)} characters")
    print(f"Output lines: {result.output.count(chr(10)) + 1}")

    # Check if output is saved
    print("\n" + "-" * 70)
    print("SAVED FILES CHECK")
    print("-" * 70)

    workspace_files = list(workspace.rglob("*"))
    print(f"\nTotal files in workspace: {len(workspace_files)}")

    for file in workspace_files:
        if file.is_file():
            size = file.stat().st_size
            print(f"  - {file.relative_to(workspace)}: {size:,} bytes")

    # Check for dialogue transcript
    worker_dir = workspace / "worker_test_001"
    if worker_dir.exists():
        print(f"\n✓ Worker directory exists: {worker_dir}")
        worker_files = list(worker_dir.iterdir())
        for wf in worker_files:
            if wf.is_file():
                print(f"  - {wf.name}: {wf.stat().st_size:,} bytes")
    else:
        print(f"\n❌ Worker directory NOT found: {worker_dir}")

    # Print output preview
    print("\n" + "-" * 70)
    print("OUTPUT PREVIEW (first 500 chars)")
    print("-" * 70)
    print(result.output[:500])
    if len(result.output) > 500:
        print(f"\n... (truncated, total {len(result.output)} chars)")

    # Assessment
    print("\n" + "=" * 70)
    print("ASSESSMENT")
    print("=" * 70)

    issues = []

    # Check 1: Was output captured?
    if not result.output:
        issues.append("❌ No output captured")
    else:
        print("✅ Output was captured")

    # Check 2: Is there a dialogue transcript file?
    transcript_file = worker_dir / "dialogue.log" if worker_dir.exists() else None
    if transcript_file and transcript_file.exists():
        print("✅ Dialogue transcript file exists")
    else:
        issues.append("❌ No dialogue transcript file found")

    # Check 3: Are logs being saved?
    log_dir = workspace / "logs"
    if log_dir.exists() and list(log_dir.glob("*.log")):
        print("✅ Log files exist")
    else:
        issues.append("⚠️  No structured log files found")

    # Summary
    print("\n" + "=" * 70)
    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
        print("\n❌ TEST REVEALED GAPS IN LOGGING")
    else:
        print("✅ ALL CHECKS PASSED")
    print("=" * 70)

    return len(issues) == 0


if __name__ == "__main__":
    try:
        success = test_dialogue_logging()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
