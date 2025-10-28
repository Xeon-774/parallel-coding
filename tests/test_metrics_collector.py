"""
Unit tests for MetricsCollector (Phase 2.2)

Tests metrics collection functionality including:
- Worker lifecycle events
- Confirmation tracking
- Output metrics
- Metrics retrieval and aggregation
"""

import pytest
import json
import time
from pathlib import Path
from datetime import datetime

from orchestrator.core.common.metrics import (
    MetricsCollector,
    MetricType,
    WorkerEvent
)


@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace directory"""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def metrics_collector(temp_workspace):
    """Create MetricsCollector instance with temporary workspace"""
    return MetricsCollector(workspace_root=temp_workspace)


class TestWorkerLifecycleMetrics:
    """Test worker lifecycle event recording"""

    def test_record_worker_spawned(self, metrics_collector, temp_workspace):
        """Test recording worker spawn event"""
        worker_id = "worker_test_001"

        # Record spawn
        metrics_collector.record_worker_spawned(worker_id)

        # Verify metrics file created
        metrics_file = temp_workspace / worker_id / "metrics.jsonl"
        assert metrics_file.exists()

        # Verify metric content
        with open(metrics_file, 'r', encoding='utf-8') as f:
            line = f.readline().strip()
            metric = json.loads(line)

        assert metric["type"] == MetricType.WORKER_LIFECYCLE.value
        assert metric["worker_id"] == worker_id
        assert metric["event"] == WorkerEvent.SPAWNED.value
        assert "timestamp" in metric
        assert metric.get("duration_seconds") is None  # No duration for spawn

        # Verify start time recorded
        assert worker_id in metrics_collector.worker_start_times

    def test_record_worker_completed(self, metrics_collector, temp_workspace):
        """Test recording worker completion event with duration"""
        worker_id = "worker_test_002"

        # Record spawn then completion
        metrics_collector.record_worker_spawned(worker_id)
        time.sleep(0.1)  # Small delay to ensure measurable duration
        metrics_collector.record_worker_completed(worker_id)

        # Read metrics
        metrics = metrics_collector.get_metrics(worker_id)

        assert len(metrics) == 2
        spawn_metric = metrics[0]
        complete_metric = metrics[1]

        # Verify spawn metric
        assert spawn_metric["event"] == WorkerEvent.SPAWNED.value

        # Verify completion metric
        assert complete_metric["event"] == WorkerEvent.COMPLETED.value
        assert complete_metric["duration_seconds"] is not None
        assert complete_metric["duration_seconds"] > 0

        # Verify start time removed
        assert worker_id not in metrics_collector.worker_start_times

    def test_record_worker_failed(self, metrics_collector):
        """Test recording worker failure event"""
        worker_id = "worker_test_003"

        # Record spawn then failure
        metrics_collector.record_worker_spawned(worker_id)
        time.sleep(0.05)
        metrics_collector.record_worker_failed(worker_id)

        # Read metrics
        metrics = metrics_collector.get_metrics(worker_id)

        assert len(metrics) == 2
        failure_metric = metrics[1]

        assert failure_metric["event"] == WorkerEvent.FAILED.value
        assert failure_metric["duration_seconds"] is not None
        assert failure_metric["duration_seconds"] > 0


class TestConfirmationMetrics:
    """Test confirmation event recording"""

    def test_record_confirmation(self, metrics_collector):
        """Test recording confirmation event"""
        worker_id = "worker_test_004"

        # Record confirmation
        metrics_collector.record_confirmation(
            worker_id=worker_id,
            confirmation_number=1,
            orchestrator_latency_ms=123.45,
            response="approved"
        )

        # Read metrics
        metrics = metrics_collector.get_metrics(worker_id)

        assert len(metrics) == 1
        metric = metrics[0]

        assert metric["type"] == MetricType.CONFIRMATION.value
        assert metric["worker_id"] == worker_id
        assert metric["confirmation_number"] == 1
        assert metric["orchestrator_latency_ms"] == 123.45
        assert metric["response"] == "approved"

    def test_record_multiple_confirmations(self, metrics_collector):
        """Test recording multiple sequential confirmations"""
        worker_id = "worker_test_005"

        # Record multiple confirmations
        for i in range(1, 4):
            metrics_collector.record_confirmation(
                worker_id=worker_id,
                confirmation_number=i,
                orchestrator_latency_ms=100 + i * 10,
                response="approved"
            )

        # Read metrics
        metrics = metrics_collector.get_metrics(worker_id)

        assert len(metrics) == 3

        # Verify sequential confirmation numbers
        for i, metric in enumerate(metrics, start=1):
            assert metric["confirmation_number"] == i
            assert metric["orchestrator_latency_ms"] == 100 + i * 10


class TestOutputMetrics:
    """Test output capture metrics"""

    def test_record_output(self, metrics_collector):
        """Test recording output capture event"""
        worker_id = "worker_test_006"

        # Record output
        metrics_collector.record_output(
            worker_id=worker_id,
            output_size_bytes=1024,
            line_count=50
        )

        # Read metrics
        metrics = metrics_collector.get_metrics(worker_id)

        assert len(metrics) == 1
        metric = metrics[0]

        assert metric["type"] == MetricType.OUTPUT.value
        assert metric["output_size_bytes"] == 1024
        assert metric["line_count"] == 50


class TestMetricsRetrieval:
    """Test metrics retrieval and aggregation"""

    def test_get_metrics_empty(self, metrics_collector):
        """Test retrieving metrics for non-existent worker"""
        metrics = metrics_collector.get_metrics("nonexistent_worker")
        assert metrics == []

    def test_get_metrics_summary_no_data(self, metrics_collector):
        """Test summary for worker with no metrics"""
        summary = metrics_collector.get_metrics_summary("nonexistent_worker")

        assert summary["worker_id"] == "nonexistent_worker"
        assert summary["total_metrics"] == 0
        assert summary["status"] == "no_data"

    def test_get_metrics_summary_complete_workflow(self, metrics_collector):
        """Test summary aggregation for complete worker workflow"""
        worker_id = "worker_test_007"

        # Simulate complete workflow
        metrics_collector.record_worker_spawned(worker_id)
        time.sleep(0.1)

        # Record confirmations
        metrics_collector.record_confirmation(
            worker_id, confirmation_number=1,
            orchestrator_latency_ms=150, response="approved"
        )
        metrics_collector.record_confirmation(
            worker_id, confirmation_number=2,
            orchestrator_latency_ms=200, response="approved"
        )

        # Record output
        metrics_collector.record_output(
            worker_id, output_size_bytes=2048, line_count=100
        )

        # Complete
        metrics_collector.record_worker_completed(worker_id)

        # Get summary
        summary = metrics_collector.get_metrics_summary(worker_id)

        assert summary["worker_id"] == worker_id
        assert summary["total_metrics"] == 5

        # Check confirmations
        assert summary["confirmations"]["count"] == 2
        assert summary["confirmations"]["avg_latency_ms"] == 175.0  # (150 + 200) / 2

        # Check output
        assert summary["output"]["total_bytes"] == 2048
        assert summary["output"]["total_lines"] == 100

        # Check execution
        assert summary["execution"]["duration_seconds"] is not None
        assert summary["execution"]["duration_seconds"] > 0


class TestJSONLFormat:
    """Test JSONL file format"""

    def test_jsonl_format(self, metrics_collector, temp_workspace):
        """Verify metrics are written in valid JSONL format"""
        worker_id = "worker_test_008"

        # Record multiple metrics
        metrics_collector.record_worker_spawned(worker_id)
        metrics_collector.record_confirmation(
            worker_id, confirmation_number=1,
            orchestrator_latency_ms=100, response="approved"
        )
        metrics_collector.record_worker_completed(worker_id)

        # Read file manually
        metrics_file = temp_workspace / worker_id / "metrics.jsonl"
        with open(metrics_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Verify each line is valid JSON
        assert len(lines) == 3
        for line in lines:
            metric = json.loads(line.strip())
            assert "type" in metric
            assert "timestamp" in metric
            assert "worker_id" in metric

    def test_timestamp_format(self, metrics_collector):
        """Verify timestamps are in ISO 8601 format"""
        worker_id = "worker_test_009"

        metrics_collector.record_worker_spawned(worker_id)

        metrics = metrics_collector.get_metrics(worker_id)
        timestamp = metrics[0]["timestamp"]

        # Verify ISO 8601 format (ends with 'Z')
        assert timestamp.endswith('Z')

        # Verify parseable by datetime
        parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert parsed is not None


class TestErrorHandling:
    """Test error handling in metrics collection"""

    def test_write_metric_failure(self, metrics_collector, temp_workspace, monkeypatch):
        """Test graceful handling of file write errors"""
        worker_id = "worker_test_010"

        def mock_open_fail(*args, **kwargs):
            raise PermissionError("Mock permission error")

        # Monkeypatch open to fail
        monkeypatch.setattr("builtins.open", mock_open_fail)

        # Should not raise exception, just print warning
        try:
            metrics_collector.record_worker_spawned(worker_id)
            # Success if no exception raised
            assert True
        except Exception as e:
            pytest.fail(f"Metrics collection should not raise exception: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
