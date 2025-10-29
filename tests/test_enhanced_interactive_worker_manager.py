"""
Comprehensive Unit Tests for WorkerManager (Unified Implementation)

Tests all major functionality with mocks to avoid requiring actual Claude CLI.
"""

import sys
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, Mock, call, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.config import OrchestratorConfig
from orchestrator.core.exceptions import PatternMatchError, WorkerSpawnError, WorkerTimeoutError
from orchestrator.core.worker.worker_manager import (
    ConfirmationRequest,
    ConfirmationType,
    WorkerManager,
    WorkerSession,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_config():
    """Create mock configuration"""
    config = Mock(spec=OrchestratorConfig)
    config.workspace_root = "./workspace"
    config.execution_mode = "windows"
    config.windows_claude_path = "claude"
    config.git_bash_path = None
    return config


@pytest.fixture
def mock_logger():
    """Create mock logger"""
    logger = Mock()
    logger.log_worker_spawn = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def mock_user_callback():
    """Create mock user approval callback"""
    return Mock(return_value=True)


@pytest.fixture
def manager(mock_config, mock_logger, mock_user_callback):
    """Create WorkerManager instance"""
    return WorkerManager(
        config=mock_config, logger=mock_logger, user_approval_callback=mock_user_callback
    )


# ============================================================================
# Initialization Tests
# ============================================================================


class TestInitialization:
    """Test manager initialization"""

    def test_manager_creation(self, manager):
        """Test manager can be created"""
        assert manager is not None
        assert manager.config is not None
        assert manager.logger is not None
        assert manager.user_approval_callback is not None

    def test_platform_detection(self, manager):
        """Test platform is detected correctly"""
        assert manager.platform in ["windows", "unix"]

    def test_confirmation_patterns_loaded(self, manager):
        """Test confirmation patterns are loaded"""
        assert len(manager.confirmation_patterns) > 0
        assert all(len(p) == 2 for p in manager.confirmation_patterns)

    def test_workers_dict_initialized(self, manager):
        """Test workers dictionary is initialized"""
        assert isinstance(manager.workers, dict)
        assert len(manager.workers) == 0


# ============================================================================
# Command Building Tests
# ============================================================================


class TestCommandBuilding:
    """Test command building for different platforms"""

    def test_build_command_windows(self, manager):
        """Test command building for Windows"""
        task_file = "workspace / task.txt"
        cmd = manager._build_command(task_file)

        assert "claude" in cmd.lower()
        assert "--print" in cmd
        assert task_file in cmd

    def test_build_command_with_git_bash(self, mock_config, mock_logger):
        """Test command building with Git Bash"""
        mock_config.git_bash_path = "C:\\Program Files\\Git\\bin\\bash.exe"

        manager = WorkerManager(config=mock_config, logger=mock_logger)

        cmd = manager._build_command("task.txt")

        assert "bash.exe" in cmd
        assert "CLAUDE_CODE_GIT_BASH_PATH" in cmd


# ============================================================================
# Confirmation Detection Tests
# ============================================================================


class TestConfirmationDetection:
    """Test confirmation request detection"""

    def test_detect_file_write_confirmation(self, manager):
        """Test detection of file write confirmation"""
        # Create mock child process
        mock_child = Mock()
        mock_child.after = "Write to file 'output.py'?"
        mock_child.match = Mock()
        mock_child.match.groups = Mock(return_value=("output.py",))
        mock_child.match.group = Mock(return_value="output.py")

        pattern_index = 0  # FILE_WRITE pattern
        confirmation = manager._parse_confirmation("worker_1", pattern_index, mock_child)

        assert confirmation is not None
        assert confirmation.confirmation_type == ConfirmationType.FILE_WRITE
        assert confirmation.details.get("file") == "output.py"

    def test_detect_file_delete_confirmation(self, manager):
        """Test detection of file delete confirmation"""
        mock_child = Mock()
        mock_child.after = "Delete file 'temp.txt'?"
        mock_child.match = Mock()
        mock_child.match.groups = Mock(return_value=("temp.txt",))
        mock_child.match.group = Mock(return_value="temp.txt")

        # Find DELETE pattern index
        pattern_index = next(
            i
            for i, (_, t) in enumerate(manager.confirmation_patterns)
            if t == ConfirmationType.FILE_DELETE
        )

        confirmation = manager._parse_confirmation("worker_1", pattern_index, mock_child)

        assert confirmation is not None
        assert confirmation.confirmation_type == ConfirmationType.FILE_DELETE
        assert confirmation.details.get("file") == "temp.txt"

    def test_detect_command_execute_confirmation(self, manager):
        """Test detection of command execution confirmation"""
        mock_child = Mock()
        mock_child.after = "Execute command 'ls -la'?"
        mock_child.match = Mock()
        mock_child.match.groups = Mock(return_value=("ls -la",))
        mock_child.match.group = Mock(return_value="ls -la")

        # Find COMMAND_EXECUTE pattern index
        pattern_index = next(
            i
            for i, (_, t) in enumerate(manager.confirmation_patterns)
            if t == ConfirmationType.COMMAND_EXECUTE
        )

        confirmation = manager._parse_confirmation("worker_1", pattern_index, mock_child)

        assert confirmation is not None
        assert confirmation.confirmation_type == ConfirmationType.COMMAND_EXECUTE
        assert confirmation.details.get("command") == "ls -la"


# ============================================================================
# Confirmation Handling Tests
# ============================================================================


class TestConfirmationHandling:
    """Test confirmation request handling"""

    @patch("orchestrator.core.common.ai_safety_judge.AISafetyJudge")
    def test_handle_safe_file_write(self, mock_judge_class, manager):
        """Test handling of safe file write"""
        # Mock AI safety judge
        mock_judge = Mock()
        mock_judgment = Mock()
        mock_judgment.should_approve = True
        mock_judgment.should_escalate = False
        mock_judgment.level = "safe"
        mock_judgment.reasoning = "Safe file write to workspace"
        mock_judge.judge_confirmation = Mock(return_value=mock_judgment)
        mock_judge_class.return_value = mock_judge

        # Create confirmation
        confirmation = ConfirmationRequest(
            worker_id="worker_1",
            confirmation_type=ConfirmationType.FILE_WRITE,
            message="Write to file 'output.py'?",
            details={"file": "workspace / output.py"},
        )

        # Handle confirmation
        response = manager._handle_confirmation(confirmation)

        # Safe operations are auto - approved without calling the judge
        assert response == "yes"
        # For SAFE operations, the judge should NOT be called (auto - approved)
        mock_judge.judge_confirmation.assert_not_called()

    @patch("orchestrator.core.common.ai_safety_judge.AISafetyJudge")
    def test_handle_dangerous_operation_with_user_approval(self, mock_judge_class, manager):
        """Test handling of dangerous operation with user approval"""
        # Mock AI safety judge
        mock_judge = Mock()
        mock_judgment = Mock()
        mock_judgment.should_approve = False
        mock_judgment.should_escalate = True
        mock_judgment.level = "dangerous"
        mock_judgment.reasoning = "Delete operation requires approval"
        mock_judge.judge_confirmation = Mock(return_value=mock_judgment)
        mock_judge_class.return_value = mock_judge

        # Mock user approval
        manager.user_approval_callback = Mock(return_value=True)

        # Create confirmation
        confirmation = ConfirmationRequest(
            worker_id="worker_1",
            confirmation_type=ConfirmationType.FILE_DELETE,
            message="Delete file 'temp.txt'?",
            details={"file": "workspace / temp.txt"},
        )

        # Handle confirmation
        response = manager._handle_confirmation(confirmation)

        assert response == "yes"
        manager.user_approval_callback.assert_called_once_with(confirmation)

    @patch("orchestrator.core.common.ai_safety_judge.AISafetyJudge")
    def test_handle_dangerous_operation_denied_by_user(self, mock_judge_class, manager):
        """Test handling of dangerous operation denied by user"""
        # Mock AI safety judge
        mock_judge = Mock()
        mock_judgment = Mock()
        mock_judgment.should_approve = False
        mock_judgment.should_escalate = True
        mock_judgment.level = "dangerous"
        mock_judge.judge_confirmation = Mock(return_value=mock_judgment)
        mock_judge_class.return_value = mock_judge

        # Mock user denial
        manager.user_approval_callback = Mock(return_value=False)

        # Create confirmation
        confirmation = ConfirmationRequest(
            worker_id="worker_1",
            confirmation_type=ConfirmationType.FILE_DELETE,
            message="Delete file 'important.txt'?",
            details={"file": "important.txt"},
        )

        # Handle confirmation
        response = manager._handle_confirmation(confirmation)

        assert response == "no"


# ============================================================================
# ConfirmationRequest Tests
# ============================================================================


class TestConfirmationRequest:
    """Test ConfirmationRequest dataclass"""

    def test_create_confirmation_request(self):
        """Test creating confirmation request"""
        conf = ConfirmationRequest(
            worker_id="worker_1",
            confirmation_type=ConfirmationType.FILE_WRITE,
            message="Write to file?",
            details={"file": "output.txt"},
        )

        assert conf.worker_id == "worker_1"
        assert conf.confirmation_type == ConfirmationType.FILE_WRITE
        assert conf.message == "Write to file?"
        assert conf.details == {"file": "output.txt"}
        assert conf.timestamp > 0

    def test_is_dangerous_file_delete(self):
        """Test is_dangerous for file delete"""
        conf = ConfirmationRequest(
            worker_id="worker_1",
            confirmation_type=ConfirmationType.FILE_DELETE,
            message="Delete file?",
            details={},
        )

        assert conf.is_dangerous() is True

    def test_is_dangerous_command_execute(self):
        """Test is_dangerous for command execute"""
        conf = ConfirmationRequest(
            worker_id="worker_1",
            confirmation_type=ConfirmationType.COMMAND_EXECUTE,
            message="Execute command?",
            details={},
        )

        assert conf.is_dangerous() is True

    def test_is_not_dangerous_file_write(self):
        """Test is_dangerous for file write"""
        conf = ConfirmationRequest(
            worker_id="worker_1",
            confirmation_type=ConfirmationType.FILE_WRITE,
            message="Write to file?",
            details={},
        )

        assert conf.is_dangerous() is False


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_workers_dictionary_management(self, manager):
        """Test workers are properly tracked"""
        # Create mock session
        session = WorkerSession(
            worker_id="worker_1",
            task_name="Test Task",
            child_process=Mock(),
            started_at=1234567890.0,
        )

        # Add to manager
        manager.workers["worker_1"] = session

        # Verify
        assert "worker_1" in manager.workers
        assert manager.workers["worker_1"].task_name == "Test Task"

    def test_multiple_workers(self, manager):
        """Test managing multiple workers"""
        sessions = []

        for i in range(3):
            session = WorkerSession(
                worker_id=f"worker_{i}",
                task_name=f"Task {i}",
                child_process=Mock(),
                started_at=1234567890.0 + i,
            )
            sessions.append(session)
            manager.workers[f"worker_{i}"] = session

        assert len(manager.workers) == 3
        assert all(f"worker_{i}" in manager.workers for i in range(3))


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error scenarios"""

    def test_parse_confirmation_with_no_groups(self, manager):
        """Test parsing confirmation with no regex groups"""
        mock_child = Mock()
        mock_child.after = "Proceed?"
        mock_child.match = Mock()
        mock_child.match.groups = Mock(return_value=())

        # Use PERMISSION_REQUEST pattern (no groups)
        pattern_index = next(
            i
            for i, (_, t) in enumerate(manager.confirmation_patterns)
            if t == ConfirmationType.PERMISSION_REQUEST
        )

        confirmation = manager._parse_confirmation("worker_1", pattern_index, mock_child)

        assert confirmation is not None
        assert confirmation.confirmation_type == ConfirmationType.PERMISSION_REQUEST
        assert confirmation.details == {}

    def test_handle_confirmation_without_user_callback(self, mock_config, mock_logger):
        """Test handling confirmation without user callback"""
        manager = WorkerManager(config=mock_config, logger=mock_logger, user_approval_callback=None)

        with patch("orchestrator.core.common.ai_safety_judge.AISafetyJudge") as mock_judge_class:
            # Mock dangerous judgment
            mock_judge = Mock()
            mock_judgment = Mock()
            mock_judgment.should_approve = False
            mock_judgment.should_escalate = True
            mock_judgment.level = "dangerous"
            mock_judge.judge_confirmation = Mock(return_value=mock_judgment)
            mock_judge_class.return_value = mock_judge

            confirmation = ConfirmationRequest(
                worker_id="worker_1",
                confirmation_type=ConfirmationType.FILE_DELETE,
                message="Delete?",
                details={},
            )

            # Should deny without user callback
            response = manager._handle_confirmation(confirmation)
            assert response == "no"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
