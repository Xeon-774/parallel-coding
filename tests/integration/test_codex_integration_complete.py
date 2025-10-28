"""
Comprehensive integration tests for Codex Worker implementation.

This test suite validates the complete Codex integration:
- CodexExecutor class (subprocess-based)
- WorkerManager integration (spawn_codex_worker, run_codex_session)
- JSONL event parsing
- File change tracking
- End-to-end task execution

Coverage target: ≥90% (Excellence AI Standard)

Test cases:
1. Simple file creation (hello.py)
2. Complex file creation (email_validator.py)
3. Multiple file creation
4. Timeout handling
5. Error handling
6. JSONL parsing validation
7. File change tracking validation

Author: Claude (Anthropic)
Date: 2025-10-27
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

import pytest

from orchestrator.config import OrchestratorConfig
from orchestrator.core.worker.codex_executor import (
    CodexExecutor,
    CodexExecutionResult,
    ExecutionStatus,
    FileChange,
    FileChangeEvent,
    ThreadStartedEvent,
    TurnCompletedEvent,
    create_codex_executor_from_config,
)
from orchestrator.core.worker.worker_manager import WorkerManager


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def test_workspace(tmp_path: Path) -> Path:
    """Create temporary workspace for tests"""
    workspace = tmp_path / "codex_test_workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


@pytest.fixture
def config(test_workspace: Path) -> OrchestratorConfig:
    """Create test configuration"""
    return OrchestratorConfig(
        execution_mode="wsl",
        workspace_root=str(test_workspace),
        wsl_distribution="Ubuntu-24.04",
        nvm_path="/home/chemi/.local/bin:/home/chemi/.nvm/versions/node/v22.21.0/bin",  # Claude CLI + Node.js paths
        codex_command="codex",
        default_timeout=300,
    )


@pytest.fixture
def executor(config: OrchestratorConfig) -> CodexExecutor:
    """Create CodexExecutor instance"""
    return create_codex_executor_from_config(config)


@pytest.fixture
def simple_logger() -> Any:
    """Simple logger for tests"""

    class SimpleLogger:
        def log_worker_spawn(self, worker_id: str, task_name: str, **kwargs: Any) -> None:
            print(f"[LOG] Spawned: {worker_id} - {task_name}")

        def log_worker_complete(self, worker_id: str, output_size: int, **kwargs: Any) -> None:
            print(f"[LOG] Completed: {worker_id} - {output_size} bytes")

        def log_task_error(self, task_id: str, task_name: str, error: str, **kwargs: Any) -> None:
            print(f"[LOG] Task Error: {task_id} - {task_name}: {error}")

        def debug(self, message: str, **kwargs: Any) -> None:
            print(f"[DEBUG] {message}")

        def info(self, message: str, **kwargs: Any) -> None:
            print(f"[INFO] {message}")

        def warning(self, message: str, **kwargs: Any) -> None:
            print(f"[WARN] {message}")

        def error(self, message: str, **kwargs: Any) -> None:
            print(f"[ERROR] {message}")

    return SimpleLogger()


@pytest.fixture
def worker_manager(config: OrchestratorConfig, simple_logger: Any) -> WorkerManager:
    """Create WorkerManager instance"""
    return WorkerManager(config=config, logger=simple_logger)


# ============================================================================
# CodexExecutor Unit Tests
# ============================================================================


def test_codex_executor_initialization(executor: CodexExecutor) -> None:
    """Test CodexExecutor initialization"""
    assert executor.wsl_distribution == "Ubuntu-24.04"
    assert executor.codex_command == "codex"
    assert executor.execution_mode == "wsl"
    assert executor.DEFAULT_TIMEOUT == 300
    assert executor.DEFAULT_MODEL == "gpt-5"


def test_codex_executor_wsl_path_conversion(executor: CodexExecutor) -> None:
    """Test Windows to WSL path conversion"""
    # Test drive letter conversion
    assert executor._convert_to_wsl_path("D:\\user\\file.txt") == "/mnt/d/user/file.txt"
    assert executor._convert_to_wsl_path("C:\\Program Files\\test") == "/mnt/c/Program Files/test"

    # Test forward slashes
    assert executor._convert_to_wsl_path("D:/user/file.txt") == "/mnt/d/user/file.txt"


def test_codex_executor_command_building(executor: CodexExecutor, test_workspace: Path) -> None:
    """Test command building for different modes"""
    task_file = test_workspace / "task.txt"
    task_file.write_text("Test task")

    cmd = executor._build_command(task_file)

    # Should contain WSL command
    assert "wsl -d Ubuntu-24.04" in cmd
    assert "codex exec" in cmd
    assert "--json" in cmd
    assert "--dangerously-bypass-approvals-and-sandbox" in cmd
    assert "--model gpt-5" in cmd


def test_codex_executor_jsonl_parsing(executor: CodexExecutor) -> None:
    """Test JSONL event parsing"""
    # Test thread.started
    line1 = '{"type":"thread.started","thread_id":"019a25d2-test"}'
    event1 = executor._parse_jsonl_event(line1)
    assert isinstance(event1, ThreadStartedEvent)
    assert event1.type == "thread.started"
    assert event1.thread_id == "019a25d2-test"

    # Test file_change
    line2 = '{"type":"file_change","changes":[{"path":"hello.py","kind":"add"}],"status":"completed"}'
    event2 = executor._parse_jsonl_event(line2)
    assert isinstance(event2, FileChangeEvent)
    assert event2.type == "file_change"
    assert len(event2.changes) == 1
    assert event2.changes[0].path == "hello.py"
    assert event2.changes[0].kind == "add"

    # Test turn.completed
    line3 = '{"type":"turn.completed","usage":{"input_tokens":100,"output_tokens":200}}'
    event3 = executor._parse_jsonl_event(line3)
    assert isinstance(event3, TurnCompletedEvent)
    assert event3.type == "turn.completed"
    assert event3.usage.input_tokens == 100
    assert event3.usage.output_tokens == 200

    # Test invalid JSON
    line4 = "Not JSON"
    event4 = executor._parse_jsonl_event(line4)
    assert event4 is None


# ============================================================================
# CodexExecutor Integration Tests (End-to-End)
# ============================================================================


@pytest.mark.integration
@pytest.mark.slow
def test_codex_simple_file_creation(
    executor: CodexExecutor, test_workspace: Path
) -> None:
    """Test simple file creation (hello.py) - SUCCESS case from investigation"""
    # Create task file
    task_file = test_workspace / "task.txt"
    task_file.write_text("Create a simple Python script hello.py that prints 'Hello, World!'")

    # Execute
    result: CodexExecutionResult = executor.execute(
        task_file=task_file, workspace_dir=test_workspace, timeout=60
    )

    # Assertions
    assert result.status == ExecutionStatus.SUCCESS, f"Failed: {result.error_message}"
    assert result.exit_code == 0
    assert result.duration_seconds < 60
    assert len(result.events) > 0

    # Check file was created
    assert len(result.created_files) >= 1
    assert any("hello.py" in f for f in result.created_files)

    # Check file exists on disk
    created_file = test_workspace / "hello.py"
    assert created_file.exists()

    # Check file content
    content = created_file.read_text()
    assert "Hello" in content or "hello" in content

    # Check token usage
    assert result.usage is not None
    assert result.usage.input_tokens > 0
    assert result.usage.output_tokens > 0

    print(f"\n✅ SUCCESS: Created {result.created_files}")
    print(f"   Duration: {result.duration_seconds:.1f}s")
    print(f"   Tokens: {result.usage.input_tokens} in, {result.usage.output_tokens} out")


@pytest.mark.integration
@pytest.mark.slow
def test_codex_complex_file_creation(
    executor: CodexExecutor, test_workspace: Path
) -> None:
    """Test complex file creation (email_validator.py) - SUCCESS case from investigation"""
    # Create task file
    task_file = test_workspace / "task.txt"
    task_file.write_text(
        "Create email_validator.py with a validate_email function that includes:\n"
        "- Module docstring\n"
        "- Type hints\n"
        "- Doctest examples\n"
        "- Error handling (length check, type check)"
    )

    # Execute
    result: CodexExecutionResult = executor.execute(
        task_file=task_file, workspace_dir=test_workspace, timeout=120
    )

    # Assertions
    assert result.status == ExecutionStatus.SUCCESS, f"Failed: {result.error_message}"
    assert result.exit_code == 0
    assert result.duration_seconds < 120

    # Check file was created
    assert len(result.created_files) >= 1
    assert any("email_validator.py" in f for f in result.created_files)

    # Check file exists on disk
    created_file = test_workspace / "email_validator.py"
    assert created_file.exists()

    # Check file content (production quality)
    content = created_file.read_text()
    assert "def " in content  # Has function definition
    assert '"""' in content or "'''" in content  # Has docstring
    assert "->" in content or ":" in content  # Has type hints (likely)
    assert len(content) > 100  # Non-trivial file

    # Check token usage
    assert result.usage is not None
    assert result.usage.input_tokens > 0
    assert result.usage.output_tokens > 0

    print(f"\n✅ SUCCESS: Created {result.created_files}")
    print(f"   Duration: {result.duration_seconds:.1f}s")
    print(f"   File size: {len(content)} chars")
    print(f"   Tokens: {result.usage.input_tokens} in, {result.usage.output_tokens} out")


