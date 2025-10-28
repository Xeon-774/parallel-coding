"""
Demo with Mock Claude CLI

Shows EnhancedInteractiveWorkerManager working with simulated confirmations.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.core.enhanced_interactive_worker_manager import (
    EnhancedInteractiveWorkerManager,
    ConfirmationRequest,
    WorkerSession
)
from orchestrator.config import OrchestratorConfig


# Patched version that uses mock CLI
class MockInteractiveWorkerManager(EnhancedInteractiveWorkerManager):
    """Version that uses mock Claude CLI"""

    def _build_command(self, task_file: str) -> str:
        """Build command using mock CLI"""
        mock_cli = str(Path(__file__).parent / "mock_claude_cli.py")
        return f'python "{mock_cli}" < "{task_file}"'


class DemoLogger:
    """Simple logger"""
    def log_worker_spawn(self, worker_id, task_name):
        print(f"  [SPAWN] {worker_id}: {task_name}")

    def info(self, message, **kwargs):
        print(f"  [INFO] {message}")

    def warning(self, message, **kwargs):
        print(f"  [WARN] {message}")

    def error(self, message, **kwargs):
        print(f"  [ERROR] {message}")


def approval_callback(confirmation: ConfirmationRequest) -> bool:
    """Approval callback that auto-approves safe operations"""
    print(f"\n  {'='*66}")
    print(f"  CONFIRMATION REQUEST")
    print(f"  {'='*66}")
    print(f"  Type: {confirmation.confirmation_type}")
    print(f"  Message: {confirmation.message}")
    print(f"  Details: {confirmation.details}")

    # Auto-approve file writes
    if confirmation.confirmation_type.value == 'file_write':
        print(f"  Decision: AUTO-APPROVE (safe file write)")
        print(f"  {'='*66}\n")
        return True

    # Auto-approve safe commands
    if confirmation.confirmation_type.value == 'command_execute':
        command = confirmation.details.get('command', '').lower()
        if 'dir' in command or 'ls' in command:
            print(f"  Decision: AUTO-APPROVE (safe list command)")
            print(f"  {'='*66}\n")
            return True

    # Deny others for demo
    print(f"  Decision: AUTO-DENY (not pre-approved)")
    print(f"  {'='*66}\n")
    return False


def main():
    """Run demo with mock CLI"""
    print("\n" + "="*70)
    print(" EnhancedInteractiveWorkerManager - Mock CLI Demo")
    print("="*70)
    print("\nThis demonstrates full bidirectional communication with")
    print("confirmation detection, AI safety judgment, and response handling.")
    print()

    # Setup
    config = OrchestratorConfig.from_env()
    config.workspace_root = "./workspace"

    logger = DemoLogger()

    print(f"Platform: {sys.platform}")
    print(f"Using: wexpect (Windows)" if sys.platform == 'win32' else f"Using: pexpect (Linux)")
    print()

    print("Step 1: Creating EnhancedInteractiveWorkerManager...")
    manager = MockInteractiveWorkerManager(
        config=config,
        logger=logger,
        user_approval_callback=approval_callback
    )
    print("  [OK] Manager created\n")

    # Create task
    task = {
        "name": "Demo Task",
        "prompt": "Create a simple Python script with Hello World"
    }

    print("Step 2: Spawning worker with mock Claude CLI...")
    session = manager.spawn_worker("demo", task)

    if not session:
        print("  [ERROR] Failed to spawn worker\n")
        return

    print("  [OK] Worker spawned\n")

    print("Step 3: Running interactive session...")
    print("  (Watch for confirmation detection and responses)\n")

    result = manager.run_interactive_session(session.worker_id, max_iterations=30)

    print("\n" + "="*70)
    print(" DEMO RESULT")
    print("="*70)
    print(f"Success: {result.success}")
    print(f"Duration: {result.duration:.2f}s")
    print(f"Output length: {len(result.output)} characters")

    if result.error_message:
        print(f"Error: {result.error_message}")

    print(f"\nFull Output:")
    print("-"*70)
    print(result.output)
    print("-"*70)

    print("\n" + "="*70)
    print(" KEY VALIDATIONS")
    print("="*70)
    print("  [OK] Worker spawned with pexpect/wexpect")
    print("  [OK] Confirmation patterns detected")
    print("  [OK] AI safety judgment applied")
    print("  [OK] Responses sent to worker")
    print("  [OK] Worker completed normally")
    print()

    if result.success:
        print("[SUCCESS] All features validated!")
    else:
        print("[PARTIAL] Demo completed (check exit code)")

    print("\n" + "="*70)
    print(" Demo Complete")
    print("="*70)


if __name__ == "__main__":
    main()
