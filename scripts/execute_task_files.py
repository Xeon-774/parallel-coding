#!/usr / bin / env python
"""
Task File Executor for Parallel AI App

Execute pre - defined task files directly without AI - driven decomposition.
This allows running detailed task files (like WORKER_1_MANAGER_AI_CORE.md)
in parallel using the orchestrator system.

Usage:
    python scripts / execute_task_files.py task1.md task2.md [task3.md ...]

Example:
    python scripts / execute_task_files.py \
        tasks / WORKER_1_MANAGER_AI_CORE.md \
        tasks / WORKER_3_HIERARCHICAL_CORE.md

Features:
- Reads task files and extracts content
- Spawns workers with task file content as prompts
- Enables parallel execution of detailed task specifications
- Integrates with existing monitoring dashboard
- Full Excellence AI Standard enforcement via task files

Author: Claude (Sonnet 4.5)
Created: 2025 - 10 - 25
Version: 1.0.0
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from typing import Any

from orchestrator.config import OrchestratorConfig
from orchestrator.core.cli_orchestrator import CLIOrchestratorAI
from orchestrator.core.worker.worker_manager import WorkerManager


class SimpleLogger:
    """Simple logger implementation for task executor"""

    def log_worker_spawn(self, worker_id: str, task_name: str, **kwargs: Any) -> None:
        print(f"[LOG] Spawned: {worker_id} - {task_name}")

    def log_worker_complete(self, worker_id: str, output_size: int, **kwargs: Any) -> None:
        print(f"[LOG] Completed: {worker_id} - {output_size} bytes")

    def log_task_error(self, task_id: str, task_name: str, error: str, **kwargs: Any) -> None:
        print(f"[LOG] Task Error: {task_id} - {task_name}: {error}")

    def debug(self, message: str, **kwargs: Any) -> None:
        print(f"[DEBUG] {message} | {kwargs}")

    def info(self, message: str, **kwargs: Any) -> None:
        print(f"[INFO] {message} | {kwargs}")

    def warning(self, message: str, **kwargs: Any) -> None:
        print(f"[WARN] {message} | {kwargs}")

    def error(self, message: str, **kwargs: Any) -> None:
        print(f"[ERROR] {message} | {kwargs}")


class TaskFileExecutor:
    """
    Execute pre - defined task files in parallel.

    This class reads task markdown files and executes them using
    the parallel AI orchestrator without requiring AI - driven task
    decomposition.
    """

    def __init__(
        self,
        config: OrchestratorConfig,
        logger: SimpleLogger,
        auto_approve_caution: bool = True,
        use_codex: bool = False,
    ):
        """
        Initialize task file executor.

        Args:
            config: Orchestrator configuration
            logger: Logger instance
            auto_approve_caution: Auto - approve CAUTION - level operations (default: True)
                                 WorkerManager handles all safety levels:
                                 - SAFE: Always auto - approved
                                 - CAUTION: Escalated to this callback
                                 - DANGEROUS / PROHIBITED: Always denied
            use_codex: Use Codex workers instead of Claude workers (default: False)
        """
        self.config = config
        self.logger = logger
        self.use_codex = use_codex

        # Callback for CAUTION - level operations escalated by WorkerManager
        user_callback = self._approve_caution_operations if auto_approve_caution else None

        self.worker_manager = WorkerManager(config, logger, user_approval_callback=user_callback)
        self.orchestrator_ai = CLIOrchestratorAI(workspace=config.workspace_root, verbose=True)

    def _approve_caution_operations(self, confirmation_request) -> bool:
        """
        Approve CAUTION - level operations for pre - defined tasks.

        WorkerManager escalates only CAUTION - level operations to this callback.
        For task file execution, we trust pre - defined tasks.

        Args:
            confirmation_request: Confirmation request from WorkerManager

        Returns:
            True (approve all CAUTION operations for pre - defined tasks)
        """
        return True

    def read_task_file(self, task_file_path: Path) -> Dict[str, Any]:
        """
        Read and parse task file.

        Args:
            task_file_path: Path to task markdown file

        Returns:
            Task dictionary with name and prompt

        Raises:
            FileNotFoundError: If task file doesn't exist
            ValueError: If task file is invalid
        """
        if not task_file_path.exists():
            raise FileNotFoundError(f"Task file not found: {task_file_path}")

        # Read task file content
        with open(task_file_path, "r", encoding="utf - 8") as f:
            content = f.read()

        if not content.strip():
            raise ValueError(f"Task file is empty: {task_file_path}")

        # Extract task name from filename
        task_name = task_file_path.stem

        # Load Codex worker system prompt
        codex_prompt_path = Path(__file__).parent.parent / "CODEX_WORKER_SYSTEM_PROMPT.md"
        if codex_prompt_path.exists():
            with open(codex_prompt_path, "r", encoding="utf - 8") as f:
                codex_prompt = f.read()
        else:
            # Fallback if Codex prompt doesn't exist
            codex_prompt = """# Codex Worker Instructions
