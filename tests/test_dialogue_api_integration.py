"""
Integration tests for dialogue WebSocket API

Tests the complete FastAPI application with WebSocket endpoints.

Coverage:
- WebSocket connection establishment
- Historical entry retrieval via WebSocket
- Real - time entry streaming
- Error handling (worker not found, etc.)
- REST API endpoints
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

# Import with fallback for running from different contexts
try:
    from orchestrator.api import main as main_module
    from orchestrator.api.main import app
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from orchestrator.api import main as main_module
    from orchestrator.api.main import app


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        yield workspace


@pytest.fixture
def client(temp_workspace):
    """Create a test client with temporary workspace."""
    # Override workspace root for testing
    main_module.WORKSPACE_ROOT = temp_workspace

    with TestClient(app) as client:
        yield client


def create_worker_workspace(workspace_root: Path, worker_id: str) -> Path:
    """Helper to create a worker workspace directory."""
    worker_path = workspace_root / worker_id
    worker_path.mkdir(parents=True, exist_ok=True)
    return worker_path


def write_dialogue_entries(workspace_path: Path, entries: List[Dict[str, Any]]) -> None:
    """Helper to write dialogue entries to transcript file."""
    transcript = workspace_path / "dialogue_transcript.jsonl"
    with open(transcript, "w", encoding="utf - 8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


# ============================================================================
# REST API Tests
# ============================================================================


def test_root_endpoint(client):
    """GET / returns API information."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data


