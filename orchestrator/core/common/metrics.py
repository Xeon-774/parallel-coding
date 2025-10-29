"""
Performance Metrics Collection System

Tracks worker execution metrics for performance analysis and visualization.
Phase 2.2 implementation.
"""

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class MetricType(Enum):
    """Metric type enumeration"""

    WORKER_LIFECYCLE = "worker_lifecycle"
    CONFIRMATION = "confirmation"
    OUTPUT = "output"
    PERFORMANCE = "performance"


class WorkerEvent(Enum):
    """Worker lifecycle events"""

    SPAWNED = "spawned"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


@dataclass
class Metric:
    """Base metric class"""

    type: str
    timestamp: str
    worker_id: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class WorkerLifecycleMetric(Metric):
    """Worker lifecycle event metric"""

    event: str
    duration_seconds: Optional[float] = None


@dataclass
class ConfirmationMetric(Metric):
    """Confirmation request metric"""

    confirmation_number: int
    orchestrator_latency_ms: float
    response: str


@dataclass
class OutputMetric(Metric):
    """Output capture metric"""

    output_size_bytes: int
    line_count: int


@dataclass
class PerformanceMetric(Metric):
    """Performance snapshot metric"""

    memory_mb: float
    cpu_percent: Optional[float] = None


class MetricsCollector:
    """
    Collects and persists worker performance metrics.

    Metrics are written to workspace/{worker_id}/metrics.jsonl in JSONL format
    (one JSON object per line) for easy streaming and analysis.
    """

    def __init__(self, workspace_root: Path):
        """
        Initialize metrics collector.

        Args:
            workspace_root: Root workspace directory
        """
        self.workspace_root = workspace_root
        self.worker_start_times: Dict[str, float] = {}

    def _get_metrics_file(self, worker_id: str) -> Path:
        """Get metrics file path for worker"""
        worker_workspace = self.workspace_root / worker_id
        worker_workspace.mkdir(parents=True, exist_ok=True)
        return worker_workspace / "metrics.jsonl"

    def _write_metric(self, worker_id: str, metric: Metric) -> None:
        """
        Append metric to metrics file.

        Args:
            worker_id: Worker identifier
            metric: Metric to write
        """
        metrics_file = self._get_metrics_file(worker_id)

        try:
            with open(metrics_file, "a", encoding="utf - 8") as f:
                json.dump(metric.to_dict(), f, ensure_ascii=False)
                f.write("\n")
                f.flush()
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Warning: Failed to write metric: {e}")

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in ISO 8601 format"""
        return datetime.utcnow().isoformat() + "Z"

    # Worker lifecycle metrics

    def record_worker_spawned(self, worker_id: str) -> None:
        """Record worker spawn event"""
        self.worker_start_times[worker_id] = time.time()

        metric = WorkerLifecycleMetric(
            type=MetricType.WORKER_LIFECYCLE.value,
            timestamp=self._get_timestamp(),
            worker_id=worker_id,
            event=WorkerEvent.SPAWNED.value,
        )
        self._write_metric(worker_id, metric)

    def record_worker_completed(self, worker_id: str) -> None:
        """Record worker completion event"""
        duration = None
        if worker_id in self.worker_start_times:
            duration = time.time() - self.worker_start_times[worker_id]
            del self.worker_start_times[worker_id]

        metric = WorkerLifecycleMetric(
            type=MetricType.WORKER_LIFECYCLE.value,
            timestamp=self._get_timestamp(),
            worker_id=worker_id,
            event=WorkerEvent.COMPLETED.value,
            duration_seconds=duration,
        )
        self._write_metric(worker_id, metric)

    def record_worker_failed(self, worker_id: str) -> None:
        """Record worker failure event"""
        duration = None
        if worker_id in self.worker_start_times:
            duration = time.time() - self.worker_start_times[worker_id]
            del self.worker_start_times[worker_id]

        metric = WorkerLifecycleMetric(
            type=MetricType.WORKER_LIFECYCLE.value,
            timestamp=self._get_timestamp(),
            worker_id=worker_id,
            event=WorkerEvent.FAILED.value,
            duration_seconds=duration,
        )
        self._write_metric(worker_id, metric)

    # Confirmation metrics

    def record_confirmation(
        self,
        worker_id: str,
        confirmation_number: int,
        orchestrator_latency_ms: float,
        response: str,
    ) -> None:
        """
        Record confirmation request and orchestrator response.

        Args:
            worker_id: Worker identifier
            confirmation_number: Sequential confirmation number (1, 2, 3...)
            orchestrator_latency_ms: Time orchestrator took to make decision
            response: "approved", "rejected", or "pending"
        """
        metric = ConfirmationMetric(
            type=MetricType.CONFIRMATION.value,
            timestamp=self._get_timestamp(),
            worker_id=worker_id,
            confirmation_number=confirmation_number,
            orchestrator_latency_ms=orchestrator_latency_ms,
            response=response,
        )
        self._write_metric(worker_id, metric)

    # Output metrics

    def record_output(self, worker_id: str, output_size_bytes: int, line_count: int) -> None:
        """
        Record output capture event.

        Args:
            worker_id: Worker identifier
            output_size_bytes: Size of captured output in bytes
            line_count: Number of lines captured
        """
        metric = OutputMetric(
            type=MetricType.OUTPUT.value,
            timestamp=self._get_timestamp(),
            worker_id=worker_id,
            output_size_bytes=output_size_bytes,
            line_count=line_count,
        )
        self._write_metric(worker_id, metric)

    # Performance metrics

    def record_performance(
        self, worker_id: str, memory_mb: float, cpu_percent: Optional[float] = None
    ) -> None:
        """
        Record performance snapshot.

        Args:
            worker_id: Worker identifier
            memory_mb: Memory usage in MB
            cpu_percent: CPU usage percentage (if available)
        """
        metric = PerformanceMetric(
            type=MetricType.PERFORMANCE.value,
            timestamp=self._get_timestamp(),
            worker_id=worker_id,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
        )
        self._write_metric(worker_id, metric)

    # Query methods

    def get_metrics(self, worker_id: str) -> List[Dict[str, Any]]:
        """
        Get all metrics for a worker.

        Args:
            worker_id: Worker identifier

        Returns:
            List of metrics as dictionaries
        """
        metrics_file = self._get_metrics_file(worker_id)

        if not metrics_file.exists():
            return []

        metrics = []
        try:
            with open(metrics_file, "r", encoding="utf - 8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        metrics.append(json.loads(line))
        except Exception as e:
            print(f"Warning: Failed to read metrics: {e}")

        return metrics

    def get_metrics_summary(self, worker_id: str) -> Dict[str, Any]:
        """
        Get aggregated metrics summary for a worker.

        Returns:
            Dictionary with summary statistics
        """
        metrics = self.get_metrics(worker_id)

        if not metrics:
            return {"worker_id": worker_id, "total_metrics": 0, "status": "no_data"}

        # Aggregate by metric type
        confirmations = [m for m in metrics if m.get("type") == "confirmation"]
        outputs = [m for m in metrics if m.get("type") == "output"]
        lifecycles = [m for m in metrics if m.get("type") == "worker_lifecycle"]

        # Calculate summary stats
        total_confirmations = len(confirmations)
        avg_latency = (
            sum(m["orchestrator_latency_ms"] for m in confirmations) / total_confirmations
            if confirmations
            else 0
        )

        total_output_bytes = sum(m.get("output_size_bytes", 0) for m in outputs)
        total_lines = sum(m.get("line_count", 0) for m in outputs)

        # Get duration from completion event
        duration_seconds = None
        completed_event = next((m for m in lifecycles if m.get("event") == "completed"), None)
        if completed_event:
            duration_seconds = completed_event.get("duration_seconds")

        return {
            "worker_id": worker_id,
            "total_metrics": len(metrics),
            "confirmations": {"count": total_confirmations, "avg_latency_ms": avg_latency},
            "output": {"total_bytes": total_output_bytes, "total_lines": total_lines},
            "execution": {"duration_seconds": duration_seconds},
        }