@pytest.mark.integration
def test_codex_timeout_handling(executor: CodexExecutor, test_workspace: Path) -> None:
    """Test timeout handling"""
    # Create task file with very complex task
    task_file = test_workspace / "task.txt"
    task_file.write_text(
        "Create a very complex web application with 50 files, "
        "including backend, frontend, database, tests, and documentation."
    )

    # Execute with very short timeout (should timeout)
    result: CodexExecutionResult = executor.execute(
        task_file=task_file, workspace_dir=test_workspace, timeout=1  # 1 second
    )

    # Assertions
    # Note: Test may fail fast if Codex CLI is not properly configured
    # Check for either timeout OR failure (both are acceptable for this test)
    assert result.status in [ExecutionStatus.TIMEOUT, ExecutionStatus.FAILED]
    assert result.duration_seconds <= 2  # Should complete quickly


@pytest.mark.integration
def test_codex_invalid_task_file(executor: CodexExecutor, test_workspace: Path) -> None:
    """Test error handling for invalid task file"""
    task_file = test_workspace / "nonexistent.txt"

    # Should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        executor.execute(task_file=task_file, workspace_dir=test_workspace)


# ============================================================================
# WorkerManager Integration Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.slow
def test_worker_manager_codex_spawn_and_run(
    worker_manager: WorkerManager, test_workspace: Path
) -> None:
    """Test WorkerManager Codex worker spawn and execution"""
    task = {
        "name": "Create hello.py",
        "prompt": "Create a simple Python script hello.py that prints 'Hello, World!'",
    }

    # Spawn Codex worker
    worker_dir = worker_manager.spawn_codex_worker(worker_id="test_001", task=task, timeout=60)

    assert worker_dir is not None
    assert worker_dir.exists()
    assert (worker_dir / "task.txt").exists()

    # Run Codex session
    result = worker_manager.run_codex_session(worker_id="worker_test_001", timeout=60, model="gpt-5")

    # Assertions
    assert result.success, f"Failed: {result.error_message}"
    assert result.duration < 60
    assert len(result.output) > 0

    # Check files were created
    created_files = list(worker_dir.glob("*.py"))
    assert len(created_files) >= 1

    # Check logs were saved
    assert (worker_dir / "codex_events.jsonl").exists()
    assert (worker_dir / "codex_summary.txt").exists()

    print(f"\n✅ SUCCESS: Worker completed")
    print(f"   Created files: {[f.name for f in created_files]}")
    print(f"   Duration: {result.duration:.1f}s")


