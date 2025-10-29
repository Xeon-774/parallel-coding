"""Unit tests for supervisor API routes.

Tests authentication, validation, error handling, and API contract for supervisor endpoints.
Coverage target: ≥90%
"""

import os
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from orchestrator.api.supervisor_routes import (
    RespondToConfirmationRequest,
    SpawnSupervisorRequest,
    authenticate,
    get_worker_manager,
    router,
)
from orchestrator.core.worker.worker_manager import (
    SupervisedWorkerResult,
    SupervisorStatus,
    SupervisorStatusInfo,
)


# Fixtures
@pytest.fixture
def mock_manager():
    """Create mock WorkerManager for testing."""
    manager = AsyncMock()
    manager.spawn_supervised_worker = AsyncMock()
    manager.get_supervisor_status = AsyncMock()
    manager.terminate_supervisor = AsyncMock()
    manager.list_supervisors = AsyncMock()
    manager.record_confirmation_response = AsyncMock()
    manager.get_output = AsyncMock()
    return manager


@pytest.fixture
def test_client(mock_manager):
    """Create test client with mocked dependencies."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    # Override dependency
    app.dependency_overrides[get_worker_manager] = lambda: mock_manager

    # Set test token
    os.environ["API_TOKEN"] = "test-token"

    return TestClient(app), mock_manager


# Authentication tests
def test_authenticate_valid_token():
    """Test successful authentication with valid bearer token."""
    os.environ["API_TOKEN"] = "test-token"

    class MockRequest:
        headers = {"authorization": "Bearer test-token"}

    # Should not raise
    authenticate(MockRequest())


def test_authenticate_missing_header():
    """Test authentication fails with missing Authorization header."""

    class MockRequest:
        headers = {}

    with pytest.raises(HTTPException) as exc_info:
        authenticate(MockRequest())

    assert exc_info.value.status_code == 401
    assert "unauthorized" in exc_info.value.detail.lower()


def test_authenticate_invalid_token():
    """Test authentication fails with invalid token."""
    os.environ["API_TOKEN"] = "correct-token"

    class MockRequest:
        headers = {"authorization": "Bearer wrong-token"}

    with pytest.raises(HTTPException) as exc_info:
        authenticate(MockRequest())

    assert exc_info.value.status_code == 401


def test_authenticate_malformed_header():
    """Test authentication fails with malformed Authorization header."""

    class MockRequest:
        headers = {"authorization": "InvalidFormat"}

    with pytest.raises(HTTPException) as exc_info:
        authenticate(MockRequest())

    assert exc_info.value.status_code == 401


# Pydantic model validation tests
def test_spawn_request_validation_success():
    """Test SpawnSupervisorRequest validation with valid data."""
    req = SpawnSupervisorRequest(
        task_file="tasks/WORKER_2.md", workspace_root="workspace/worker_2", timeout=300
    )
    assert req.task_file == "tasks/WORKER_2.md"
    assert req.workspace_root == "workspace/worker_2"
    assert req.timeout == 300


def test_spawn_request_validation_default_timeout():
    """Test SpawnSupervisorRequest uses default timeout when not specified."""
    req = SpawnSupervisorRequest(task_file="tasks/test.md", workspace_root="workspace/test")
    assert req.timeout == 300  # Default value


def test_spawn_request_validation_invalid_timeout():
    """Test SpawnSupervisorRequest validation fails with invalid timeout."""
    with pytest.raises(ValueError):
        SpawnSupervisorRequest(
            task_file="tasks/test.md", workspace_root="workspace/test", timeout=-1
        )


def test_spawn_request_validation_path_traversal():
    """Test SpawnSupervisorRequest rejects path traversal attempts."""
    with pytest.raises(ValueError):
        SpawnSupervisorRequest(task_file="../etc/passwd", workspace_root="workspace/test")


def test_confirmation_request_validation():
    """Test RespondToConfirmationRequest validation."""
    req = RespondToConfirmationRequest(decision="APPROVE", reason="Safe to execute")
    assert req.decision == "APPROVE"
    assert req.reason == "Safe to execute"


def test_confirmation_request_invalid_decision():
    """Test RespondToConfirmationRequest validation fails with invalid decision."""
    with pytest.raises(ValueError):
        RespondToConfirmationRequest(decision="invalid", reason="test")


# API endpoint tests
@pytest.mark.asyncio
async def test_spawn_supervisor_success(test_client):
    """Test POST /api/v1/supervisor/spawn endpoint success."""
    client, manager = test_client

    # Mock response
    manager.spawn_supervised_worker.return_value = SupervisedWorkerResult(
        supervisor_id="worker_2", status=SupervisorStatus.SPAWNING
    )

    response = client.post(
        "/api/v1/supervisor/spawn",
        json={"task_file": "tasks/WORKER_2.md", "workspace_root": "workspace/worker_2"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 201  # HTTP_201_CREATED
    data = response.json()
    assert data["supervisor_id"] == "worker_2"
    assert data["status"] == "spawning"

    # Verify manager was called correctly
    manager.spawn_supervised_worker.assert_called_once()


@pytest.mark.asyncio
async def test_spawn_supervisor_authentication_required(test_client):
    """Test spawn endpoint requires authentication."""
    client, _ = test_client

    response = client.post(
        "/api/v1/supervisor/spawn",
        json={"task_file": "tasks/test.md", "workspace_root": "workspace/test"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_spawn_supervisor_validation_error(test_client):
    """Test spawn endpoint returns 422 for validation errors."""
    client, _ = test_client

    response = client.post(
        "/api/v1/supervisor/spawn",
        json={"task_file": "tasks/test.md"},  # Missing workspace_root
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_supervisor_status_success(test_client):
    """Test GET /api/v1/supervisor/{id} endpoint success."""
    client, manager = test_client

    # Mock response
    manager.get_supervisor_status.return_value = SupervisorStatusInfo(
        supervisor_id="worker_2",
        status=SupervisorStatus.RUNNING,
        alive=True,
        uptime_secs=120.5,
        output_lines=42,
    )

    response = client.get(
        "/api/v1/supervisor/worker_2", headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["supervisor_id"] == "worker_2"
    assert data["status"] == "running"
    assert data["alive"] is True
    assert data["uptime_secs"] == 120.5
    assert data["output_lines"] == 42


@pytest.mark.asyncio
async def test_get_supervisor_status_not_found(test_client):
    """Test get status endpoint returns 404 when supervisor not found."""
    client, manager = test_client

    manager.get_supervisor_status.return_value = None

    response = client.get(
        "/api/v1/supervisor/nonexistent", headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_terminate_supervisor_success(test_client):
    """Test DELETE /api/v1/supervisor/{id} endpoint success."""
    client, manager = test_client

    manager.terminate_supervisor.return_value = True

    response = client.delete(
        "/api/v1/supervisor/worker_2", headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["terminated"] is True

    manager.terminate_supervisor.assert_called_once_with(worker_id="worker_2")


@pytest.mark.asyncio
async def test_terminate_supervisor_not_found(test_client):
    """Test terminate endpoint returns 404 when supervisor not found."""
    client, manager = test_client

    manager.terminate_supervisor.return_value = False

    response = client.delete(
        "/api/v1/supervisor/nonexistent", headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_supervisors_empty(test_client):
    """Test GET /api/v1/supervisor endpoint with no supervisors."""
    client, manager = test_client

    manager.list_supervisors.return_value = []

    response = client.get("/api/v1/supervisor", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_supervisors_with_data(test_client):
    """Test list supervisors endpoint returns supervisor data."""
    client, manager = test_client

    manager.list_supervisors.return_value = [
        SupervisorStatusInfo(
            supervisor_id="worker_1",
            status=SupervisorStatus.RUNNING,
            alive=True,
            uptime_secs=100.0,
            output_lines=10,
        ),
        SupervisorStatusInfo(
            supervisor_id="worker_2",
            status=SupervisorStatus.TERMINATED,
            alive=False,
            uptime_secs=50.0,
            output_lines=5,
        ),
    ]

    response = client.get("/api/v1/supervisor", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["supervisor_id"] == "worker_1"
    assert data["items"][1]["supervisor_id"] == "worker_2"


@pytest.mark.asyncio
async def test_record_confirmation_response_success(test_client):
    """Test POST /api/v1/supervisor/{id}/respond endpoint success."""
    client, manager = test_client

    manager.record_confirmation_response.return_value = True

    response = client.post(
        "/api/v1/supervisor/worker_2/respond",
        json={"decision": "APPROVE", "reason": "Task is safe"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"

    manager.record_confirmation_response.assert_called_once_with(
        worker_id="worker_2", decision="APPROVE", reason="Task is safe"
    )


@pytest.mark.asyncio
async def test_record_confirmation_response_not_found(test_client):
    """Test record confirmation endpoint returns 404 when supervisor not found."""
    client, manager = test_client

    manager.record_confirmation_response.return_value = False

    response = client.post(
        "/api/v1/supervisor/nonexistent/respond",
        json={"decision": "DENY", "reason": "Too risky"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_output_success(test_client):
    """Test GET /api/v1/supervisor/{id}/output endpoint success."""
    client, manager = test_client

    manager.get_output.return_value = [
        (1698765432.0, "Starting worker..."),
        (1698765433.5, "Task completed successfully"),
    ]

    response = client.get(
        "/api/v1/supervisor/worker_2/output", headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["timestamp"] == 1698765432.0
    assert data["items"][0]["content"] == "Starting worker..."
    assert data["next_offset"] == 2  # offset(0) + len(items)(2)


@pytest.mark.asyncio
async def test_get_output_not_found(test_client):
    """Test get output endpoint returns 404 when supervisor not found."""
    client, manager = test_client

    manager.get_output.return_value = None

    response = client.get(
        "/api/v1/supervisor/nonexistent/output", headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 404


# Error handling tests
@pytest.mark.asyncio
async def test_spawn_supervisor_runtime_error(test_client):
    """Test spawn endpoint handles RuntimeError from manager."""
    client, manager = test_client

    manager.spawn_supervised_worker.side_effect = RuntimeError("Spawn failed")

    response = client.post(
        "/api/v1/supervisor/spawn",
        json={"task_file": "tasks/test.md", "workspace_root": "workspace/test"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 500
    assert "spawn failed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_spawn_supervisor_not_implemented_error(test_client):
    """Test spawn endpoint handles NotImplementedError gracefully.

    Note: Current implementation returns 500 for NotImplementedError.
    This is acceptable as the stub implementation will be replaced in Week 3.
    """
    client, manager = test_client

    manager.spawn_supervised_worker.side_effect = NotImplementedError(
        "Supervisor integration pending"
    )

    response = client.post(
        "/api/v1/supervisor/spawn",
        json={"task_file": "tasks/test.md", "workspace_root": "workspace/test"},
        headers={"Authorization": "Bearer test-token"},
    )

    # Current implementation returns 500 for all exceptions except ValidationError/FileNotFoundError
    assert response.status_code == 500
    assert "spawn failed" in response.json()["detail"].lower()
