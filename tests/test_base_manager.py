"""
Unit Tests for BaseAIManager

Tests the abstract base class functionality including:
- Lifecycle management (start, stop, restart)
- Health checking
- Confirmation handling
- Metrics collection
- Status management

Author: Claude (Sonnet 4.5)
Created: 2025 - 10 - 24
"""

import time
from pathlib import Path
from typing import Optional

import pytest

from orchestrator.config import OrchestratorConfig
from orchestrator.core.common.base_manager import (
    BaseAIManager,
    HealthCheckResult,
    ManagerMetrics,
    ManagerStatus,
    ManagerType,
)
from orchestrator.core.common.models import ConfirmationRequest, ConfirmationType
from orchestrator.interfaces import ILogger

# =============================================================================
# Test Fixtures
# =============================================================================


class MockLogger:
    """Mock logger for testing"""

    def __init__(self):
        self.logs = []

    def info(self, message: str, **kwargs):
        self.logs.append(("INFO", message, kwargs))

    def error(self, message: str, **kwargs):
        self.logs.append(("ERROR", message, kwargs))

    def warning(self, message: str, **kwargs):
        self.logs.append(("WARNING", message, kwargs))

    def debug(self, message: str, **kwargs):
        self.logs.append(("DEBUG", message, kwargs))


class ConcreteTestManager(BaseAIManager):
    """Concrete implementation of BaseAIManager for testing"""

    def __init__(self, config: OrchestratorConfig, logger: ILogger, manager_id: str):
        super().__init__(
            config=config,
            logger=logger,
            manager_id=manager_id,
            manager_type=ManagerType.WORKER,
        )
        self.start_called = False
        self.stop_called = False
        self.should_fail_start = False
        self.should_fail_stop = False

    def start(self) -> bool:
        self.start_called = True
        if self.should_fail_start:
            return False
        self._mark_started()
        return True

    def stop(self) -> bool:
        self.stop_called = True
        if self.should_fail_stop:
            return False
        self._mark_stopped()
        return True

    def _health_check_impl(self) -> HealthCheckResult:
        return HealthCheckResult(
            is_healthy=True,
            status=self.status,
            message="Test manager healthy",
            checks_passed=3,
            checks_failed=0,
            details={"test": "ok"},
        )

    def _handle_confirmation_impl(self, confirmation: ConfirmationRequest) -> Optional[str]:
        # Auto - approve file writes, deny deletes
        if confirmation.confirmation_type == ConfirmationType.FILE_WRITE:
            return "yes"
        elif confirmation.confirmation_type == ConfirmationType.FILE_DELETE:
            return "no"
        return None


@pytest.fixture
def config(tmp_path):
    """Create test configuration"""
    config = OrchestratorConfig(
        workspace_root=str(tmp_path / "workspace"),
        max_workers=4,
        default_timeout=300,
    )
    return config


@pytest.fixture
def logger():
    """Create mock logger"""
    return MockLogger()


@pytest.fixture
def manager(config, logger):
    """Create test manager instance"""
    return ConcreteTestManager(
        config=config,
        logger=logger,
        manager_id="test_manager_001",
    )


# =============================================================================
# Initialization Tests
# =============================================================================


def test_base_manager_initialization(manager, config):
    """Test BaseAIManager initializes correctly"""
    assert manager.manager_id == "test_manager_001"
    assert manager.manager_type == ManagerType.WORKER
    assert manager.status == ManagerStatus.READY
    assert manager.config == config
    assert manager.workspace_root == Path(config.workspace_root)
    assert manager.get_uptime() == 0.0


def test_base_manager_creates_workspace(manager):
    """Test workspace directory is created"""
    assert manager.workspace_root.exists()
    assert manager.workspace_root.is_dir()


# =============================================================================
# Lifecycle Tests
# =============================================================================


def test_start_manager(manager):
    """Test starting manager"""
    result = manager.start()

    assert result is True
    assert manager.start_called is True
    assert manager.status == ManagerStatus.RUNNING
    assert manager.get_uptime() > 0


def test_stop_manager(manager):
    """Test stopping manager"""
    manager.start()
    result = manager.stop()

    assert result is True
    assert manager.stop_called is True
    assert manager.status == ManagerStatus.STOPPED


def test_restart_manager(manager):
    """Test restarting manager"""
    manager.start()
    original_start_time = manager._start_time

    time.sleep(0.1)  # Brief delay

    result = manager.restart()

    assert result is True
    assert manager.start_called is True
    assert manager.stop_called is True
    assert manager.status == ManagerStatus.RUNNING
    assert manager._start_time > original_start_time


def test_restart_fails_if_stop_fails(manager):
    """Test restart fails if stop fails"""
    manager.start()
    manager.should_fail_stop = True

    result = manager.restart()

    assert result is False


