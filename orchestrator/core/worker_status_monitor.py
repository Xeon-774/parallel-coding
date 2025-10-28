"""
Worker Status Monitoring System

Centralized service for tracking and reporting worker execution status in real-time.
Milestone 1.3: Worker Status UI implementation.

Features:
- Real-time worker state tracking (spawning, running, waiting, completed, error)
- Progress calculation based on output and confirmations
- Health monitoring with last activity timestamps
- Integration with MetricsCollector for historical data
- Thread-safe operations for concurrent access
"""

import asyncio
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Any, List
from threading import Lock


class WorkerState(str, Enum):
    """Worker execution state enumeration"""

    SPAWNING = "spawning"  # Worker process is being created
    RUNNING = "running"  # Worker is actively executing
    WAITING = "waiting"  # Worker is waiting for orchestrator response
    COMPLETED = "completed"  # Worker finished successfully
    ERROR = "error"  # Worker encountered an error
    TERMINATED = "terminated"  # Worker was forcefully stopped


class HealthStatus(str, Enum):
    """Worker health status"""

    HEALTHY = "healthy"  # Normal operation
    IDLE = "idle"  # No activity for moderate duration
    STALLED = "stalled"  # No activity for extended duration
    UNHEALTHY = "unhealthy"  # Critical issue detected


@dataclass
class WorkerStatus:
    """
    Complete status information for a single worker.

    This is the primary data structure exposed via REST and WebSocket APIs.
    """

    worker_id: str
    state: WorkerState
    current_task: str
    progress: int  # 0-100 percentage
    elapsed_time: float  # Seconds since spawn
    output_lines: int  # Total output lines captured
    confirmation_count: int  # Number of confirmations handled
    last_activity: float  # Unix timestamp of last activity
    health: HealthStatus

    # Optional detailed metrics
    memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    error_message: Optional[str] = None

    # Timestamps
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert enums to strings
        data["state"] = self.state.value
        data["health"] = self.health.value
        return data

    @property
    def is_active(self) -> bool:
        """Check if worker is currently active"""
        return self.state in {WorkerState.RUNNING, WorkerState.WAITING, WorkerState.SPAWNING}

    @property
    def is_terminal(self) -> bool:
        """Check if worker is in terminal state (completed/error/terminated)"""
        return self.state in {WorkerState.COMPLETED, WorkerState.ERROR, WorkerState.TERMINATED}


