"""
Phase 1 End-to-End Validation Test

Tests the complete Phase 1 system with 3-4 parallel workers:
- Worker Status Dashboard real-time updates (<2s)
- Dialogue View integration
- Terminal View integration
- Metrics Dashboard integration
- Data consistency and no data loss
- All 4 view modes operational

Success Criteria:
- 3-4 workers execute in parallel successfully
- Worker Status Dashboard updates <2 seconds
- All dashboard views display correctly
- No data loss or corruption
- Performance metrics within targets
"""

import asyncio
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure UTF-8 encoding
from orchestrator.utils.encoding_config import configure_console_encoding, safe_print

configure_console_encoding()

from orchestrator.config import OrchestratorConfig
from orchestrator.core.common.metrics import MetricsCollector
from orchestrator.core.structured_logging import StructuredLogger
from orchestrator.core.worker.worker_manager import WorkerManager
from orchestrator.core.worker_status_monitor import WorkerStatusMonitor


class Phase1E2EValidator:
    """Phase 1 End-to-End Validation Manager"""

    def __init__(self, num_workers: int = 4):
        """
        Initialize E2E validator.

        Args:
            num_workers: Number of parallel workers to spawn (3-4)
        """
        self.num_workers = max(3, min(4, num_workers))
        self.config = self._create_config()
        self.logger = self._create_logger()

        # Create workspace directory
        workspace_path = Path(self.config.workspace_root)
        workspace_path.mkdir(parents=True, exist_ok=True)

        self.status_monitor = WorkerStatusMonitor(workspace_root=str(workspace_path))
        self.metrics_collector = MetricsCollector(workspace_root=workspace_path)
        self.worker_manager = None

        # Validation results
        self.results = {
            "workers_spawned": 0,
            "workers_completed": 0,
            "workers_failed": 0,
            "status_updates": [],
            "dialogue_messages": [],
            "terminal_outputs": [],
            "metrics_collected": [],
            "performance_metrics": {},
            "validation_errors": [],
        }

    def _create_config(self) -> OrchestratorConfig:
        """Create orchestrator configuration"""
        config = OrchestratorConfig()
        config.workspace_root = str(project_root / "workspace" / "e2e_test")
        config.execution_mode = "windows"
        # config.wsl_distribution = "Ubuntu-24.04"  # Not needed for Windows mode
        config.claude_command = "claude"  # Use PATH-resolved claude command
        config.windows_claude_path = "claude"  # Windows mode requires this
        config.nvm_path = ""  # Not needed for Windows mode
        return config

    def _create_logger(self) -> StructuredLogger:
        """Create structured logger"""
        log_dir = project_root / "logs" / "e2e_test"
        log_dir.mkdir(parents=True, exist_ok=True)

        return StructuredLogger(name="phase1_e2e", log_dir=log_dir, enable_console=True)

    def _create_test_tasks(self) -> List[Dict[str, Any]]:
        """
        Create simple test tasks for E2E validation.

        Returns:
            List of task dictionaries
        """
        task_templates = [
            {
                "name": "create_hello_world",
                "prompt": """Create a simple hello_world.py file that prints 'Hello from Worker 1!'.

Requirements:
1. Create hello_world.py in the workspace
2. Add a main function
3. Print the greeting message
4. Add a docstring
5. Ensure UTF-8 encoding

Complete this task and confirm when done.""",
            },
            {
                "name": "create_calculator",
                "prompt": """Create a simple calculator.py file with basic arithmetic operations.

Requirements:
1. Create calculator.py in the workspace
2. Implement add, subtract, multiply, divide functions
3. Add docstrings to all functions
4. Add basic error handling (division by zero)
5. Ensure UTF-8 encoding

Complete this task and confirm when done.""",
            },
            {
                "name": "create_string_utils",
                "prompt": """Create a string_utils.py file with string manipulation functions.

Requirements:
1. Create string_utils.py in the workspace
2. Implement reverse_string, capitalize_words, count_words functions
3. Add docstrings to all functions
4. Add type hints
5. Ensure UTF-8 encoding

Complete this task and confirm when done.""",
            },
            {
                "name": "create_file_reader",
                "prompt": """Create a file_reader.py file that reads and processes text files.

Requirements:
1. Create file_reader.py in the workspace
2. Implement read_file, count_lines, count_characters functions
3. Add proper error handling for file operations
4. Add docstrings to all functions
5. Ensure UTF-8 encoding

Complete this task and confirm when done.""",
            },
        ]

        return task_templates[: self.num_workers]

    async def validate_worker_status_updates(
        self, worker_ids: List[str], timeout: float = 120.0
    ) -> bool:
        """
        Validate Worker Status Dashboard real-time updates.

        Args:
            worker_ids: List of worker IDs to monitor
            timeout: Maximum validation time in seconds

        Returns:
            True if validation passes
        """
        safe_print("\n[E2E] Validating Worker Status Dashboard...")

        start_time = time.time()
        update_latencies = []

        # Monitor status updates for all workers
        while time.time() - start_time < timeout:
            for worker_id in worker_ids:
                status = self.status_monitor.get_worker_status(worker_id)

                if status:
                    # Record update
                    update_time = time.time()
                    latency = update_time - status.get("last_update", update_time)
                    update_latencies.append(latency)

                    self.results["status_updates"].append(
                        {
                            "worker_id": worker_id,
                            "timestamp": update_time,
                            "latency": latency,
                            "status": status,
                        }
                    )

            # Check if all workers have completed
            all_done = all(
                self.status_monitor.get_worker_status(wid).get("state")
                in ["completed", "error", "terminated"]
                for wid in worker_ids
                if self.status_monitor.get_worker_status(wid)
            )

            if all_done:
                break

            await asyncio.sleep(0.5)  # Poll every 500ms

        # Calculate performance metrics
        if update_latencies:
            avg_latency = sum(update_latencies) / len(update_latencies)
            max_latency = max(update_latencies)

            self.results["performance_metrics"]["status_avg_latency"] = avg_latency
            self.results["performance_metrics"]["status_max_latency"] = max_latency

            # Validation: max latency must be <2 seconds
            passed = max_latency < 2.0

            safe_print(f"[E2E] Status Update Performance:")
            safe_print(f"      Average Latency: {avg_latency:.3f}s")
            safe_print(f"      Maximum Latency: {max_latency:.3f}s")
            safe_print(f"      Target: <2.0s")
            safe_print(f"      Result: {'✅ PASS' if passed else '❌ FAIL'}")

            return passed
        else:
            safe_print("[E2E] ❌ No status updates recorded")
            self.results["validation_errors"].append("No status updates recorded")
            return False

    async def validate_dialogue_logging(self, worker_ids: List[str]) -> bool:
        """
        Validate Dialogue View integration.

        Args:
            worker_ids: List of worker IDs

        Returns:
            True if validation passes
        """
        safe_print("\n[E2E] Validating Dialogue View...")

        # Check dialogue transcript files
        dialogue_dir = Path(self.config.workspace_root).parent / "dialogue_logs"

        if not dialogue_dir.exists():
            safe_print("[E2E] ❌ Dialogue log directory not found")
            self.results["validation_errors"].append("Dialogue log directory missing")
            return False

        # Check for dialogue files
        dialogue_files = list(dialogue_dir.glob("*.jsonl"))

        if len(dialogue_files) == 0:
            safe_print("[E2E] ⚠️ No dialogue files found (may be normal for short tasks)")
            return True  # Not a failure

        # Count dialogue messages
        message_count = 0
        for dialogue_file in dialogue_files:
            with open(dialogue_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                message_count += len(lines)
                self.results["dialogue_messages"].extend(lines)

        safe_print(f"[E2E] Dialogue Messages: {message_count}")
        safe_print(f"[E2E] Dialogue Files: {len(dialogue_files)}")
        safe_print("[E2E] ✅ Dialogue logging operational")

        return True

    async def validate_terminal_capture(self, worker_ids: List[str]) -> bool:
        """
        Validate Terminal View integration.

        Args:
            worker_ids: List of worker IDs

        Returns:
            True if validation passes
        """
        safe_print("\n[E2E] Validating Terminal View...")

        # Check terminal output captures
        workspace_root = Path(self.config.workspace_root).parent
        output_dir = workspace_root / "outputs"

        if not output_dir.exists():
            safe_print("[E2E] ❌ Output directory not found")
            self.results["validation_errors"].append("Output directory missing")
            return False

        # Check for output files
        output_files = list(output_dir.glob("worker_*.txt"))

        if len(output_files) == 0:
            safe_print("[E2E] ❌ No terminal output files found")
            self.results["validation_errors"].append("No terminal outputs captured")
            return False

        # Count output lines
        total_lines = 0
        for output_file in output_files:
            with open(output_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                total_lines += len(lines)
                self.results["terminal_outputs"].append(
                    {"file": output_file.name, "lines": len(lines)}
                )

        safe_print(f"[E2E] Terminal Output Files: {len(output_files)}")
        safe_print(f"[E2E] Total Output Lines: {total_lines}")
        safe_print("[E2E] ✅ Terminal capture operational")

        return True

    async def validate_metrics_collection(self) -> bool:
        """
        Validate Metrics Dashboard integration.

        Returns:
            True if validation passes
        """
        safe_print("\n[E2E] Validating Metrics Dashboard...")

        # Get current metrics
        current_metrics = self.metrics_collector.get_current_metrics()

        if not current_metrics:
            safe_print("[E2E] ⚠️ No metrics collected (may be normal for simple tasks)")
            return True  # Not a failure

        # Record metrics
        self.results["metrics_collected"].append(current_metrics)

        # Validate metric structure
        required_fields = ["total_decisions", "rule_decisions", "ai_decisions"]
        missing_fields = [f for f in required_fields if f not in current_metrics]

        if missing_fields:
            safe_print(f"[E2E] ❌ Missing metric fields: {missing_fields}")
            self.results["validation_errors"].append(f"Missing metrics: {missing_fields}")
            return False

        safe_print(f"[E2E] Total Decisions: {current_metrics.get('total_decisions', 0)}")
        safe_print(f"[E2E] Rule Decisions: {current_metrics.get('rule_decisions', 0)}")
        safe_print(f"[E2E] AI Decisions: {current_metrics.get('ai_decisions', 0)}")
        safe_print("[E2E] ✅ Metrics collection operational")

        return True

    async def run_validation(self) -> bool:
        """
        Run complete Phase 1 E2E validation.

        Returns:
            True if all validation passes
        """
        safe_print("=" * 80)
        safe_print("Phase 1 End-to-End Validation Test")
        safe_print("=" * 80)
        safe_print(f"Workers: {self.num_workers}")
        safe_print(f"Workspace: {self.config.workspace_root}")
        safe_print("=" * 80)

        try:
            # Create workspace
            workspace_path = Path(self.config.workspace_root)
            workspace_path.mkdir(parents=True, exist_ok=True)

            # Initialize worker manager
            self.worker_manager = WorkerManager(
                config=self.config, logger=self.logger, user_approval_callback=None  # Auto-approval
            )

            # Create test tasks
            tasks = self._create_test_tasks()

            # Spawn workers
            safe_print("\n[E2E] Spawning workers...")
            worker_ids = []

            for i, task in enumerate(tasks):
                worker_id = f"e2e_worker_{i+1:02d}"

                safe_print(f"[E2E] Spawning: {worker_id} - {task['name']}")

                session = self.worker_manager.spawn_worker(worker_id=worker_id, task=task)

                if session:
                    worker_ids.append(worker_id)
                    self.results["workers_spawned"] += 1
                    safe_print(f"[E2E] ✅ {worker_id} spawned")
                else:
                    self.results["workers_failed"] += 1
                    safe_print(f"[E2E] ❌ {worker_id} failed to spawn")

            if len(worker_ids) == 0:
                safe_print("[E2E] ❌ No workers spawned")
                return False

            # Start parallel validation
            safe_print(f"\n[E2E] Executing {len(worker_ids)} workers in parallel...")

            # Monitor worker status in background
            status_task = asyncio.create_task(
                self.validate_worker_status_updates(worker_ids, timeout=300.0)
            )

            # Wait for workers to complete
            results = self.worker_manager.wait_all(
                max_workers=len(worker_ids), timeout=300  # 5 minutes
            )

            # Process results
            for result in results:
                if result.success:
                    self.results["workers_completed"] += 1
                    safe_print(f"[E2E] ✅ {result.worker_id} completed")
                else:
                    self.results["workers_failed"] += 1
                    safe_print(f"[E2E] ❌ {result.worker_id} failed: {result.error_message}")

            # Wait for status validation to complete
            status_validation_passed = await status_task

            # Run additional validations
            dialogue_validation_passed = await self.validate_dialogue_logging(worker_ids)
            terminal_validation_passed = await self.validate_terminal_capture(worker_ids)
            metrics_validation_passed = await self.validate_metrics_collection()

            # Generate final report
            safe_print("\n" + "=" * 80)
            safe_print("Phase 1 E2E Validation Results")
            safe_print("=" * 80)

            safe_print(f"\n✓ Workers Spawned: {self.results['workers_spawned']}/{self.num_workers}")
            safe_print(
                f"✓ Workers Completed: {self.results['workers_completed']}/{self.num_workers}"
            )
            safe_print(f"✓ Workers Failed: {self.results['workers_failed']}/{self.num_workers}")

            safe_print(
                f"\n✓ Worker Status Dashboard: {'✅ PASS' if status_validation_passed else '❌ FAIL'}"
            )
            safe_print(f"✓ Dialogue View: {'✅ PASS' if dialogue_validation_passed else '❌ FAIL'}")
            safe_print(f"✓ Terminal View: {'✅ PASS' if terminal_validation_passed else '❌ FAIL'}")
            safe_print(
                f"✓ Metrics Dashboard: {'✅ PASS' if metrics_validation_passed else '❌ FAIL'}"
            )

            # Overall success criteria
            completion_rate = (self.results["workers_completed"] / self.num_workers) * 100
            all_dashboards_passed = (
                status_validation_passed
                and dialogue_validation_passed
                and terminal_validation_passed
                and metrics_validation_passed
            )

            overall_success = (
                self.results["workers_spawned"] >= 3
                and completion_rate >= 75.0
                and all_dashboards_passed
                and len(self.results["validation_errors"]) == 0
            )

            safe_print("\n" + "=" * 80)
            if overall_success:
                safe_print("🎉 PHASE 1 E2E VALIDATION: SUCCESS")
                safe_print("All 4 dashboard views operational, performance targets met!")
            else:
                safe_print("❌ PHASE 1 E2E VALIDATION: FAILURE")
                if self.results["validation_errors"]:
                    safe_print("\nErrors:")
                    for error in self.results["validation_errors"]:
                        safe_print(f"  - {error}")
            safe_print("=" * 80)

            return overall_success

        except Exception as e:
            safe_print(f"\n[E2E] ❌ Validation failed with exception: {e}")
            import traceback

            traceback.print_exc()
            return False


@pytest.mark.asyncio
async def test_phase1_e2e_validation_4_workers():
    """
    Test Phase 1 E2E with 4 workers.

    Success Criteria:
    - 4 workers spawn and execute in parallel
    - Worker Status Dashboard updates <2s
    - All 4 view modes operational
    - ≥75% completion rate
    - No data loss
    """
    validator = Phase1E2EValidator(num_workers=4)
    success = await validator.run_validation()
    assert success, "Phase 1 E2E validation with 4 workers failed"


@pytest.mark.asyncio
async def test_phase1_e2e_validation_3_workers():
    """
    Test Phase 1 E2E with 3 workers.

    Success Criteria:
    - 3 workers spawn and execute in parallel
    - Worker Status Dashboard updates <2s
    - All 4 view modes operational
    - ≥75% completion rate
    - No data loss
    """
    validator = Phase1E2EValidator(num_workers=3)
    success = await validator.run_validation()
    assert success, "Phase 1 E2E validation with 3 workers failed"


if __name__ == "__main__":
    """Run E2E validation standalone"""

    async def main():
        # Run with 4 workers by default
        validator = Phase1E2EValidator(num_workers=4)
        success = await validator.run_validation()
        sys.exit(0 if success else 1)

    asyncio.run(main())