def test_health_check(client):
    """GET /health returns server status."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "workspace_root" in data
    assert "workspace_exists" in data


def test_list_workers_empty(client):
    """GET /api / v1 / workers returns empty list when no workers."""
    response = client.get("/api / v1 / workers")
    assert response.status_code == 200

    data = response.json()
    assert data["workers"] == []
    assert data["count"] == 0


def test_list_workers_with_workers(client, temp_workspace):
    """GET /api / v1 / workers returns worker list."""
    # Create test workers
    create_worker_workspace(temp_workspace, "worker_001")
    create_worker_workspace(temp_workspace, "worker_002")

    # Write dialogue to one worker
    worker1_path = temp_workspace / "worker_001"
    write_dialogue_entries(
        worker1_path,
        [{"timestamp": 1000.0, "direction": "test", "content": "test", "type": "output"}],
    )

    response = client.get("/api / v1 / workers")
    assert response.status_code == 200

    data = response.json()
    assert data["count"] == 2
    assert len(data["workers"]) == 2

    # Find worker_001
    worker1 = next(w for w in data["workers"] if w["worker_id"] == "worker_001")
    assert worker1["has_dialogue"] is True
    assert worker1["dialogue_size"] > 0

    # Find worker_002
    worker2 = next(w for w in data["workers"] if w["worker_id"] == "worker_002")
    assert worker2["has_dialogue"] is False


def test_get_worker_info(client, temp_workspace):
    """GET /api / v1 / workers/{worker_id} returns worker details."""
    worker_path = create_worker_workspace(temp_workspace, "worker_001")
    write_dialogue_entries(
        worker_path,
        [{"timestamp": 1000.0, "direction": "test", "content": "test", "type": "output"}],
    )

    response = client.get("/api / v1 / workers / worker_001")
    assert response.status_code == 200

    data = response.json()
    assert data["worker_id"] == "worker_001"
    assert data["dialogue"]["jsonl_exists"] is True
    assert data["dialogue"]["jsonl_size"] > 0


def test_get_worker_info_not_found(client):
    """GET /api / v1 / workers/{worker_id} returns 404 for non - existent worker."""
    response = client.get("/api / v1 / workers / worker_999")
    assert response.status_code == 404

    data = response.json()
    assert "not found" in data["detail"].lower()


# ============================================================================
# WebSocket Integration Tests
# ============================================================================


def test_websocket_worker_not_found(client):
    """WebSocket connection sends error for non - existent worker."""
    with client.websocket_connect("/ws / dialogue / worker_999") as websocket:
        message = websocket.receive_json()
        assert message["type"] == "error"
        assert "not found" in message["message"].lower()


def test_websocket_historical_entries(client, temp_workspace):
    """WebSocket sends historical entries on connection."""
    # Create worker with dialogue
    worker_path = create_worker_workspace(temp_workspace, "worker_001")
    entries = [
        {
            "timestamp": 1000.0,
            "direction": "worker→orchestrator",
            "content": "Running test",
            "type": "output",
            "confirmation_type": None,
            "confirmation_message": None,
        },
        {
            "timestamp": 2000.0,
            "direction": "orchestrator→worker",
            "content": "Approved",
            "type": "response",
            "confirmation_type": None,
            "confirmation_message": None,
        },
    ]
    write_dialogue_entries(worker_path, entries)

    # Connect via WebSocket
    with client.websocket_connect("/ws / dialogue / worker_001") as websocket:
        # Receive historical entries
        received_messages = []

        # First should be historical entries
        while True:
            message = websocket.receive_json()
            received_messages.append(message)

            if message["type"] == "ready":
                break

            # Timeout after 10 messages to prevent infinite loop
            if len(received_messages) > 10:
                break

        # Verify we got historical entries
        historical_messages = [m for m in received_messages if m["type"] == "historical"]
        assert len(historical_messages) == 2

        # Verify first entry
        assert historical_messages[0]["data"]["content"] == "Running test"
        assert historical_messages[0]["data"]["direction"] == "worker→orchestrator"

        # Verify second entry
        assert historical_messages[1]["data"]["content"] == "Approved"
        assert historical_messages[1]["data"]["direction"] == "orchestrator→worker"

        # Verify ready message
        ready_messages = [m for m in received_messages if m["type"] == "ready"]
        assert len(ready_messages) == 1


def test_websocket_empty_dialogue(client, temp_workspace):
    """WebSocket works with worker that has no dialogue yet."""
    # Create worker without dialogue
    create_worker_workspace(temp_workspace, "worker_001")

    # Connect via WebSocket
    with client.websocket_connect("/ws / dialogue / worker_001") as websocket:
        # Should receive ready message (no historical entries)
        message = websocket.receive_json()
        assert message["type"] == "ready"


def test_websocket_connection_with_multiple_clients(client, temp_workspace):
    """Multiple WebSocket clients can connect to same worker."""
    # Create worker with dialogue
    worker_path = create_worker_workspace(temp_workspace, "worker_001")
    write_dialogue_entries(
        worker_path,
        [
            {
                "timestamp": 1000.0,
                "direction": "test",
                "content": "test",
                "type": "output",
                "confirmation_type": None,
                "confirmation_message": None,
            }
        ],
    )

    # Connect two clients
    with client.websocket_connect("/ws / dialogue / worker_001") as ws1:
        with client.websocket_connect("/ws / dialogue / worker_001") as ws2:
            # Both should receive messages
            msg1 = ws1.receive_json()
            msg2 = ws2.receive_json()

            assert msg1["type"] == "historical"
            assert msg2["type"] == "historical"


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_api_handles_invalid_worker_id(client):
    """API handles invalid worker ID formats gracefully."""
    # Test with various invalid formats
    invalid_ids = [
        "../etc / passwd",  # Path traversal attempt
        "worker_001; rm -rf /",  # Command injection attempt
    ]

    for worker_id in invalid_ids:
        response = client.get(f"/api / v1 / workers/{worker_id}")
        # Should either return 404 or handle gracefully
        assert response.status_code in [404, 400, 422]


def test_websocket_handles_malformed_path(client):
    """WebSocket handles malformed paths gracefully."""
    # Test with invalid worker IDs
    with pytest.raises(Exception):
        with client.websocket_connect("/ws / dialogue/") as websocket:
            pass


# ============================================================================
# Real - time Streaming Test (Simulation)
# ============================================================================


def test_websocket_entry_format(client, temp_workspace):
    """WebSocket entry format matches expected structure."""
    worker_path = create_worker_workspace(temp_workspace, "worker_001")
    entries = [
        {
            "timestamp": 1000.0,
            "direction": "worker→orchestrator",
            "content": "Test content",
            "type": "output",
            "confirmation_type": "bash",
            "confirmation_message": "Run command?",
        }
    ]
    write_dialogue_entries(worker_path, entries)

    with client.websocket_connect("/ws / dialogue / worker_001") as websocket:
        message = websocket.receive_json()

        # Verify message structure
        assert "type" in message
        assert message["type"] == "historical"
        assert "data" in message

        data = message["data"]
        assert "timestamp" in data
        assert "direction" in data
        assert "content" in data
        assert "type" in data
        assert "confirmation_type" in data
        assert "confirmation_message" in data

        # Verify values
        assert data["timestamp"] == 1000.0
        assert data["direction"] == "worker→orchestrator"
        assert data["content"] == "Test content"
        assert data["type"] == "output"
        assert data["confirmation_type"] == "bash"
        assert data["confirmation_message"] == "Run command?"


# ============================================================================
# Performance Tests
# ============================================================================


def test_websocket_handles_large_history(client, temp_workspace):
    """WebSocket handles large history efficiently (limit=100)."""
    # Create worker with 200 entries
    worker_path = create_worker_workspace(temp_workspace, "worker_001")

    large_entries = [
        {
            "timestamp": float(i),
            "direction": "test",
            "content": f"Entry {i}",
            "type": "output",
            "confirmation_type": None,
            "confirmation_message": None,
        }
        for i in range(200)
    ]
    write_dialogue_entries(worker_path, large_entries)

    with client.websocket_connect("/ws / dialogue / worker_001") as websocket:
        # Collect all historical messages
        historical_count = 0

        while True:
            message = websocket.receive_json()

            if message["type"] == "historical":
                historical_count += 1
            elif message["type"] == "ready":
                break

            # Safety limit
            if historical_count > 150:
                break

        # Should receive at most 100 entries (limit in get_historical_entries)
        assert historical_count == 100


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