class WorkerStatusMonitor:
    """
    Centralized worker status tracking service.

    Thread-safe singleton service that maintains real-time status for all workers.
    Integrates with WorkerManager and MetricsCollector for comprehensive monitoring.

    Usage:
        monitor = WorkerStatusMonitor(workspace_root=Path("workspace"))

        # Update status
        monitor.update_worker_state("worker_001", WorkerState.RUNNING, task="Fix bug #123")

        # Get status
        status = monitor.get_worker_status("worker_001")

        # Get all statuses
        all_statuses = monitor.get_all_statuses()
    """

    # Health check thresholds
    IDLE_THRESHOLD = 30.0  # Seconds with no activity = idle
    STALLED_THRESHOLD = 120.0  # Seconds with no activity = stalled

    def __init__(self, workspace_root: Path):
        """
        Initialize status monitor.

        Args:
            workspace_root: Root workspace directory for workers
        """
        self.workspace_root = workspace_root
        self._statuses: Dict[str, WorkerStatus] = {}
        self._lock = Lock()  # Thread-safe access

    def register_worker(
        self, worker_id: str, task_name: str, state: WorkerState = WorkerState.SPAWNING
    ) -> WorkerStatus:
        """
        Register a new worker and create initial status.

        Args:
            worker_id: Worker identifier (e.g., "worker_001")
            task_name: Task description
            state: Initial state (default: SPAWNING)

        Returns:
            Initial WorkerStatus
        """
        with self._lock:
            now = time.time()
            status = WorkerStatus(
                worker_id=worker_id,
                state=state,
                current_task=task_name,
                progress=0,
                elapsed_time=0.0,
                output_lines=0,
                confirmation_count=0,
                last_activity=now,
                health=HealthStatus.HEALTHY,
                started_at=now,
            )
            self._statuses[worker_id] = status
            return status

    def update_worker_state(
        self,
        worker_id: str,
        state: WorkerState,
        task: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update worker state and related metadata.

        Args:
            worker_id: Worker identifier
            state: New worker state
            task: Optional task update
            error_message: Optional error message (for ERROR state)
        """
        with self._lock:
            if worker_id not in self._statuses:
                # Auto-register if not exists
                self.register_worker(worker_id, task or "Unknown task", state)
                return

            status = self._statuses[worker_id]
            status.state = state
            status.last_activity = time.time()

            if task:
                status.current_task = task

            if error_message:
                status.error_message = error_message

            # Update completed timestamp for terminal states
            if state in {WorkerState.COMPLETED, WorkerState.ERROR, WorkerState.TERMINATED}:
                status.completed_at = time.time()
                status.progress = 100 if state == WorkerState.COMPLETED else status.progress

    def update_output_metrics(self, worker_id: str, output_lines: int) -> None:
        """
        Update worker output line count.

        Args:
            worker_id: Worker identifier
            output_lines: Total number of output lines captured
        """
        with self._lock:
            if worker_id in self._statuses:
                status = self._statuses[worker_id]
                status.output_lines = output_lines
                status.last_activity = time.time()

                # Update progress based on output (heuristic)
                status.progress = self._calculate_progress(status)

    def update_confirmation_count(self, worker_id: str, confirmation_count: int) -> None:
        """
        Update worker confirmation count.

        Args:
            worker_id: Worker identifier
            confirmation_count: Total number of confirmations handled
        """
        with self._lock:
            if worker_id in self._statuses:
                status = self._statuses[worker_id]
                status.confirmation_count = confirmation_count
                status.last_activity = time.time()

                # Update progress based on confirmations (heuristic)
                status.progress = self._calculate_progress(status)

    def update_performance_metrics(
        self, worker_id: str, memory_mb: Optional[float] = None, cpu_percent: Optional[float] = None
    ) -> None:
        """
        Update worker performance metrics.

        Args:
            worker_id: Worker identifier
            memory_mb: Memory usage in MB
            cpu_percent: CPU usage percentage
        """
        with self._lock:
            if worker_id in self._statuses:
                status = self._statuses[worker_id]
                if memory_mb is not None:
                    status.memory_mb = memory_mb
                if cpu_percent is not None:
                    status.cpu_percent = cpu_percent
                status.last_activity = time.time()

    def get_worker_status(self, worker_id: str) -> Optional[WorkerStatus]:
        """
        Get current status for a specific worker.

        Args:
            worker_id: Worker identifier

        Returns:
            WorkerStatus if worker exists, None otherwise
        """
        with self._lock:
            if worker_id not in self._statuses:
                return None

            status = self._statuses[worker_id]

            # Update derived fields
            status.elapsed_time = time.time() - status.started_at
            status.health = self._calculate_health(status)

            return status

    def get_all_statuses(self) -> List[WorkerStatus]:
        """
        Get status for all registered workers.

        Returns:
            List of WorkerStatus objects
        """
        with self._lock:
            statuses = []
            for worker_id in self._statuses:
                status = self._statuses[worker_id]

                # Update derived fields
                status.elapsed_time = time.time() - status.started_at
                status.health = self._calculate_health(status)

                statuses.append(status)

            return statuses

    def get_summary(self) -> Dict[str, Any]:
        """
        Get aggregated summary of all workers.

        Returns:
            Dictionary with summary statistics
        """
        with self._lock:
            statuses = list(self._statuses.values())

            if not statuses:
                return {
                    "total_workers": 0,
                    "active_workers": 0,
                    "completed_workers": 0,
                    "error_workers": 0,
                }

            active = sum(1 for s in statuses if s.is_active)
            completed = sum(1 for s in statuses if s.state == WorkerState.COMPLETED)
            errors = sum(1 for s in statuses if s.state == WorkerState.ERROR)

            # Calculate average progress for active workers
            active_statuses = [s for s in statuses if s.is_active]
            avg_progress = (
                sum(s.progress for s in active_statuses) / len(active_statuses)
                if active_statuses
                else 0
            )

            return {
                "total_workers": len(statuses),
                "active_workers": active,
                "completed_workers": completed,
                "error_workers": errors,
                "avg_progress": round(avg_progress, 1),
                "total_confirmations": sum(s.confirmation_count for s in statuses),
            }

    def remove_worker(self, worker_id: str) -> bool:
        """
        Remove worker from monitoring.

        Args:
            worker_id: Worker identifier

        Returns:
            True if worker was removed, False if not found
        """
        with self._lock:
            if worker_id in self._statuses:
                del self._statuses[worker_id]
                return True
            return False

    def _calculate_progress(self, status: WorkerStatus) -> int:
        """
        Calculate progress percentage based on heuristics.

        This is an estimation based on:
        - Output lines (more output = more progress)
        - Confirmations (each confirmation = milestone)
        - Elapsed time (assumes tasks take ~5 minutes)

        Args:
            status: Worker status

        Returns:
            Progress percentage (0-100)
        """
        # Terminal states have fixed progress
        if status.state == WorkerState.COMPLETED:
            return 100
        if status.state in {WorkerState.ERROR, WorkerState.TERMINATED}:
            return status.progress  # Keep last known progress

        if status.state == WorkerState.SPAWNING:
            return 5

        # Heuristic calculation for RUNNING/WAITING states
        progress = 10  # Base progress for running

        # Add progress based on output (0-40 points)
        if status.output_lines > 0:
            # Assume 50 output lines = significant progress
            output_progress = min(40, (status.output_lines / 50) * 40)
            progress += output_progress

        # Add progress based on confirmations (0-30 points)
        if status.confirmation_count > 0:
            # Assume 5 confirmations = significant milestones
            confirmation_progress = min(30, (status.confirmation_count / 5) * 30)
            progress += confirmation_progress

        # Add progress based on time (0-20 points)
        # Assume 5 minutes = 100% time-based progress
        time_progress = min(20, (status.elapsed_time / 300) * 20)
        progress += time_progress

        # Cap at 95% until actually completed (leave room for final steps)
        return min(95, int(progress))

    def _calculate_health(self, status: WorkerStatus) -> HealthStatus:
        """
        Calculate worker health based on activity timestamps.

        Args:
            status: Worker status

        Returns:
            HealthStatus
        """
        # Terminal states are healthy by definition
        if status.is_terminal:
            return HealthStatus.HEALTHY

        # Check time since last activity
        time_since_activity = time.time() - status.last_activity

        if time_since_activity > self.STALLED_THRESHOLD:
            return HealthStatus.STALLED
        elif time_since_activity > self.IDLE_THRESHOLD:
            return HealthStatus.IDLE
        else:
            return HealthStatus.HEALTHY


# Global singleton instance
_global_monitor: Optional[WorkerStatusMonitor] = None


def get_global_monitor(workspace_root: Optional[Path] = None) -> WorkerStatusMonitor:
    """
    Get or create global WorkerStatusMonitor instance.

    Args:
        workspace_root: Workspace root path (required for first call)

    Returns:
        Global WorkerStatusMonitor instance

    Raises:
        ValueError: If workspace_root is not provided on first call
    """
    global _global_monitor

    if _global_monitor is None:
        if workspace_root is None:
            raise ValueError("workspace_root is required to initialize global monitor")
        _global_monitor = WorkerStatusMonitor(workspace_root)

    return _global_monitor
