"""
Integration tests for Week 2 MVP Phase 2: API Modules.

Tests FastAPI dependencies, Supervisor API, Resource Manager API,
Job Orchestrator API, and error handling (401, 403, 404, 422).

Coverage Target: ≥75% for API modules (supervisor_api, resources_api, jobs_api, dependencies)
"""

from __future__ import annotations

from typing import Generator

import pytest
from fastapi.testclient import TestClient

from orchestrator.api.main import app
from orchestrator.core.auth import create_access_token, create_dev_token
from orchestrator.core.database import get_db
from orchestrator.core.db_models import Job, JobStatus, Worker, WorkerStatus

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_db() -> Generator[None, None, None]:
    """Clean up database before each test."""
    db = next(get_db())
    try:
        db.query(Job).delete()
        db.query(Worker).delete()
        db.commit()
        yield
    finally:
        db.close()


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Create valid JWT token with all scopes for testing."""
    token = create_dev_token(
        scopes=[
            "supervisor:read",
            "supervisor:write",
            "jobs:read",
            "jobs:write",
            "resources:read",
            "resources:write",
        ]
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def readonly_headers() -> dict[str, str]:
    """Create JWT token with read-only scopes."""
    token = create_dev_token(scopes=["supervisor:read", "jobs:read", "resources:read"])
    return {"Authorization": f"Bearer {token}"}


def _seed_worker(
    worker_id: str = "w1",
    workspace_id: str = "ws1",
    status: WorkerStatus = WorkerStatus.IDLE,
) -> Worker:
    """Helper function to seed a worker in the database."""
    db = next(get_db())
    try:
        worker = Worker(id=worker_id, workspace_id=workspace_id, status=status)
        db.add(worker)
        db.commit()
        db.refresh(worker)
        return worker
    finally:
        db.close()


def _seed_job(
    job_id: str = "j1",
    task_description: str = "Test task",
    status: JobStatus = JobStatus.PENDING,
    depth: int = 0,
    worker_count: int = 1,
) -> Job:
    """Helper function to seed a job in the database."""
    db = next(get_db())
    try:
        job = Job(
            id=job_id,
            task_description=task_description,
            status=status,
            depth=depth,
            worker_count=worker_count,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    finally:
        db.close()


# ============================================================================
# Task D.2: API Modules Integration Tests
# ============================================================================


# --- Authentication & Authorization Tests ---


def test_get_current_user_valid_token(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test JWT validation success with valid token."""
    response = client.get("/api/supervisor/workers", headers=auth_headers)
    assert response.status_code == 200


def test_get_current_user_invalid_token(client: TestClient) -> None:
    """Test JWT validation failure with invalid token (401 Unauthorized)."""
    headers = {"Authorization": "Bearer invalid.token.here"}
    response = client.get("/api/supervisor/workers", headers=headers)
    assert response.status_code == 401
    assert "detail" in response.json()


def test_get_current_user_missing_token(client: TestClient) -> None:
    """Test JWT validation failure with missing token (401 Unauthorized)."""
    response = client.get("/api/supervisor/workers")
    assert response.status_code == 401


