"""
Base AI Manager - Abstract base class for AI instance managers.

This module provides the foundational architecture for managing AI instances
(both Worker AI and Supervisor/Manager AI) with standardized lifecycle,
monitoring, and safety features.

Architecture:
    BaseAIManager (ABC)
    ├── WorkerAIManager (concrete) - Manages Claude worker instances
    └── SupervisorAIManager (concrete) - Manages Claude Code monitoring

Design Principles:
    1. Separation of Concerns - Common functionality in base, specific in derived
    2. Template Method Pattern - Base defines workflow, derived customizes steps
    3. Dependency Injection - Config and logger injected via constructor
    4. Type Safety - Comprehensive type hints for all methods
    5. Observability - Built-in metrics and logging

Author: Claude (Sonnet 4.5)
Created: 2025-10-24
Version: 1.0.0
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from orchestrator.config import OrchestratorConfig
from orchestrator.core.common.metrics import MetricsCollector
from orchestrator.core.common.models import ConfirmationRequest
from orchestrator.interfaces import ILogger
from orchestrator.utils.ansi_utils import strip_ansi_codes


class ManagerType(str, Enum):
    """Type of AI manager"""

    WORKER = "worker"  # Worker AI instance manager
    SUPERVISOR = "supervisor"  # Supervisor/Manager AI monitor


class ManagerStatus(str, Enum):
    """Status of AI manager"""

    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class HealthCheckResult:
    """Health check result for AI manager"""

    is_healthy: bool
    status: ManagerStatus
    message: str
    checks_passed: int
    checks_failed: int
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ManagerMetrics:
    """Common metrics for AI managers"""

    manager_id: str
    manager_type: ManagerType
    status: ManagerStatus
    uptime_seconds: float
    total_operations: int
    successful_operations: int
    failed_operations: int
    confirmations_handled: int
    last_activity_time: float
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


class BaseAIManager(ABC):
    """
    Abstract base class for AI instance managers.

    This class provides common functionality for managing AI instances,
    including lifecycle management, monitoring, metrics collection,
    and confirmation handling.

    Derived classes must implement:
        - start() - Start the AI instance(s)
        - stop() - Stop the AI instance(s)
        - _health_check_impl() - Perform health check
        - _handle_confirmation_impl() - Handle confirmation requests

    Example:
        >>> class MyAIManager(BaseAIManager):
        ...     def start(self) -> bool:
        ...         # Custom start logic
        ...         return True
        ...
        ...     def stop(self) -> bool:
        ...         # Custom stop logic
        ...         return True
        ...
        ...     def _health_check_impl(self) -> HealthCheckResult:
        ...         # Custom health check
        ...         return HealthCheckResult(is_healthy=True, ...)

    Attributes:
        config: Orchestrator configuration
        logger: Logger instance
        manager_id: Unique identifier for this manager
        manager_type: Type of manager (WORKER or SUPERVISOR)
        status: Current status of the manager
        metrics: Metrics collector instance
    """

    def __init__(
        self,
        config: OrchestratorConfig,
        logger: ILogger,
        manager_id: str,
        manager_type: ManagerType,
    ):
        """
        Initialize base AI manager.

        Args:
            config: Orchestrator configuration
            logger: Logger instance for structured logging
            manager_id: Unique identifier for this manager instance
            manager_type: Type of manager (WORKER or SUPERVISOR)
        """
        self.config = config
        self.logger = logger
        self.manager_id = manager_id
        self.manager_type = manager_type
        self.status = ManagerStatus.INITIALIZING

        # Workspace management
        self.workspace_root = Path(config.workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)

        # Metrics collection
        self.metrics = MetricsCollector(workspace_root=self.workspace_root)

        # Lifecycle tracking
        self._start_time: Optional[float] = None
        self._stop_time: Optional[float] = None
        self._operation_count = 0
        self._success_count = 0
        self._failure_count = 0
        self._confirmation_count = 0
        self._last_activity_time = time.time()

        # Update status
        self.status = ManagerStatus.READY

        self.logger.info(
            f"BaseAIManager initialized",
            manager_id=manager_id,
            manager_type=manager_type.value,
            workspace=str(self.workspace_root),
        )

    # =============================================================================
    # Abstract Methods - Must be implemented by derived classes
    # =============================================================================

    @abstractmethod
    def start(self) -> bool:
        """
        Start the AI manager and its managed instances.

        This method should:
        1. Initialize necessary resources
        2. Start AI instance(s)
        3. Begin monitoring/communication loops
        4. Update status to RUNNING

        Returns:
            True if started successfully, False otherwise

        Raises:
            NotImplementedError: If not implemented by derived class
        """
        pass

    @abstractmethod
    def stop(self) -> bool:
        """
        Stop the AI manager and its managed instances.

        This method should:
        1. Gracefully stop AI instance(s)
        2. Clean up resources
        3. Save final state/metrics
        4. Update status to STOPPED

        Returns:
            True if stopped successfully, False otherwise

        Raises:
            NotImplementedError: If not implemented by derived class
        """
        pass

    @abstractmethod
    def _health_check_impl(self) -> HealthCheckResult:
        """
        Perform manager-specific health check.

        This method should check:
        - AI instance(s) are responsive
        - Resources are available
        - Communication channels are working
        - Any manager-specific health indicators

        Returns:
            HealthCheckResult with detailed health status

        Raises:
            NotImplementedError: If not implemented by derived class
        """
        pass

    @abstractmethod
    def _handle_confirmation_impl(self, confirmation: ConfirmationRequest) -> Optional[str]:
        """
        Handle confirmation request (manager-specific logic).

        This method should:
        1. Evaluate the confirmation request
        2. Apply safety policies
        3. Make approval decision
        4. Return appropriate response

        Args:
            confirmation: The confirmation request to handle

        Returns:
            Response string ("yes"/"no") or None if no response needed

        Raises:
            NotImplementedError: If not implemented by derived class
        """
        pass

    # =============================================================================
    # Concrete Methods - Implemented in base class
    # =============================================================================

    def restart(self) -> bool:
        """
        Restart the AI manager (stop then start).

        Returns:
            True if restart successful, False otherwise
        """
        self.logger.info(f"Restarting manager", manager_id=self.manager_id)

        stop_success = self.stop()
        if not stop_success:
            self.logger.error(
                f"Failed to stop manager during restart",
                manager_id=self.manager_id,
            )
            return False

        # Brief pause to ensure clean shutdown
        time.sleep(1.0)

        start_success = self.start()
        if not start_success:
            self.logger.error(
                f"Failed to start manager during restart",
                manager_id=self.manager_id,
            )
            return False

        self.logger.info(f"Manager restarted successfully", manager_id=self.manager_id)
        return True

    def pause(self) -> bool:
        """
        Pause the AI manager (if supported by derived class).

        Default implementation just updates status.
        Override in derived class for actual pause logic.

        Returns:
            True if paused successfully
        """
        if self.status != ManagerStatus.RUNNING:
            self.logger.warning(
                f"Cannot pause manager - not running",
                manager_id=self.manager_id,
                current_status=self.status.value,
            )
            return False

        self.status = ManagerStatus.PAUSED
        self.logger.info(f"Manager paused", manager_id=self.manager_id)
        return True

    def resume(self) -> bool:
        """
        Resume the AI manager from paused state.

        Returns:
            True if resumed successfully
        """
        if self.status != ManagerStatus.PAUSED:
            self.logger.warning(
                f"Cannot resume manager - not paused",
                manager_id=self.manager_id,
                current_status=self.status.value,
            )
            return False

        self.status = ManagerStatus.RUNNING
        self.logger.info(f"Manager resumed", manager_id=self.manager_id)
        return True

    def health_check(self) -> HealthCheckResult:
        """
        Perform comprehensive health check.

        This is a template method that calls _health_check_impl()
        and adds common health checks.

        Returns:
            HealthCheckResult with detailed health status
        """
        try:
            # Call derived class implementation
            result = self._health_check_impl()

            # Add common checks
            uptime = self.get_uptime()
            result.details["uptime_seconds"] = uptime
            result.details["status"] = self.status.value
            result.details["last_activity_age_seconds"] = time.time() - self._last_activity_time

            return result

        except Exception as e:
            self.logger.error(
                f"Health check failed with exception",
                manager_id=self.manager_id,
                error=str(e),
            )

            return HealthCheckResult(
                is_healthy=False,
                status=ManagerStatus.ERROR,
                message=f"Health check exception: {str(e)}",
                checks_passed=0,
                checks_failed=1,
                details={"exception": str(e)},
            )

    def handle_confirmation(self, confirmation: ConfirmationRequest) -> Optional[str]:
        """
        Handle confirmation request (template method).

        This method provides common confirmation handling logic
        and delegates to _handle_confirmation_impl() for specifics.

        Args:
            confirmation: The confirmation request

        Returns:
            Response string or None
        """
        self._increment_operation()
        self._confirmation_count += 1

        self.logger.info(
            f"Handling confirmation",
            manager_id=self.manager_id,
            confirmation_type=confirmation.confirmation_type.value,
            worker_id=confirmation.worker_id,
        )

        try:
            # Call derived class implementation
            response = self._handle_confirmation_impl(confirmation)

            self._increment_success()

            return response

        except Exception as e:
            self._increment_failure()

            self.logger.error(
                f"Confirmation handling failed",
                manager_id=self.manager_id,
                error=str(e),
            )

            # Default to deny on error for safety
            return "no"

    def get_status(self) -> ManagerStatus:
        """
        Get current manager status.

        Returns:
            Current ManagerStatus
        """
        return self.status

    def get_uptime(self) -> float:
        """
        Get manager uptime in seconds.

        Returns:
            Uptime in seconds, or 0 if not started
        """
        if self._start_time is None:
            return 0.0

        if self._stop_time is not None:
            return self._stop_time - self._start_time

        return time.time() - self._start_time

    def get_metrics(self) -> ManagerMetrics:
        """
        Get current manager metrics.

        Returns:
            ManagerMetrics with current statistics
        """
        return ManagerMetrics(
            manager_id=self.manager_id,
            manager_type=self.manager_type,
            status=self.status,
            uptime_seconds=self.get_uptime(),
            total_operations=self._operation_count,
            successful_operations=self._success_count,
            failed_operations=self._failure_count,
            confirmations_handled=self._confirmation_count,
            last_activity_time=self._last_activity_time,
        )

    def log_event(self, event_type: str, message: str, **kwargs: Any) -> None:
        """
        Log an event with structured logging.

        Args:
            event_type: Type of event (e.g., "start", "stop", "error")
            message: Human-readable message
            **kwargs: Additional context to log
        """
        self.logger.info(
            message,
            manager_id=self.manager_id,
            manager_type=self.manager_type.value,
            event_type=event_type,
            **kwargs,
        )

    def write_terminal_output(
        self,
        output_text: str,
        log_file: Path,
        strip_ansi: bool = True,
    ) -> bool:
        """
        Write output to terminal log file.

        This is a common helper for writing terminal output with:
        - ANSI code stripping (optional)
        - Immediate flush for real-time streaming
        - Error handling

        Args:
            output_text: Text to write
            log_file: Path to log file
            strip_ansi: Whether to strip ANSI escape codes

        Returns:
            True if write successful, False otherwise
        """
        try:
            # Strip ANSI codes if requested
            clean_text = strip_ansi_codes(output_text) if strip_ansi else output_text

            # Ensure file exists
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Append to file
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(clean_text)
                if not clean_text.endswith("\n"):
                    f.write("\n")
                f.flush()  # Force immediate write

            self._update_activity_time()
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to write terminal output",
                manager_id=self.manager_id,
                log_file=str(log_file),
                error=str(e),
            )
            return False

    # =============================================================================
    # Protected Helper Methods
    # =============================================================================

    def _mark_started(self) -> None:
        """Mark manager as started and update metrics."""
        self._start_time = time.time()
        self.status = ManagerStatus.RUNNING
        self._update_activity_time()

        # Metrics tracking for manager_started
        pass

    def _mark_stopped(self) -> None:
        """Mark manager as stopped and update metrics."""
        self._stop_time = time.time()
        self.status = ManagerStatus.STOPPED

        # Metrics tracking for manager_stopped
        pass

    def _update_activity_time(self) -> None:
        """Update last activity timestamp."""
        self._last_activity_time = time.time()

    def _increment_operation(self) -> None:
        """Increment operation counter."""
        self._operation_count += 1
        self._update_activity_time()

    def _increment_success(self) -> None:
        """Increment success counter."""
        self._success_count += 1

    def _increment_failure(self) -> None:
        """Increment failure counter."""
        self._failure_count += 1

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<{self.__class__.__name__}("
            f"id={self.manager_id}, "
            f"type={self.manager_type.value}, "
            f"status={self.status.value}, "
            f"uptime={self.get_uptime():.1f}s"
            f")>"
        )


# =============================================================================
# Type Aliases for Convenience
# =============================================================================

AIManagerFactory = Callable[[OrchestratorConfig, ILogger, str], BaseAIManager]
"""Factory function type for creating AI managers."""


# =============================================================================
# Example Usage (if run directly)
# =============================================================================

if __name__ == "__main__":
    print("BaseAIManager is an abstract class and cannot be instantiated directly.")
    print("Create a derived class (e.g., WorkerAIManager or SupervisorAIManager).")
    print("\nExample:")
    print(
        """
    class MyAIManager(BaseAIManager):
        def start(self) -> bool:
            self._mark_started()
            # Your start logic here
            return True

        def stop(self) -> bool:
            # Your stop logic here
            self._mark_stopped()
            return True

        def _health_check_impl(self) -> HealthCheckResult:
            return HealthCheckResult(
                is_healthy=True,
                status=self.status,
                message="All systems operational",
                checks_passed=1,
                checks_failed=0,
            )

        def _handle_confirmation_impl(self, confirmation: ConfirmationRequest) -> Optional[str]:
            # Your confirmation handling logic
            return "yes"  # Auto-approve

    # Usage
    from orchestrator.config import OrchestratorConfig
    from orchestrator.logger import SimpleLogger

    config = OrchestratorConfig.from_env()
    logger = SimpleLogger()

    manager = MyAIManager(
        config=config,
        logger=logger,
        manager_id="my_manager_001",
        manager_type=ManagerType.WORKER,
    )

    manager.start()
    health = manager.health_check()
    print(f"Healthy: {health.is_healthy}")
    manager.stop()
    """
    )
