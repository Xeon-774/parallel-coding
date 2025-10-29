"""
Terminal Capture Validation Test (Phase 1.3.2)

Tests that raw_terminal.log is created and populated correctly
with actual worker output.

This is a critical validation test to confirm Phase 1.3 implementation.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure UTF-8 encoding
from orchestrator.utils.encoding_config import configure_console_encoding, safe_print

configure_console_encoding()

from orchestrator.config import OrchestratorConfig
from orchestrator.core.structured_logging import StructuredLogger
from orchestrator.core.worker.worker_manager import WorkerManager


def test_terminal_capture():
    """Validate that worker terminal output is captured to raw_terminal.log"""

    print("=" * 80)
    print("Phase 1.3.2 - Terminal Capture Validation Test")
    print("=" * 80)
    print()

    # Configuration
    config = OrchestratorConfig()
    workspace = project_root / "workspace" / "test_terminal_capture"
    config.workspace_root = str(workspace)
    config.execution_mode = "wsl"
    config.wsl_distribution = "Ubuntu-24.04"
    config.claude_command = "~/.local/bin/claude"
    config.nvm_path = "/usr/bin"

    # Prepare workspace
    workspace.mkdir(parents=True, exist_ok=True)

    # Logger
    logger = StructuredLogger(name="terminal_capture_test", log_dir=workspace, enable_console=True)

    print(f"[Test] Workspace: {workspace}")
    print(f"[Test] Execution Mode: {config.execution_mode}")
    print()

    # Initialize WorkerManager
    worker_manager = WorkerManager(
        config=config, logger=logger, user_approval_callback=None  # Auto-approve mode
    )

    # Simple test task
    task = {
        "name": "Terminal Capture Test",
        "prompt": """
You are testing terminal output capture.

Please perform these simple actions:
1. Print "Hello from Worker AI!"
2. Calculate: 10 + 20 = ?
3. Print "Test complete!"

Start now.
""",
    }

    try:
        print("[Test] Spawning worker...")
        worker_id = "terminal_capture_test"

        # Spawn worker
        session = worker_manager.spawn_worker(worker_id=worker_id, task=task)

        if not session:
            print("[ERROR] Failed to spawn worker")
            return False

        print(f"[Test] Worker spawned: {session.worker_id}")
        print(f"[Test] Expected log file: {session.raw_terminal_file}")
        print()

        # Check if raw_terminal.log was created
        if not session.raw_terminal_file:
            print("[ERROR] raw_terminal_file is None!")
            return False

        if not session.raw_terminal_file.exists():
            print("[ERROR] raw_terminal.log file was not created!")
            return False

        print("[SUCCESS] raw_terminal.log file created ✓")
        print()

        # Read initial content
        initial_content = session.raw_terminal_file.read_text(encoding="utf-8")
        print("[Test] Initial content:")
        print("-" * 80)
        safe_print(initial_content[:500])  # First 500 chars
        print("-" * 80)
        print()

        # Run interactive session
        print("[Test] Running interactive session...")
        result = worker_manager.run_interactive_session(session.worker_id)

        # Validation results
        print("\n" + "=" * 80)
        print("Validation Results")
        print("=" * 80)

        # Check 1: File still exists
        file_exists = session.raw_terminal_file.exists()
        print(f"✓ File exists: {file_exists}")

        # Check 2: File has content
        if file_exists:
            file_size = session.raw_terminal_file.stat().st_size
            print(f"✓ File size: {file_size} bytes")

            # Check 3: Read final content
            final_content = session.raw_terminal_file.read_text(encoding="utf-8")
            print(f"✓ Content length: {len(final_content)} characters")

            # Check 4: Content increased from initial
            content_grew = len(final_content) > len(initial_content)
            print(f"✓ Content grew during execution: {content_grew}")

            # Display final content preview
            print("\n[Test] Final content preview (last 1000 chars):")
            print("-" * 80)
            safe_print(final_content[-1000:])
            print("-" * 80)

            # Success criteria
            success = file_exists and file_size > 0 and content_grew and result.success

            print("\n" + "=" * 80)
            if success:
                print("[SUCCESS] ✓ Terminal capture working correctly!")
                print("- File created ✓")
                print("- Content captured ✓")
                print("- Worker executed successfully ✓")
            else:
                print("[WARNING] Terminal capture may have issues:")
                if not content_grew:
                    print("- Content did not grow during execution")
                if not result.success:
                    print("- Worker execution failed")
            print("=" * 80)

            return success

        else:
            print("[ERROR] File disappeared after execution!")
            return False

    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_terminal_capture()
    print()
    print("=" * 80)
    print(f"Test Result: {'PASSED ✓' if success else 'FAILED ✗'}")
    print("=" * 80)
    sys.exit(0 if success else 1)
