"""
Test Codex Worker Integration

Simple test script to verify Codex worker can be spawned and executed
through the orchestrator system.
"""

import sys
import time
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.config import OrchestratorConfig
from orchestrator.core.worker.worker_manager import WorkerManager
from orchestrator.interfaces import ILogger


class TestLogger(ILogger):
    """Simple logger for testing"""

    def info(self, message: str, **kwargs):
        print(f"[INFO] {message}", kwargs if kwargs else "")

    def error(self, message: str, **kwargs):
        print(f"[ERROR] {message}", kwargs if kwargs else "")

    def warning(self, message: str, **kwargs):
        print(f"[WARNING] {message}", kwargs if kwargs else "")

    def log_worker_spawn(self, worker_id: str, task_name: str):
        print(f"[SPAWN] Worker {worker_id}: {task_name}")

    def log_worker_complete(self, worker_id: str, duration: float):
        print(f"[COMPLETE] Worker {worker_id} completed in {duration:.2f}s")

    def log_worker_error(self, worker_id: str, error: str):
        print(f"[ERROR] Worker {worker_id}: {error}")


def test_codex_worker():
    """Test Codex worker with simple file creation task"""

    print("=" * 60)
    print("Test: Codex Worker Integration")
    print("=" * 60)

    # Create test workspace
    test_workspace = Path(__file__).parent / "test_codex_integration"
    test_workspace.mkdir(exist_ok=True)

    # Configure orchestrator for test
    config = OrchestratorConfig(
        workspace_root=str(test_workspace),
        wsl_workspace_root="/mnt / d / user / ai_coding / AI_Investor / tools / parallel - coding / test_codex_integration",
        execution_mode="wsl",
        wsl_distribution="Ubuntu - 24.04",
        nvm_path="/home / chemi/.local / bin:/home / chemi/.nvm / versions / node / v22.21.0 / bin",
        codex_command="codex",
    )

    # Create worker manager
    logger = TestLogger()
    manager = WorkerManager(config=config, logger=logger)

    # Define simple test task
    task = {
        "name": "Create Calculator Module",
        "prompt": """Create a Python calculator module.

Requirements:
- File name: calculator.py
- Implement functions: add(a, b), subtract(a, b), multiply(a, b), divide(a, b)
- Include docstrings
- Include type hints
- Handle division by zero

Save to calculator.py in the current directory.
""",
    }

    print(f"\nTask: {task['name']}")
    print("Worker Type: Codex (GPT - 5)")
    print(f"Workspace: {test_workspace}")
    print()

    # Spawn Codex worker
    print("[1] Spawning Codex worker...")
    session = manager.spawn_worker(
        worker_id="codex_test_001", task=task, timeout=120, worker_type="codex"
    )

    if not session:
        print("[ERROR] Failed to spawn Codex worker")
        return False

    print(f"[OK] Worker spawned: {session.worker_id}")
    print()

    # Monitor worker execution
    print("[2] Monitoring worker execution...")
    max_wait = 60  # seconds
    check_interval = 2  # seconds
    elapsed = 0

    while elapsed < max_wait:
        # Check if worker has output
        try:
            output = session.child_process.read_nonblocking(size=1000, timeout=0)
            if output:
                print(f"[OUTPUT] {output[:200]}...")
        except Exception:
            pass

        # Check if calculator.py was created
        worker_dir = test_workspace / f"worker_{session.worker_id}"
        calculator_file = worker_dir / "calculator.py"

        if calculator_file.exists():
            print(f"\n[SUCCESS] File created: {calculator_file}")
            print(f"File size: {calculator_file.stat().st_size} bytes")

            # Read and display first few lines
            with open(calculator_file, "r", encoding="utf - 8") as f:
                lines = f.readlines()[:10]
                print("\nFirst 10 lines:")
                for i, line in enumerate(lines, 1):
                    print(f"  {i:2d}: {line.rstrip()}")

            print("\n[TEST PASSED] Codex worker successfully created calculator.py")
            return True

        time.sleep(check_interval)
        elapsed += check_interval
        print(f"  ... waiting ({elapsed}s / {max_wait}s)")

    print(f"\n[TIMEOUT] File not created within {max_wait}s")
    print("[TEST FAILED] Codex worker did not complete task")
    return False


if __name__ == "__main__":
    try:
        success = test_codex_worker()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[EXCEPTION] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
