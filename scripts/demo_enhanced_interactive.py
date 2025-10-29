"""
Simple Demo of EnhancedInteractiveWorkerManager

Demonstrates the pexpect/wexpect-based interactive mode with a simple example.
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


class DemoLogger:
    """Simple logger for demo"""

    def log_worker_spawn(self, worker_id, task_name):
        print(f"[SPAWN] {worker_id}: {task_name}")

    def info(self, message, **kwargs):
        print(f"[INFO] {message}")

    def warning(self, message, **kwargs):
        print(f"[WARN] {message}")

    def error(self, message, **kwargs):
        print(f"[ERROR] {message}")


def demo_approval_callback(confirmation: ConfirmationRequest) -> bool:
    """Demo approval callback - auto-approves safe operations"""
    print(f"\n{'='*60}")
    print(f"CONFIRMATION REQUEST")
    print(f"{'='*60}")
    print(f"Type: {confirmation.confirmation_type}")
    print(f"Message: {confirmation.message}")
    print(f"Details: {confirmation.details}")

    # Auto-approve file writes
    if confirmation.confirmation_type.value == "file_write":
        print("[AUTO-APPROVE] Safe file write operation")
        print(f"{'='*60}\n")
        return True

    # Auto-approve file reads
    if confirmation.confirmation_type.value == "file_read":
        print("[AUTO-APPROVE] Safe file read operation")
        print(f"{'='*60}\n")
        return True

    # Deny everything else for safety
    print("[AUTO-DENY] Operation not pre-approved")
    print(f"{'='*60}\n")
    return False


def main():
    """Run simple demo"""
    print("\n" + "=" * 70)
    print(" EnhancedInteractiveWorkerManager Demo")
    print("=" * 70)
    print("\nThis demo shows the pexpect/wexpect-based interactive mode")
    print("with a simple Python script execution.\n")

    # Setup
    config = OrchestratorConfig.from_env()
    config.workspace_root = "./workspace"

    logger = DemoLogger()

    print(f"Platform: {sys.platform}")
    if sys.platform == "win32":
        print("Using: wexpect (Windows)")
    else:
        print("Using: pexpect (Unix/Linux)")

    print("\n" + "-" * 70)
    print("Creating manager...")

    manager = EnhancedInteractiveWorkerManager(
        config=config, logger=logger, user_approval_callback=demo_approval_callback
    )

    print("[OK] Manager created\n")

    # Create a simple Python task
    print("Creating task: 'Hello World' Python script")

    task = {
        "name": "Create Hello World",
        "prompt": """
Please create a simple Python script that:
1. Prints "Hello, World!" to the console
2. Saves the output to a file called 'hello.txt'

Just create a basic script and save it.
""",
    }

    print("\nSpawning worker...")

    # Note: This will try to use Claude CLI
    # For demo purposes, we'll catch the error if Claude CLI is not available
    try:
        session = manager.spawn_worker("demo_worker", task)

        if session:
            print("[OK] Worker spawned successfully")
            print("\nRunning interactive session...")
            print("(Watch for confirmation detection and AI safety judgments)\n")

            result = manager.run_interactive_session(session.worker_id, max_iterations=20)

            print("\n" + "=" * 70)
            print(" RESULT")
            print("=" * 70)
            print(f"Success: {result.success}")
            print(f"Duration: {result.duration:.2f}s" if result.duration else "Duration: N/A")

            if result.error_message:
                print(f"Error: {result.error_message}")

            print(f"\nOutput preview ({len(result.output)} chars):")
            print("-" * 70)
            # Show first 500 chars
            preview = result.output[:500]
            if len(result.output) > 500:
                preview += "\n... (truncated)"
            print(preview)
            print("-" * 70)

            if result.success:
                print("\n[SUCCESS] Demo completed successfully!")
            else:
                print("\n[PARTIAL] Demo completed with errors")
        else:
            print("[ERROR] Failed to spawn worker")
            print("\nThis is expected if Claude CLI is not installed or configured.")

    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        print("\nThis is expected if Claude CLI is not installed.")
        print("\nTo test with actual Claude CLI:")
        print("  1. Install Claude CLI")
        print("  2. Configure paths in OrchestratorConfig")
        print("  3. Run this demo again")
        print("\nFor now, the architecture has been validated with:")
        print("  - Basic pexpect/wexpect functionality tests")
        print("  - Mock CLI integration tests")

    print("\n" + "=" * 70)
    print(" Demo Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
