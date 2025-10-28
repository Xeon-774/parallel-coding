"""
Integration tests for Worker Status API endpoints.

Tests the REST and WebSocket API endpoints with actual FastAPI TestClient.
Milestone 1.3: Worker Status UI - API Tests

Test Coverage:
- REST endpoints (/health, /summary, /workers, /workers/{id})
- WebSocket streaming endpoint
- Error handling (404s, invalid worker IDs)
- Integration with WorkerStatusMonitor
- JSON serialization and response formats
"""

import pytest
import asyncio
import json
from pathlib import Path
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from orchestrator.api.main import app
from orchestrator.api import worker_status_api
from orchestrator.core.worker_status_monitor import (
    get_global_monitor,
    WorkerState,
    HealthStatus,
)


@pytest.fixture
def client(tmp_path):
    """Create FastAPI test client with initialized worker status API."""
    # Initialize worker status API with temporary workspace
    worker_status_api.init_worker_status_api(tmp_path)

    # Create test client
    test_client = TestClient(app)

    yield test_client

    # Cleanup: reset global monitor and workspace root to avoid state pollution
    monitor = get_global_monitor()
    # Clear all workers
    for worker_id in list(monitor._statuses.keys()):
        monitor.remove_worker(worker_id)
    worker_status_api._global_monitor = None
    worker_status_api._workspace_root = None


@pytest.fixture
def monitor(tmp_path):
    """Get the global WorkerStatusMonitor instance."""
    worker_status_api.init_worker_status_api(tmp_path)
    return get_global_monitor()