def test_require_scope_authorized(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test scope check success with proper authorization."""
    # auth_headers includes supervisor:read scope
    response = client.get("/api/supervisor/workers", headers=auth_headers)
    assert response.status_code == 200


def test_require_scope_forbidden(client: TestClient) -> None:
    """Test scope check failure (403 Forbidden)."""
    # Create token without required scopes
    token = create_dev_token(scopes=["jobs:read"])  # Missing supervisor:read
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/supervisor/workers", headers=headers)
    assert response.status_code == 403
    assert "detail" in response.json()


# --- Supervisor API Tests ---


def test_supervisor_list_workers_empty(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test GET /api/supervisor/workers endpoint with no workers."""
    response = client.get("/api/supervisor/workers", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "workers" in data
    assert data["total"] == 0
    assert isinstance(data["workers"], list)
    assert len(data["workers"]) == 0


def test_supervisor_list_workers_populated(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Test GET /api/supervisor/workers endpoint with seeded workers."""
    _seed_worker("worker-1", "ws-1", WorkerStatus.IDLE)
    _seed_worker("worker-2", "ws-1", WorkerStatus.RUNNING)

    response = client.get("/api/supervisor/workers", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["workers"]) == 2


def test_supervisor_get_worker_success(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test GET /api/supervisor/workers/{id} endpoint with existing worker."""
    worker = _seed_worker("worker-detail", "ws-1", WorkerStatus.IDLE)

    response = client.get(f"/api/supervisor/workers/{worker.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == worker.id
    assert data["workspace_id"] == "ws-1"
    assert data["status"] == "IDLE"


def test_supervisor_get_worker_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test GET /api/supervisor/workers/{id} endpoint with non-existent worker (404)."""
    response = client.get("/api/supervisor/workers/nonexistent-worker", headers=auth_headers)
    assert response.status_code == 404
    assert "detail" in response.json()


def test_supervisor_terminate_worker(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test POST /api/supervisor/workers/{id}/terminate endpoint."""
    worker = _seed_worker("worker-terminate", "ws-1", WorkerStatus.RUNNING)

    response = client.post(
        f"/api/supervisor/workers/{worker.id}/terminate",
        headers=auth_headers,
        json={"reason": "User requested termination"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == worker.id
    assert data["status"] == "TERMINATED"


def test_supervisor_metrics(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test GET /api/supervisor/metrics endpoint."""
    _seed_worker("m1", "ws-1", WorkerStatus.IDLE)
    _seed_worker("m2", "ws-1", WorkerStatus.RUNNING)

    response = client.get("/api/supervisor/metrics", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_workers" in data
    assert "by_status" in data
    assert data["total_workers"] >= 2
    assert isinstance(data["by_status"], dict)


# --- Resource Manager API Tests ---


def test_resources_get_quotas(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test GET /api/resources/quotas endpoint."""
    response = client.get("/api/resources/quotas", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "quotas" in data
    assert isinstance(data["quotas"], list)
    if len(data["quotas"]) > 0:
        assert "depth" in data["quotas"][0]
        assert "max_workers" in data["quotas"][0]


def test_resources_allocate_success(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test POST /api/resources/allocate endpoint with valid allocation."""
    worker = _seed_worker("alloc-worker", "ws-1", WorkerStatus.IDLE)
    job = _seed_job("alloc-job", "Test allocation task", JobStatus.PENDING, depth=0, worker_count=1)

    response = client.post(
        "/api/resources/allocate",
        headers=auth_headers,
        json={"job_id": job.id, "depth": 0, "worker_count": 1},
    )
    assert response.status_code in (200, 201)
    data = response.json()
    assert "job_id" in data
    assert data["job_id"] == job.id


def test_resources_release(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test POST /api/resources/release endpoint."""
    worker = _seed_worker("release-worker", "ws-1", WorkerStatus.RUNNING)
    job = _seed_job("release-job", "Test release task", JobStatus.RUNNING, depth=0, worker_count=1)

    response = client.post(
        "/api/resources/release",
        headers=auth_headers,
        json={"job_id": job.id, "depth": 0},
    )
    assert response.status_code == 200
    data = response.json()
    assert "released" in data


def test_resources_usage(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test GET /api/resources/usage endpoint."""
    _seed_worker("usage-w1", "ws-1", WorkerStatus.IDLE)
    _seed_worker("usage-w2", "ws-1", WorkerStatus.RUNNING)

    response = client.get("/api/resources/usage", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "usage" in data
    assert isinstance(data["usage"], list)


# --- Job Orchestrator API Tests ---


def test_jobs_submit(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test POST /api/jobs/submit endpoint."""
    response = client.post(
        "/api/jobs/submit",
        headers=auth_headers,
        json={
            "task_description": "Test task submission",
            "worker_count": 1,
            "depth": 0,
        },
    )
    assert response.status_code == 200 or response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "PENDING"


def test_jobs_get_success(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test GET /api/jobs/{id} endpoint with existing job."""
    job = _seed_job(
        "job-get-test", "Test job retrieval", JobStatus.PENDING, depth=0, worker_count=1
    )

    response = client.get(f"/api/jobs/{job.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job.id
    assert data["status"] == "PENDING"


def test_jobs_get_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test GET /api/jobs/{id} endpoint with non-existent job (404)."""
    response = client.get("/api/jobs/nonexistent-job-id", headers=auth_headers)
    assert response.status_code == 404
    assert "detail" in response.json()


def test_jobs_list(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test GET /api/jobs/list endpoint."""
    _seed_job("list-job-1", "Test task 1", JobStatus.PENDING, depth=0, worker_count=1)
    _seed_job("list-job-2", "Test task 2", JobStatus.RUNNING, depth=0, worker_count=2)

    response = client.get("/api/jobs", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_jobs_cancel(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test POST /api/jobs/{id}/cancel endpoint."""
    job = _seed_job("cancel-job", "Test cancel task", JobStatus.RUNNING, depth=0, worker_count=1)

    response = client.post(
        f"/api/jobs/{job.id}/cancel",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job.id
    assert data["status"] == "CANCELED"


# --- Error Handling Tests ---


def test_validation_error_422(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test validation error (422 Unprocessable Entity) with invalid request body."""
    response = client.post(
        "/api/jobs/submit",
        headers=auth_headers,
        json={"invalid_field": "value"},  # Missing required fields
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_readonly_user_cannot_write(client: TestClient, readonly_headers: dict[str, str]) -> None:
    """Test that read-only user cannot perform write operations (403 Forbidden)."""
    response = client.post(
        "/api/jobs/submit",
        headers=readonly_headers,
        json={"task_file_path": "/tmp/task.txt", "priority": 5},
    )
    assert response.status_code == 403
    assert "detail" in response.json()
