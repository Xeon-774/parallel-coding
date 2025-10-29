"""
Test Script for Enhanced Interactive Worker Manager

This script tests the pexpect / wexpect - based interactive mode with actual Claude CLI.
It captures and logs all confirmation requests to help tune pattern matching.

Usage:
    python scripts / test_enhanced_interactive.py
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.config import OrchestratorConfig
from orchestrator.core.enhanced_interactive_worker_manager import (
    ConfirmationRequest,
    EnhancedInteractiveWorkerManager,
)


# Logger for testing
class TestLogger:
    """Simple logger that prints and saves to file"""

    def __init__(self, log_file: str):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _log(self, level: str, message: str, **kwargs):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        if kwargs:
            log_line += f" | {kwargs}"

        print(log_line)

        with open(self.log_file, "a", encoding="utf - 8") as f:
            f.write(log_line + "\n")

    def log_worker_spawn(self, worker_id, task_name):
        self._log("SPAWN", f"{worker_id}: {task_name}")

    def info(self, message, **kwargs):
        self._log("INFO", message, **kwargs)

    def warning(self, message, **kwargs):
        self._log("WARN", message, **kwargs)

    def error(self, message, **kwargs):
        self._log("ERROR", message, **kwargs)


def user_approval_callback(confirmation: ConfirmationRequest) -> bool:
    """
    User approval callback for testing

    Logs all confirmation details for analysis
    """
    print("\n" + "=" * 70)
    print("USER APPROVAL REQUIRED")
    print("=" * 70)
    print(f"Worker: {confirmation.worker_id}")
    print(f"Type: {confirmation.confirmation_type}")
    print(f"Message: {confirmation.message}")
    print(f"Details: {confirmation.details}")
    print(f"Timestamp: {confirmation.timestamp}")
    print("=" * 70)

    # Save to log for analysis
    log_file = Path("workspace / confirmation_requests.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, "a", encoding="utf - 8") as f:
        f.write("\n" + "=" * 70 + "\n")
        f.write(
            f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(confirmation.timestamp))}\n"
        )
        f.write(f"Worker: {confirmation.worker_id}\n")
        f.write(f"Type: {confirmation.confirmation_type}\n")
        f.write(f"Message: {confirmation.message}\n")
        f.write(f"Details: {confirmation.details}\n")
        f.write("=" * 70 + "\n")

    # For testing, auto - approve safe operations
    if confirmation.confirmation_type.value in ["file_write", "file_read", "package_install"]:
        print("[AUTO - APPROVE] Safe operation")
        return True

    # Ask user for dangerous operations
    response = input("\nApprove this operation? (y / n): ").strip().lower()
    approved = response == "y"

    print(f"[USER - DECISION] {'APPROVED' if approved else 'DENIED'}")

    return approved


def test_1_simple_file_creation():
    """Test 1: Simple file creation (should be auto - approved)"""
    print("\n" + "=" * 70)
    print("TEST 1: Simple File Creation")
    print("=" * 70)

    config = OrchestratorConfig.from_env()
    config.workspace_root = "./workspace"

    logger = TestLogger("workspace / test_enhanced_interactive.log")

    manager = EnhancedInteractiveWorkerManager(
        config=config, logger=logger, user_approval_callback=user_approval_callback
    )

    task = {
        "name": "Create Hello World Script",
        "prompt": """
Create a simple Python script that:
1. Prints "Hello, World!"
2. Save it to workspace / worker_test_1 / hello.py

Please proceed with creating the file.
""",
    }

    print("\n[SPAWNING] Worker for Test 1...")
    session = manager.spawn_worker("test_1", task)

    if session:
        print("[OK] Worker spawned successfully")
        print("\n[RUNNING] Interactive session...")

        result = manager.run_interactive_session(session.worker_id)

        print("\n" + "=" * 70)
        print("TEST 1 RESULT")
        print("=" * 70)
        print(f"Success: {result.success}")
        print(f"Duration: {result.duration:.1f}s" if result.duration else "Duration: N / A")
        print(f"Error: {result.error_message}" if result.error_message else "Error: None")
        print(f"Output length: {len(result.output)} characters")

        if result.success:
            print("\n[PASS] Test 1 completed successfully!")
        else:
            print("\n[FAIL] Test 1 failed")

        return result.success
    else:
        print("\n[ERROR] Failed to spawn worker")
        return False


def test_2_command_execution():
    """Test 2: Command execution (should require approval)"""
    print("\n" + "=" * 70)
    print("TEST 2: Command Execution")
    print("=" * 70)

    config = OrchestratorConfig.from_env()
    config.workspace_root = "./workspace"

    logger = TestLogger("workspace / test_enhanced_interactive.log")

    manager = EnhancedInteractiveWorkerManager(
        config=config, logger=logger, user_approval_callback=user_approval_callback
    )

    task = {
        "name": "List Files in Directory",
        "prompt": """
List all Python files in the current workspace directory.