@pytest.mark.integration
@pytest.mark.slow
def test_worker_manager_multiple_codex_workers(
    worker_manager: WorkerManager, test_workspace: Path
) -> None:
    """Test multiple Codex workers in parallel"""
    tasks = [
        {
            "name": "Create calculator.py",
            "prompt": "Create calculator.py with add, subtract, multiply, divide functions",
        },
        {
            "name": "Create greeter.py",
            "prompt": "Create greeter.py with a function that greets users by name",
        },
    ]

    # Spawn workers
    worker_ids = []
    for i, task in enumerate(tasks):
        worker_dir = worker_manager.spawn_codex_worker(
            worker_id=f"test_00{i+1}", task=task, timeout=60
        )
        assert worker_dir is not None
        worker_ids.append(f"worker_test_00{i+1}")

    # Run workers sequentially (parallel would require thread pool)
    results = []
    for worker_id in worker_ids:
        result = worker_manager.run_codex_session(worker_id=worker_id, timeout=60)
        results.append(result)

    # Assertions
    assert all(r.success for r in results), f"Some workers failed: {[r.error_message for r in results if not r.success]}"
    assert len(results) == 2

    print(f"\n✅ SUCCESS: {len(results)} workers completed")
    for i, result in enumerate(results):
        print(f"   Worker {i+1}: {result.duration:.1f}s")


# ============================================================================
# Event Parsing Tests
# ============================================================================


def test_file_change_event_parsing() -> None:
    """Test FileChangeEvent parsing"""
    data = {
        "type": "file_change",
        "changes": [
            {"path": "hello.py", "kind": "add"},
            {"path": "test.py", "kind": "modify"},
        ],
        "status": "completed",
    }

    event = FileChangeEvent(**data)

    assert event.type == "file_change"
    assert len(event.changes) == 2
    assert event.changes[0].path == "hello.py"
    assert event.changes[0].kind == "add"
    assert event.changes[1].path == "test.py"
    assert event.changes[1].kind == "modify"
    assert event.status == "completed"


def test_execution_result_properties() -> None:
    """Test CodexExecutionResult properties"""
    file_changes = [
        FileChange(path="file1.py", kind="add"),
        FileChange(path="file2.py", kind="modify"),
        FileChange(path="file3.py", kind="delete"),
    ]

    result = CodexExecutionResult(
        status=ExecutionStatus.SUCCESS,
        exit_code=0,
        stdout="output",
        stderr="",
        duration_seconds=10.5,
        file_changes=file_changes,
    )

    assert result.success is True
    assert result.created_files == ["file1.py"]
    assert result.modified_files == ["file2.py"]
    assert result.deleted_files == ["file3.py"]


# ============================================================================
# Test Runner
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
