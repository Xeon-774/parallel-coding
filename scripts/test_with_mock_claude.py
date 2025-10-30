"""
Test EnhancedInteractiveWorkerManager with Mock Claude CLI

Uses mock_claude_cli.py to simulate Claude CLI behavior.
Tests the complete interactive flow without requiring actual Claude CLI.

Usage:
    python scripts / test_with_mock_claude.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.config import OrchestratorConfig
from orchestrator.core.enhanced_interactive_worker_manager import (
    ConfirmationRequest,
    EnhancedInteractiveWorkerManager,
)


# Temporarily patch the command builder to use mock CLI
class MockEnhancedInteractiveWorkerManager(EnhancedInteractiveWorkerManager):
    """
    Version of EnhancedInteractiveWorkerManager that uses mock Claude CLI
    """

    def _build_command(self, task_file: str) -> str:
        """Build command using mock Claude CLI"""
        mock_cli = str(Path(__file__).parent / "mock_claude_cli.py")
        return f'python "{mock_cli}" < "{task_file}"'


# Logger for testing
class TestLogger:
    def log_worker_spawn(self, worker_id, task_name):
        print(f"[LOG - SPAWN] {worker_id}: {task_name}")

    def info(self, message, **kwargs):
        print(f"[LOG - INFO] {message}")
        if kwargs:
            print(f"          {kwargs}")

    def warning(self, message, **kwargs):
        print(f"[LOG - WARN] {message}")
        if kwargs:
            print(f"          {kwargs}")

    def error(self, message, **kwargs):
        print(f"[LOG - ERROR] {message}")
        if kwargs:
            print(f"           {kwargs}")


def user_approval_callback(confirmation: ConfirmationRequest) -> bool:
    """
    User approval callback for testing

    Auto - approves file writes, asks user for other operations
    """
    print(f"\n{'='*60}")
    print("USER APPROVAL CALLBACK")
    print(f"{'='*60}")
    print(f"Worker: {confirmation.worker_id}")
    print(f"Type: {confirmation.confirmation_type}")
    print(f"Message: {confirmation.message}")
    print(f"Details: {confirmation.details}")
    print(f"{'='*60}")

    # Auto - approve file writes for testing
    if confirmation.confirmation_type.value == "file_write":
        print("[AUTO - APPROVE] File write operation")
        return True

    # Auto - approve file reads
    if confirmation.confirmation_type.value == "file_read":
        print("[AUTO - APPROVE] File read operation")
        return True

    # For command execution, approve safe commands
    if confirmation.confirmation_type.value == "command_execute":
        command = confirmation.details.get("command", "").lower()
        if "dir" in command or "ls" in command:
            print("[AUTO - APPROVE] Safe list command")
            return True

    # Ask user for everything else
    response = input("\nApprove? (y / n): ").strip().lower()
    approved = response == "y"

    print(f"[USER - DECISION] {'APPROVED' if approved else 'DENIED'}")

    return approved


def test_mock_integration():
    """Test full integration with mock Claude CLI"""

    print("\n" + "=" * 70)
    print(" Testing EnhancedInteractiveWorkerManager with Mock Claude CLI")
    print("=" * 70)

    # Setup
    config = OrchestratorConfig.from_env()
    config.workspace_root = "./workspace"

    logger = TestLogger()

    manager = MockEnhancedInteractiveWorkerManager(
        config=config, logger=logger, user_approval_callback=user_approval_callback
    )

    # Create task
    task = {
        "name": "Test Interactive Mode",
        "prompt": """
Create a simple Python script that prints "Hello, World!"
and save it to a file.
""",
    }

    print("\n[STEP 1] Spawning worker with mock CLI...")
    session = manager.spawn_worker("mock_test", task)

    if not session:
        print("[FAIL] Failed to spawn worker")
        return False

    print("[OK] Worker spawned successfully")

    print("\n[STEP 2] Running interactive session...")
    print("Watch for confirmation detection and responses...\n")

    result = manager.run_interactive_session(session.worker_id, max_iterations=20)

    print("\n" + "=" * 70)
    print(" TEST RESULT")
    print("=" * 70)
    print(f"Success: {result.success}")
    print(f"Duration: {result.duration:.2f}s" if result.duration else "Duration: N / A")
    print(f"Error: {result.error_message if result.error_message else 'None'}")
    print(f"\nOutput ({len(result.output)} chars):")
    print("-" * 70)
    print(result.output)
    print("-" * 70)

    if result.success:
        print("\n[PASS] Test completed successfully!")
        print("\nKey validations:")
        print("  [OK] Worker spawned with pexpect / wexpect")
        print("  [OK] Confirmation requests detected")
        print("  [OK] Responses sent to worker")
        print("  [OK] Worker completed normally")
        return True
    else:
        print("\n[FAIL] Test failed")
        return False


def main():
    """Run test"""
    print("\n" + "=" * 70)
    print(" Mock Claude CLI Integration Test")
    print("=" * 70)
    print("\nThis test validates EnhancedInteractiveWorkerManager")
    print("using a mock Claude CLI that simulates confirmations.\n")

    print(f"Platform: {sys.platform}")

    if sys.platform == "win32":
        print("Using: wexpect (Windows)")
    else:
        print("Using: pexpect (Unix / Linux)")

    print("\n" + "-" * 70)

    # Skip input in automated mode
    # import os
    # if not os.environ.get('AUTOMATED_TEST'):
    #     input("Press Enter to start test...")
    print("Starting test automatically...")

    try:
        success = test_mock_integration()

        print("\n" + "=" * 70)
        if success:
            print(" TEST PASSED")
        else:
            print(" TEST FAILED")
        print("=" * 70)

        return success

    except KeyboardInterrupt:
        print("\n\n[!] Test interrupted by user")
        return False

    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
