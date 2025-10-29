"""
Simple 2 - Worker Parallel Execution Test

Test the new parallel execution feature with 2 simple tasks.
"""

import sys
from pathlib import Path

# Project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure UTF - 8 encoding BEFORE any output
from orchestrator.utils.encoding_config import configure_console_encoding, safe_print

configure_console_encoding()

from orchestrator.config import OrchestratorConfig
from orchestrator.core.structured_logging import StructuredLogger
from orchestrator.core.worker.worker_manager import WorkerManager


def test_parallel_execution_simple():
    """
    Simple test: Spawn 2 workers in parallel

    Each worker performs a simple task (calculate a sum).
    Verify that both workers execute simultaneously.
    """

    safe_print("=" * 80)
    safe_print("Simple Parallel Execution Test (2 Workers)")
    safe_print("=" * 80)

    # Configuration
    config = OrchestratorConfig()
    config.workspace_root = str(project_root / "workspace" / "test_parallel_simple")
    config.execution_mode = "wsl"
    config.wsl_distribution = "Ubuntu - 24.04"
    config.claude_command = "~/.local / bin / claude"
    config.nvm_path = "/usr / bin"

    # Prepare workspace
    workspace = Path(config.workspace_root)
    workspace.mkdir(parents=True, exist_ok=True)

    # Logger
    logger = StructuredLogger(name="parallel_simple_test", log_dir=workspace, enable_console=True)

    # Worker manager
    worker_manager = WorkerManager(
        config=config, logger=logger, user_approval_callback=None  # Auto - approval mode
    )

    # Define 2 simple tasks
    tasks = [
        {
            "worker_id": "worker_01_simple",
            "task": {
                "name": "Simple Task 1: Calculate Sum",
                "prompt": """
Calculate the sum: 100 + 200 + 300

Print the result in this format: "Sum: [result]"

This is a simple test task. Complete it quickly.
""",
            },
        },
        {
            "worker_id": "worker_02_simple",
            "task": {
                "name": "Simple Task 2: Calculate Product",
                "prompt": """
Calculate the product: 5 × 10 × 15

Print the result in this format: "Product: [result]"

This is a simple test task. Complete it quickly.
""",
            },
        },
    ]

    try:
        # Spawn both workers
        safe_print("\n" + "=" * 80)
        safe_print("Spawning 2 workers...")
        safe_print("=" * 80)

        spawned_workers = []

        for task_def in tasks:
            worker_id = task_def["worker_id"]
            task = task_def["task"]

            safe_print(f"\n[Spawn] Worker: {worker_id}")
            safe_print(f"        Task: {task['name']}")

            session = worker_manager.spawn_worker(worker_id=worker_id, task=task)

            if session:
                spawned_workers.append(worker_id)
                safe_print(f"[SUCCESS] Worker {worker_id} spawned")
            else:
                safe_print(f"[FAILURE] Worker {worker_id} failed to spawn")

        if len(spawned_workers) != 2:
            safe_print(f"\n[ERROR] Failed to spawn all workers. Spawned: {len(spawned_workers)}/2")
            return False

        # Execute in parallel
        safe_print("\n" + "=" * 80)
        safe_print("Executing workers in PARALLEL...")
        safe_print("=" * 80)

        import time

        start_time = time.time()

        # Execute in parallel
        results = worker_manager.wait_all(max_workers=2, timeout=600)  # 10 minutes

        total_time = time.time() - start_time

        # Analyze results
        safe_print("\n" + "=" * 80)
        safe_print("Results")
        safe_print("=" * 80)

        success_count = 0
        for result in results:
            safe_print(f"\nWorker: {result.worker_id}")
            safe_print(f"  Success: {result.success}")
            safe_print(f"  Duration: {result.duration:.1f}s")

            if result.success:
                success_count += 1
                # Display output preview
                output_preview = result.output[-500:] if len(result.output) > 500 else result.output
                safe_print(f"  Output preview:\n{output_preview}")
            else:
                safe_print(f"  Error: {result.error_message}")

        safe_print(f"\nTotal execution time: {total_time:.1f}s")
        safe_print(f"Success rate: {success_count}/2 ({success_count / 2 * 100:.0f}%)")

        # Verify parallel execution
        safe_print("\n" + "=" * 80)
        safe_print("Parallel Execution Verification")
        safe_print("=" * 80)

        if len(results) == 2 and results[0].duration > 0 and results[1].duration > 0:
            # If parallel, total time should be ~= max(individual times)
            # If sequential, total time should be ~= sum(individual times)

            individual_sum = sum(r.duration for r in results)
            individual_max = max(r.duration for r in results)

            safe_print("\nIndividual durations:")
            for r in results:
                safe_print(f"  {r.worker_id}: {r.duration:.1f}s")

            safe_print(f"\nSum of individual durations: {individual_sum:.1f}s")
            safe_print(f"Max individual duration: {individual_max:.1f}s")
            safe_print(f"Actual total time: {total_time:.1f}s")

            # Check if execution was parallel
            # Parallel: total_time ≈ max_duration (within 20% tolerance)
            # Sequential: total_time ≈ sum_duration

            is_parallel = total_time < (
                individual_sum * 0.8
            )  # If total < 80% of sum, likely parallel

            safe_print(f"\nExecution mode: {'✅ PARALLEL' if is_parallel else '❌ SEQUENTIAL'}")

            if is_parallel:
                safe_print("Workers executed simultaneously! ✓")
            else:
                safe_print("Workers executed sequentially (NOT parallel)")

        safe_print("\n" + "=" * 80)
        if success_count == 2:
            safe_print("✅ TEST PASSED: Both workers completed successfully")
        else:
            safe_print("⚠️ TEST PARTIAL: Some workers failed")
        safe_print("=" * 80)

        return success_count == 2

    except Exception as e:
        safe_print(f"\n[ERROR] Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_parallel_execution_simple()
    sys.exit(0 if success else 1)