Execute this task completely with excellence_ai_standard 100% compliance.
DO NOT ask for permission repeatedly. Proceed with implementation immediately."""

        # Combine Codex prompt + task content
        prompt = """{codex_prompt}

---

# YOUR TASK

{content}

---

**START EXECUTION NOW. This task is pre - approved.**
"""

        return {"name": task_name, "prompt": prompt, "source_file": str(task_file_path)}

    async def execute_tasks_parallel(self, task_files: List[Path]) -> bool:
        """
        Execute multiple task files in parallel.

        Args:
            task_files: List of task file paths

        Returns:
            True if all tasks completed successfully
        """
        print(f"\n{'='*70}")
        print("PARALLEL TASK FILE EXECUTION")
        print(f"{'='*70}")
        print(f"Tasks to execute: {len(task_files)}")
        for i, task_file in enumerate(task_files, 1):
            print(f"  {i}. {task_file.name}")
        print(f"{'='*70}\n")

        # Read all task files
        tasks = []
        for task_file in task_files:
            try:
                task = self.read_task_file(task_file)
                tasks.append(task)
                print(f"✓ Loaded: {task['name']}")
            except Exception as e:
                print(f"✗ Failed to load {task_file}: {e}")
                return False

        print(f"\n{'='*70}")
        print(f"Starting {len(tasks)} workers in parallel...")
        print(f"{'='*70}\n")

        # Spawn workers
        sessions = []
        for i, task in enumerate(tasks, 1):
            worker_id = str(i)

            if self.use_codex:
                # Use Codex Worker
                session = self.worker_manager.spawn_codex_worker(
                    worker_id=worker_id, task=task, timeout=300
                )
            else:
                # Use Claude Worker
                session = self.worker_manager.spawn_worker(
                    worker_id=worker_id, task=task, timeout=300
                )

            if session:
                sessions.append(session)
                worker_type = "Codex" if self.use_codex else "Claude"
                print(f"✓ Worker {worker_id} started ({worker_type}): {task['name']}")
            else:
                print(f"✗ Failed to start worker {worker_id}")
                return False

        print(f"\n{'='*70}")
        print("MONITORING WORKERS")
        print(f"{'='*70}")
        print(f"All {len(sessions)} workers running.")
        print("Open Web Dashboard: http://localhost:8000")
        print(f"{'='*70}\n")

        # Monitor workers until completion
        try:
            if self.use_codex:
                # Codex workers: Run sessions in parallel using asyncio
                import asyncio as aio

                async def run_codex_worker(worker_idx: int, task: dict) -> Any:
                    worker_id = f"worker_{worker_idx}"
                    print(f"\n[CODEX - RUN] {worker_id}: {task['name']}")
                    # Run in executor to avoid blocking
                    loop = aio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, self.worker_manager.run_codex_session, worker_id, 1800
                    )
                    return result

                # Run all Codex workers in parallel
                results = await aio.gather(
                    *[run_codex_worker(i, task) for i, task in enumerate(tasks, 1)]
                )
            else:
                # Claude workers: Use existing wait_all method
                results = self.worker_manager.wait_all(
                    max_workers=len(sessions), timeout=1800  # 30 minutes timeout
                )

            # Check if all succeeded
            all_success = all(r.success for r in results)

            print(f"\n{'='*70}")
            print("EXECUTION COMPLETE")
            print(f"{'='*70}")
            for i, result in enumerate(results, 1):
                status = "✓" if result.success else "✗"
                print(f"{status} Worker {i}: {result.name} ({result.duration:.1f}s)")
            print(f"{'='*70}\n")

            return all_success
        except KeyboardInterrupt:
            print("\n\nExecution interrupted by user.")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Execute pre - defined task files in parallel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Execute 2 tasks in parallel
  python scripts / execute_task_files.py \\
      tasks / WORKER_1_MANAGER_AI_CORE.md \\
      tasks / WORKER_3_HIERARCHICAL_CORE.md

  # Execute single task
  python scripts / execute_task_files.py tasks / MY_TASK.md

Notes:
  - Task files should be detailed markdown specifications
  - Workers will execute tasks independently
  - Monitor progress via Web Dashboard (http://localhost:8000)
  - All excellence_ai_standard rules are automatically enforced
""",
    )

    parser.add_argument("task_files", nargs="+", type=Path, help="Path(s) to task markdown file(s)")

    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path("workspace"),
        help="Workspace root directory (default: workspace/)",
    )

    parser.add_argument(
        "--codex",
        action="store_true",
        help="Use Codex workers (GPT - 5) instead of Claude workers (cost - efficient)",
    )

    args = parser.parse_args()

    # Validate task files
    for task_file in args.task_files:
        if not task_file.exists():
            print(f"Error: Task file not found: {task_file}")
            sys.exit(1)

    # Initialize config and logger
    config = OrchestratorConfig.from_env()
    config.workspace_root = str(args.workspace)
    logger = SimpleLogger()

    # Create executor
    executor = TaskFileExecutor(config, logger, use_codex=args.codex)

    # Execute tasks
    success = asyncio.run(executor.execute_tasks_parallel(args.task_files))

    if success:
        print("\n✓ All tasks completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Task execution failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