def test_restart_fails_if_start_fails(manager):
    """Test restart fails if start fails after stop"""
    manager.start()
    manager.should_fail_start = True

    result = manager.restart()

    assert result is False


# =============================================================================
# Status Management Tests
# =============================================================================


def test_get_status(manager):
    """Test getting manager status"""
    assert manager.get_status() == ManagerStatus.READY

    manager.start()
    assert manager.get_status() == ManagerStatus.RUNNING

    manager.stop()
    assert manager.get_status() == ManagerStatus.STOPPED


def test_pause_manager(manager):
    """Test pausing manager"""
    manager.start()
    result = manager.pause()

    assert result is True
    assert manager.status == ManagerStatus.PAUSED


def test_pause_fails_if_not_running(manager):
    """Test pause fails if manager not running"""
    result = manager.pause()
    assert result is False


def test_resume_manager(manager):
    """Test resuming paused manager"""
    manager.start()
    manager.pause()

    result = manager.resume()

    assert result is True
    assert manager.status == ManagerStatus.RUNNING


def test_resume_fails_if_not_paused(manager):
    """Test resume fails if not paused"""
    manager.start()
    result = manager.resume()
    assert result is False


# =============================================================================
# Health Check Tests
# =============================================================================


def test_health_check(manager):
    """Test health check"""
    manager.start()
    health = manager.health_check()

    assert isinstance(health, HealthCheckResult)
    assert health.is_healthy is True
    assert health.status == ManagerStatus.RUNNING
    assert health.checks_passed == 3
    assert health.checks_failed == 0
    assert "uptime_seconds" in health.details
    assert "status" in health.details
    assert "last_activity_age_seconds" in health.details


def test_health_check_handles_exceptions(manager):
    """Test health check handles exceptions gracefully"""

    # Override _health_check_impl to raise exception
    def failing_health_check():
        raise RuntimeError("Test error")

    manager._health_check_impl = failing_health_check

    health = manager.health_check()

    assert health.is_healthy is False
    assert health.status == ManagerStatus.ERROR
    assert "exception" in health.details


# =============================================================================
# Metrics Tests
# =============================================================================


def test_get_metrics(manager):
    """Test getting manager metrics"""
    manager.start()
    metrics = manager.get_metrics()

    assert isinstance(metrics, ManagerMetrics)
    assert metrics.manager_id == "test_manager_001"
    assert metrics.manager_type == ManagerType.WORKER
    assert metrics.status == ManagerStatus.RUNNING
    assert metrics.uptime_seconds > 0
    assert metrics.total_operations == 0


def test_metrics_track_operations(manager):
    """Test metrics track operations"""
    manager.start()

    # Simulate operations
    manager._increment_operation()
    manager._increment_success()
    manager._increment_operation()
    manager._increment_failure()

    metrics = manager.get_metrics()

    assert metrics.total_operations == 2
    assert metrics.successful_operations == 1
    assert metrics.failed_operations == 1


# =============================================================================
# Confirmation Handling Tests
# =============================================================================


def test_handle_confirmation_file_write(manager):
    """Test handling file write confirmation"""
    manager.start()

    confirmation = ConfirmationRequest(
        worker_id="worker_001",
        confirmation_type=ConfirmationType.FILE_WRITE,
        message="Write to file test.txt?",
        details={"file": "test.txt"},
        timestamp=time.time(),
    )

    response = manager.handle_confirmation(confirmation)

    assert response == "yes"
    assert manager._confirmation_count == 1
    assert manager._success_count == 1


def test_handle_confirmation_file_delete(manager):
    """Test handling file delete confirmation"""
    manager.start()

    confirmation = ConfirmationRequest(
        worker_id="worker_001",
        confirmation_type=ConfirmationType.FILE_DELETE,
        message="Delete file test.txt?",
        details={"file": "test.txt"},
        timestamp=time.time(),
    )

    response = manager.handle_confirmation(confirmation)

    assert response == "no"
    assert manager._confirmation_count == 1


def test_handle_confirmation_exception_returns_no(manager):
    """Test confirmation handling exception returns 'no' for safety"""
    manager.start()

    # Override to raise exception
    def failing_confirmation(conf):
        raise RuntimeError("Test error")

    manager._handle_confirmation_impl = failing_confirmation

    confirmation = ConfirmationRequest(
        worker_id="worker_001",
        confirmation_type=ConfirmationType.COMMAND_EXECUTE,
        message="Execute command?",
        details={},
        timestamp=time.time(),
    )

    response = manager.handle_confirmation(confirmation)

    assert response == "no"
    assert manager._failure_count == 1


# =============================================================================
# Uptime Tests
# =============================================================================


def test_get_uptime_before_start(manager):
    """Test uptime is 0 before start"""
    assert manager.get_uptime() == 0.0


def test_get_uptime_while_running(manager):
    """Test uptime increases while running"""
    manager.start()
    time.sleep(0.1)
    uptime = manager.get_uptime()

    assert uptime > 0.1
    assert uptime < 1.0  # Should be less than 1 second