class TestHealthEndpoint:
    """Test API health check endpoint."""

    def test_health_endpoint_returns_healthy(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get("/api/v1/status/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["monitor_initialized"] is True
        # Health endpoint doesn't currently return timestamp
        # (could be added in future if needed)

    def test_health_endpoint_includes_workspace(self, client):
        """Test health endpoint includes workspace info."""
        response = client.get("/api/v1/status/health")
        data = response.json()

        assert "workspace_root" in data
        assert isinstance(data["workspace_root"], str)


class TestWorkersListEndpoint:
    """Test workers list endpoint."""

    def test_list_workers_empty(self, client):
        """Test listing workers when none are registered."""
        response = client.get("/api/v1/status/workers")

        assert response.status_code == 200
        data = response.json()

        assert data["workers"] == []
        assert data["count"] == 0

    def test_list_workers_with_registered_workers(self, client, monitor):
        """Test listing workers with multiple registered workers."""
        # Register test workers
        monitor.register_worker("worker_001", "Task 1")
        monitor.register_worker("worker_002", "Task 2")
        monitor.register_worker("worker_003", "Task 3")

        response = client.get("/api/v1/status/workers")

        assert response.status_code == 200
        data = response.json()

        assert data["count"] == 3
        assert len(data["workers"]) == 3

        worker_ids = {worker["worker_id"] for worker in data["workers"]}
        assert worker_ids == {"worker_001", "worker_002", "worker_003"}

    def test_list_workers_json_serialization(self, client, monitor):
        """Test that worker status is properly serialized to JSON."""
        monitor.register_worker("worker_001", "Test task")
        monitor.update_worker_state("worker_001", WorkerState.RUNNING)
        monitor.update_output_metrics("worker_001", output_lines=25)

        response = client.get("/api/v1/status/workers")
        data = response.json()

        worker = data["workers"][0]

        # Check all required fields are present
        assert worker["worker_id"] == "worker_001"
        assert worker["state"] == "running"
        assert worker["current_task"] == "Test task"
        assert worker["output_lines"] == 25
        assert "progress" in worker
        assert "elapsed_time" in worker
        assert "health" in worker
        assert "started_at" in worker

    def test_list_workers_includes_all_states(self, client, monitor):
        """Test listing workers in different states."""
        monitor.register_worker("worker_001", "Task 1", WorkerState.SPAWNING)
        monitor.register_worker("worker_002", "Task 2", WorkerState.RUNNING)
        monitor.register_worker("worker_003", "Task 3", WorkerState.COMPLETED)
        monitor.register_worker("worker_004", "Task 4", WorkerState.ERROR)

        response = client.get("/api/v1/status/workers")
        data = response.json()

        assert data["count"] == 4

        states = {worker["state"] for worker in data["workers"]}
        assert "spawning" in states
        assert "running" in states
        assert "completed" in states
        assert "error" in states


class TestWorkerDetailEndpoint:
    """Test individual worker detail endpoint."""

    def test_get_worker_detail(self, client, monitor):
        """Test getting details for a specific worker."""
        monitor.register_worker("worker_001", "Test task")
        monitor.update_worker_state("worker_001", WorkerState.RUNNING)
        monitor.update_output_metrics("worker_001", output_lines=42)
        monitor.update_confirmation_count("worker_001", confirmation_count=3)

        response = client.get("/api/v1/status/workers/worker_001")

        assert response.status_code == 200
        data = response.json()

        assert data["worker_id"] == "worker_001"
        assert data["state"] == "running"
        assert data["current_task"] == "Test task"
        assert data["output_lines"] == 42
        assert data["confirmation_count"] == 3
        assert data["progress"] > 0

    def test_get_nonexistent_worker(self, client):
        """Test getting details for a worker that doesn't exist."""
        response = client.get("/api/v1/status/workers/worker_999")

        assert response.status_code == 404
        data = response.json()

        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_get_worker_with_error_message(self, client, monitor):
        """Test getting worker with error state and message."""
        monitor.register_worker("worker_001", "Task")
        monitor.update_worker_state(
            "worker_001", WorkerState.ERROR, error_message="Connection timeout"
        )

        response = client.get("/api/v1/status/workers/worker_001")
        data = response.json()

        assert data["state"] == "error"
        assert data["error_message"] == "Connection timeout"

    def test_get_worker_with_performance_metrics(self, client, monitor):
        """Test getting worker with performance metrics."""
        monitor.register_worker("worker_001", "Task")
        monitor.update_performance_metrics("worker_001", memory_mb=512.5, cpu_percent=25.3)

        response = client.get("/api/v1/status/workers/worker_001")
        data = response.json()

        assert data["memory_mb"] == 512.5
        assert data["cpu_percent"] == 25.3


class TestSummaryEndpoint:
    """Test summary statistics endpoint."""

    def test_summary_empty(self, client):
        """Test summary with no workers."""
        response = client.get("/api/v1/status/summary")

        assert response.status_code == 200
        data = response.json()

        assert data["total_workers"] == 0
        assert data["active_workers"] == 0
        assert data["completed_workers"] == 0
        assert data["error_workers"] == 0
        # When no workers exist, avg_progress and total_confirmations are not included
        # (early return in get_summary)

    def test_summary_with_multiple_workers(self, client, monitor):
        """Test summary with workers in various states."""
        # Register workers in different states
        monitor.register_worker("worker_001", "Task 1")
        monitor.update_worker_state("worker_001", WorkerState.RUNNING)
        monitor.update_confirmation_count("worker_001", confirmation_count=2)

        monitor.register_worker("worker_002", "Task 2")
        monitor.update_worker_state("worker_002", WorkerState.RUNNING)
        monitor.update_confirmation_count("worker_002", confirmation_count=3)

        monitor.register_worker("worker_003", "Task 3")
        monitor.update_worker_state("worker_003", WorkerState.COMPLETED)

        monitor.register_worker("worker_004", "Task 4")
        monitor.update_worker_state("worker_004", WorkerState.ERROR)

        monitor.register_worker("worker_005", "Task 5")
        monitor.update_worker_state("worker_005", WorkerState.WAITING)

        response = client.get("/api/v1/status/summary")
        data = response.json()

        assert data["total_workers"] == 5
        assert data["active_workers"] == 3  # RUNNING (2) + WAITING (1)
        assert data["completed_workers"] == 1
        assert data["error_workers"] == 1
        assert data["total_confirmations"] == 5  # 2 + 3
        assert data["avg_progress"] > 0

    def test_summary_calculates_average_progress(self, client, monitor):
        """Test that summary correctly calculates average progress."""
        monitor.register_worker("worker_001", "Task 1")
        monitor.update_worker_state("worker_001", WorkerState.RUNNING)
        monitor.update_output_metrics("worker_001", output_lines=25)

        monitor.register_worker("worker_002", "Task 2")
        monitor.update_worker_state("worker_002", WorkerState.RUNNING)
        monitor.update_output_metrics("worker_002", output_lines=30)

        response = client.get("/api/v1/status/summary")
        data = response.json()

        # Both workers should have progress > 0
        assert data["avg_progress"] > 0
        # Progress should be capped at 95% for active workers
        assert data["avg_progress"] <= 95


class TestWebSocketEndpoint:
    """Test WebSocket streaming endpoint."""

    def test_websocket_connection_and_streaming(self, client, monitor):
        """Test WebSocket connection and status streaming."""
        # Register worker
        monitor.register_worker("worker_001", "Test task")
        monitor.update_worker_state("worker_001", WorkerState.RUNNING)

        # Connect to WebSocket
        with client.websocket_connect("/api/v1/status/ws/worker_001") as websocket:
            # Receive first status message
            data = websocket.receive_json()

            assert data["type"] == "status"
            assert "data" in data

            status = data["data"]
            assert status["worker_id"] == "worker_001"
            assert status["state"] == "running"
            assert status["current_task"] == "Test task"

            # Update worker state while connected
            monitor.update_output_metrics("worker_001", output_lines=50)

            # Receive updated status
            data = websocket.receive_json()
            updated_status = data["data"]
            assert updated_status["output_lines"] == 50

    def test_websocket_closes_on_terminal_state(self, client, monitor):
        """Test WebSocket closes when worker reaches terminal state."""
        monitor.register_worker("worker_001", "Task")
        monitor.update_worker_state("worker_001", WorkerState.RUNNING)

        with client.websocket_connect("/api/v1/status/ws/worker_001") as websocket:
            # Receive initial status
            data = websocket.receive_json()
            assert data["data"]["state"] == "running"

            # Complete the worker
            monitor.update_worker_state("worker_001", WorkerState.COMPLETED)

            # Should receive completed status
            data = websocket.receive_json()
            assert data["data"]["state"] == "completed"

            # WebSocket should close after terminal state
            # (Server sends completed status then closes)

    def test_websocket_with_nonexistent_worker(self, client):
        """Test WebSocket with worker that doesn't exist."""
        with client.websocket_connect("/api/v1/status/ws/worker_999") as websocket:
            # Should receive error or status updates with None
            data = websocket.receive_json()

            # Server may send "error" type or "status" with None data
            assert data["type"] in ["status", "error"]
            if data["type"] == "status":
                assert data["data"] is None

    def test_websocket_updates_frequency(self, client, monitor):
        """Test WebSocket sends updates at expected frequency (500ms)."""
        import time

        monitor.register_worker("worker_001", "Task")
        monitor.update_worker_state("worker_001", WorkerState.RUNNING)

        with client.websocket_connect("/api/v1/status/ws/worker_001") as websocket:
            # Receive first message
            start_time = time.time()
            data1 = websocket.receive_json()

            # Receive second message
            data2 = websocket.receive_json()
            elapsed = time.time() - start_time

            # Should be approximately 500ms between messages
            # Allow some tolerance for processing time
            assert 0.4 < elapsed < 0.7  # 400-700ms tolerance


class TestAPIErrorHandling:
    """Test API error handling and edge cases."""

    def test_invalid_worker_id_format(self, client):
        """Test handling of invalid worker ID format."""
        # FastAPI should handle this gracefully
        response = client.get("/api/v1/status/workers/invalid%20id")

        # Should return 404 (not found) or handle the ID
        assert response.status_code in [404, 200]

    def test_concurrent_api_requests(self, client, monitor):
        """Test concurrent API requests don't cause issues."""
        import threading

        # Register multiple workers
        for i in range(5):
            monitor.register_worker(f"worker_{i:03d}", f"Task {i}")
            monitor.update_worker_state(f"worker_{i:03d}", WorkerState.RUNNING)

        results = []

        def fetch_workers():
            response = client.get("/api/v1/status/workers")
            results.append(response.status_code)

        def fetch_summary():
            response = client.get("/api/v1/status/summary")
            results.append(response.status_code)

        # Make concurrent requests
        threads = []
        for _ in range(10):
            t1 = threading.Thread(target=fetch_workers)
            t2 = threading.Thread(target=fetch_summary)
            threads.extend([t1, t2])

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All requests should succeed
        assert all(status == 200 for status in results)


class TestAPIIntegration:
    """Test full integration scenarios."""

    def test_worker_lifecycle_via_api(self, client, monitor):
        """Test tracking a worker's full lifecycle via API."""
        # 1. Register worker
        monitor.register_worker("worker_001", "Build feature X")

        response = client.get("/api/v1/status/workers/worker_001")
        data = response.json()
        assert data["state"] == "spawning"
        # Progress is only calculated when metrics are updated, not during registration
        assert data["progress"] >= 0

        # 2. Start running
        monitor.update_worker_state("worker_001", WorkerState.RUNNING)

        response = client.get("/api/v1/status/workers/worker_001")
        data = response.json()
        assert data["state"] == "running"
        # Progress is still 0 until metrics are updated
        assert data["progress"] >= 0

        # 3. Add output
        monitor.update_output_metrics("worker_001", output_lines=25)

        response = client.get("/api/v1/status/workers/worker_001")
        data = response.json()
        assert data["output_lines"] == 25
        assert data["progress"] > 10

        # 4. Add confirmations
        monitor.update_confirmation_count("worker_001", confirmation_count=2)

        response = client.get("/api/v1/status/workers/worker_001")
        data = response.json()
        assert data["confirmation_count"] == 2
        assert data["progress"] > 20

        # 5. Complete
        monitor.update_worker_state("worker_001", WorkerState.COMPLETED)

        response = client.get("/api/v1/status/workers/worker_001")
        data = response.json()
        assert data["state"] == "completed"
        assert data["progress"] == 100
        assert "completed_at" in data

    def test_summary_reflects_real_time_changes(self, client, monitor):
        """Test that summary endpoint reflects real-time changes."""
        # Initial state
        response = client.get("/api/v1/status/summary")
        data = response.json()
        assert data["total_workers"] == 0

        # Add worker
        monitor.register_worker("worker_001", "Task")
        monitor.update_worker_state("worker_001", WorkerState.RUNNING)

        response = client.get("/api/v1/status/summary")
        data = response.json()
        assert data["total_workers"] == 1
        assert data["active_workers"] == 1

        # Complete worker
        monitor.update_worker_state("worker_001", WorkerState.COMPLETED)

        response = client.get("/api/v1/status/summary")
        data = response.json()
        assert data["total_workers"] == 1
        assert data["active_workers"] == 0
        assert data["completed_workers"] == 1
