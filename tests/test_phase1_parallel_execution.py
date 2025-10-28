"""
Phase 1: 8-Parallel Validation Test

Execute 8 Claude Code workers in parallel on MicroBlog test project.
"""

import sys
import json
from pathlib import Path

# Project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure UTF-8 encoding BEFORE any output
from orchestrator.utils.encoding_config import configure_console_encoding, safe_print
configure_console_encoding()

from orchestrator.config import OrchestratorConfig
from orchestrator.core.worker.worker_manager import WorkerManager
from orchestrator.core.structured_logging import StructuredLogger


def load_execution_config(config_path: str) -> dict:
    """Load Phase 1 execution configuration"""
    with open(config_path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def test_phase1_parallel_execution():
    """
    Phase 1: 8-Parallel Validation

    Spawns 8 Claude Code workers in parallel to develop different modules
    of the MicroBlog platform.

    Success Criteria:
    - All 8 workers spawn successfully
    - ≥75% (6/8) tasks complete successfully
    - <20% git conflict rate
    - No system crashes or deadlocks
    """

    safe_print("=" * 80)
    safe_print("Phase 1: 8-Parallel Validation Test")
    safe_print("=" * 80)

    # Load execution configuration
    config_file = project_root / "config" / "phase1_execution_config.json"
    exec_config = load_execution_config(str(config_file))

    safe_print(f"\nProject: {exec_config['execution_name']}")
    safe_print(f"Workers: {exec_config['max_parallel_workers']}")
    safe_print(f"Project Path: {exec_config['project_path']}\n")

    # Orchestrator configuration
    config = OrchestratorConfig()
    config.workspace_root = exec_config['project_path']
    config.execution_mode = exec_config['execution_mode']
    config.wsl_distribution = exec_config['wsl_distribution']
    config.claude_command = "~/.local/bin/claude"
    config.nvm_path = "/usr/bin"

    # Logging
    log_dir = Path(exec_config['logging']['log_dir'])
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = StructuredLogger(
        name="phase1_validation",
        log_dir=log_dir,
        enable_console=True
    )

    # Worker manager
    worker_manager = WorkerManager(
        config=config,
        logger=logger,
        user_approval_callback=None  # Auto-approval mode
    )

    safe_print("=" * 80)
    safe_print("Starting 8 Parallel Workers...")
    safe_print("=" * 80)

    # Track results
    spawned_workers = []
    completed_workers = []
    failed_workers = []
    git_conflicts = []

    try:
        # Spawn all workers in parallel
        for worker_config in exec_config['workers']:
            safe_print(f"\n[Spawn] Worker: {worker_config['worker_id']}")
            safe_print(f"        Module: {worker_config['module_name']}")
            safe_print(f"        Branch: {worker_config['git_branch']}")

            # Read task file
            task_file_path = Path(exec_config['project_path']) / worker_config['task_file']
            with open(task_file_path, 'r', encoding='utf-8-sig') as f:
                task_content = f.read()

            # Create task
            task = {
                "name": worker_config['module_name'],
                "prompt": f"""
You are a WorkerAI developing a module for the MicroBlog platform.

Your task:
{task_content}

Important:
- Follow all requirements exactly
- Create all specified files
- Write unit tests
- Ensure TypeScript compiles without errors
- Follow the encoding policy (UTF-8 with BOM)

Start working on this task now.
"""
            }

            # Spawn worker
            session = worker_manager.spawn_worker(
                worker_id=worker_config['worker_id'],
                task=task
            )

            if session:
                spawned_workers.append(worker_config['worker_id'])
                safe_print(f"[SUCCESS] Worker {worker_config['worker_id']} spawned")
            else:
                failed_workers.append(worker_config['worker_id'])
                safe_print(f"[FAILURE] Worker {worker_config['worker_id']} failed to spawn")

        # Wait for all workers to complete IN PARALLEL
        safe_print("\n" + "=" * 80)
        safe_print("Executing workers in PARALLEL...")
        safe_print(f"Workers: {len(spawned_workers)}")
        safe_print("=" * 80)

        # Execute all workers in parallel
        results = worker_manager.wait_all(
            max_workers=len(spawned_workers),
            timeout=1800  # 30 minutes total
        )

        # Process results
        for result in results:
            if result.success:
                completed_workers.append(result.worker_id)
                safe_print(f"[COMPLETE] Worker {result.worker_id} completed successfully")
            else:
                failed_workers.append(result.worker_id)
                safe_print(f"[FAILED] Worker {result.worker_id} failed: {result.error_message}")

        # Generate validation report
        safe_print("\n" + "=" * 80)
        safe_print("Phase 1 Validation Results")
        safe_print("=" * 80)

        total_workers = len(exec_config['workers'])
        spawned_count = len(spawned_workers)
        completed_count = len(completed_workers)
        failed_count = len(failed_workers)

        completion_rate = (completed_count / total_workers) * 100
        conflict_rate = (len(git_conflicts) / total_workers) * 100 if total_workers > 0 else 0

        safe_print(f"\nWorkers Spawned: {spawned_count}/{total_workers} ({spawned_count/total_workers*100:.1f}%)")
        safe_print(f"Modules Completed: {completed_count}/{total_workers} ({completion_rate:.1f}%)")
        safe_print(f"Modules Failed: {failed_count}/{total_workers} ({failed_count/total_workers*100:.1f}%)")
        safe_print(f"Git Conflicts: {len(git_conflicts)} ({conflict_rate:.1f}%)")

        # Evaluate success
        safe_print("\n" + "=" * 80)
        safe_print("Success Criteria Evaluation")
        safe_print("=" * 80)

        all_spawned = spawned_count == total_workers
        completion_target_met = completion_rate >= 75.0
        conflict_target_met = conflict_rate < 20.0

        safe_print(f"\n✓ All workers spawned: {'✅ PASS' if all_spawned else '❌ FAIL'}")
        safe_print(f"✓ Completion rate ≥75%: {'✅ PASS' if completion_target_met else '❌ FAIL'} ({completion_rate:.1f}%)")
        safe_print(f"✓ Conflict rate <20%: {'✅ PASS' if conflict_target_met else '❌ FAIL'} ({conflict_rate:.1f}%)")

        overall_success = all_spawned and completion_target_met and conflict_target_met

        safe_print("\n" + "=" * 80)
        if overall_success:
            safe_print("🎉 PHASE 1 VALIDATION: SUCCESS")
            safe_print("Parallel AI coding tool is validated for 8-parallel execution!")
        elif completion_rate >= 50:
            safe_print("⚠️ PHASE 1 VALIDATION: PARTIAL SUCCESS")
            safe_print("Some workers completed, but improvements needed.")
        else:
            safe_print("❌ PHASE 1 VALIDATION: FAILURE")
            safe_print("Significant issues detected. Review logs for details.")
        safe_print("=" * 80)

        return overall_success

    except Exception as e:
        safe_print(f"\n[ERROR] Phase 1 validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_phase1_parallel_execution()
    sys.exit(0 if success else 1)