def test_get_uptime_after_stop(manager):
    """Test uptime is fixed after stop"""
    manager.start()
    time.sleep(0.1)
    manager.stop()

    uptime1 = manager.get_uptime()
    time.sleep(0.1)
    uptime2 = manager.get_uptime()

    # Uptime should not change after stop
    assert uptime1 == pytest.approx(uptime2, abs=0.01)


# =============================================================================
# Terminal Output Tests
# =============================================================================


def test_write_terminal_output(manager, tmp_path):
    """Test writing terminal output to file"""
    log_file = tmp_path / "test_output.log"

    result = manager.write_terminal_output(
        output_text="Test output line 1\nTest output line 2\n",
        log_file=log_file,
        strip_ansi=False,
    )

    assert result is True
    assert log_file.exists()

    content = log_file.read_text(encoding="utf - 8")
    assert "Test output line 1" in content
    assert "Test output line 2" in content


def test_write_terminal_output_strips_ansi(manager, tmp_path):
    """Test ANSI code stripping in terminal output"""
    log_file = tmp_path / "test_output.log"

    # Output with ANSI codes
    output_with_ansi = "\x1b[32mGreen text\x1b[0m\nNormal text\n"

    result = manager.write_terminal_output(
        output_text=output_with_ansi,
        log_file=log_file,
        strip_ansi=True,
    )

    assert result is True

    content = log_file.read_text(encoding="utf - 8")
    assert "\x1b" not in content  # ANSI codes removed
    assert "Green text" in content
    assert "Normal text" in content


@pytest.mark.skip(reason="Environment - dependent test")
def test_write_terminal_output_handles_errors(manager, tmp_path):
    """Test terminal output handles write errors"""
    # Try to write to invalid path
    log_file = Path("/invalid / path / test.log")

    result = manager.write_terminal_output(
        output_text="Test",
        log_file=log_file,
        strip_ansi=False,
    )

    assert result is False


# =============================================================================
# Logging Tests
# =============================================================================


def test_log_event(manager, logger):
    """Test logging events"""
    manager.log_event(
        event_type="test_event",
        message="Test message",
        extra_data="test_value",
    )

    assert len(logger.logs) > 0
    log_entry = logger.logs[-1]
    assert log_entry[0] == "INFO"
    assert "Test message" in log_entry[1]
    assert log_entry[2]["event_type"] == "test_event"
    assert log_entry[2]["extra_data"] == "test_value"


# =============================================================================
# String Representation Tests
# =============================================================================


def test_manager_repr(manager):
    """Test string representation"""
    manager.start()
    repr_str = repr(manager)

    assert "ConcreteTestManager" in repr_str
    assert "test_manager_001" in repr_str
    assert "worker" in repr_str.lower()
    assert "running" in repr_str.lower()


# =============================================================================
# Abstract Method Enforcement Tests
# =============================================================================


def test_cannot_instantiate_base_manager_directly(config, logger):
    """Test BaseAIManager cannot be instantiated directly"""
    with pytest.raises(TypeError):
        BaseAIManager(
            config=config,
            logger=logger,
            manager_id="test",
            manager_type=ManagerType.WORKER,
        )


def test_derived_class_must_implement_start():
    """Test derived class must implement start()"""

    class IncompleteManager(BaseAIManager):
        def stop(self) -> bool:
            return True

        def _health_check_impl(self) -> HealthCheckResult:
            return HealthCheckResult(True, ManagerStatus.READY, "ok", 1, 0)

        def _handle_confirmation_impl(self, confirmation) -> Optional[str]:
            return "yes"

    # Should raise TypeError when trying to instantiate
    with pytest.raises(TypeError):
        config = OrchestratorConfig(workspace_root="/tmp / test", default_timeout=300)
        logger = MockLogger()
        IncompleteManager(config, logger, "test", ManagerType.WORKER)


# =============================================================================
# Integration Tests
# =============================================================================


def test_full_lifecycle_integration(manager):
    """Test full lifecycle: start -> operate -> stop"""
    # Start
    assert manager.start() is True
    assert manager.status == ManagerStatus.RUNNING

    # Operate
    health = manager.health_check()
    assert health.is_healthy is True

    metrics_before = manager.get_metrics()

    confirmation = ConfirmationRequest(
        worker_id="worker_001",
        confirmation_type=ConfirmationType.FILE_WRITE,
        message="Write file?",
        details={},
        timestamp=time.time(),
    )
    response = manager.handle_confirmation(confirmation)
    assert response == "yes"

    metrics_after = manager.get_metrics()
    assert metrics_after.total_operations > metrics_before.total_operations

    # Stop
    assert manager.stop() is True
    assert manager.status == ManagerStatus.STOPPED
    assert manager.get_uptime() > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