When asked to execute a command, please ask for confirmation.
""",
    }

    print("\n[SPAWNING] Worker for Test 2...")
    session = manager.spawn_worker("test_2", task)

    if session:
        print("[OK] Worker spawned successfully")
        print("\n[RUNNING] Interactive session...")

        result = manager.run_interactive_session(session.worker_id)

        print("\n" + "=" * 70)
        print("TEST 2 RESULT")
        print("=" * 70)
        print(f"Success: {result.success}")
        print(f"Duration: {result.duration:.1f}s" if result.duration else "Duration: N / A")
        print(f"Error: {result.error_message}" if result.error_message else "Error: None")
        print(f"Output length: {len(result.output)} characters")

        if result.success:
            print("\n[PASS] Test 2 completed successfully!")
        else:
            print("\n[FAIL] Test 2 failed")

        return result.success
    else:
        print("\n[ERROR] Failed to spawn worker")
        return False


def test_3_pattern_discovery():
    """Test 3: Discover actual Claude CLI confirmation patterns"""
    print("\n" + "=" * 70)
    print("TEST 3: Pattern Discovery")
    print("=" * 70)
    print("\nThis test runs a worker that will likely trigger confirmations.")
    print("All output will be captured to help identify actual patterns.")

    config = OrchestratorConfig.from_env()
    config.workspace_root = "./workspace"

    logger = TestLogger("workspace / test_enhanced_interactive.log")

    # Create manager with verbose logging
    manager = EnhancedInteractiveWorkerManager(
        config=config, logger=logger, user_approval_callback=user_approval_callback
    )

    task = {
        "name": "Pattern Discovery Task",
        "prompt": """
You are helping test the interactive mode of the orchestrator.

Please perform these actions and note what confirmations you receive:

1. Create a new file called "test_output.txt" with some content
2. Read the file you just created
3. List the files in the current directory

For each operation, please explicitly ask for confirmation before proceeding,
even if you might normally proceed without asking.

After each confirmation, note what format the confirmation request took.
""",
    }

    print("\n[SPAWNING] Worker for Test 3...")
    session = manager.spawn_worker("test_3", task)

    if session:
        print("[OK] Worker spawned successfully")
        print("\n[RUNNING] Interactive session...")
        print("[NOTE] Watch for confirmation patterns in the output\n")

        result = manager.run_interactive_session(session.worker_id, max_iterations=50)

        print("\n" + "=" * 70)
        print("TEST 3 RESULT")
        print("=" * 70)
        print(f"Success: {result.success}")
        print(f"Duration: {result.duration:.1f}s" if result.duration else "Duration: N / A")
        print(f"Error: {result.error_message}" if result.error_message else "Error: None")

        print("\n[SAVED] Full output saved to workspace / worker_test_3 / output.txt")
        print("[SAVED] Confirmation requests saved to workspace / confirmation_requests.log")

        # Save full output for analysis
        output_file = Path("workspace / worker_test_3 / full_output.txt")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf - 8") as f:
            f.write(result.output)

        print("\n[INFO] Analyze the output to identify actual confirmation patterns")

        return True
    else:
        print("\n[ERROR] Failed to spawn worker")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print(" Enhanced Interactive Worker Manager - Test Suite")
    print("=" * 70)
    print("\nThis test suite validates pexpect / wexpect integration")
    print("and captures actual Claude CLI confirmation patterns.\n")

    print(f"Platform: {sys.platform}")

    if sys.platform == "win32":
        print("Using: wexpect (Windows pseudo - terminal)")
    else:
        print("Using: pexpect (Unix pseudo - terminal)")

    print("\n[!] NOTE: These tests require Claude CLI to be installed")
    print("   and properly configured in your environment.\n")

    input("Press Enter to start tests...")

    tests = [
        ("Simple File Creation", test_1_simple_file_creation),
        ("Command Execution", test_2_command_execution),
        ("Pattern Discovery", test_3_pattern_discovery),
    ]

    results = []

    for i, (name, test_func) in enumerate(tests, 1):
        print(f"\n\n{'='*70}")
        print(f"Running Test {i}/{len(tests)}: {name}")
        print(f"{'='*70}")

        try:
            success = test_func()
            results.append((name, success))
        except KeyboardInterrupt:
            print("\n\n[!] Tests interrupted by user")
            break
        except Exception as e:
            print(f"\n[ERROR] Test failed with exception: {e}")
            import traceback

            traceback.print_exc()
            results.append((name, False))

        if i < len(tests):
            print("\n" + "-" * 70)
            input("Press Enter to continue to next test...")

    # Summary
    print("\n\n" + "=" * 70)
    print(" TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    print("\n" + "=" * 70)
    print(" ANALYSIS FILES")
    print("=" * 70)
    print("Check these files for detailed information:")
    print("  - workspace / test_enhanced_interactive.log")
    print("  - workspace / confirmation_requests.log")
    print("  - workspace / worker_*/full_output.txt")
    print("\nUse these to identify actual Claude CLI confirmation patterns")
    print("and tune the regex patterns in enhanced_interactive_worker_manager.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
