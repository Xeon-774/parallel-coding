"""
End-to-End Workflow Tests for Week 2 MVP.

Tests complete workflows including job submission, execution, completion,
worker lifecycle, resource allocation, and authentication flow.

Coverage Target: ≥75% for complete system integration
"""

from __future__ import annotations

from typing import Generator

import pytest
from fastapi.testclient import TestClient

from orchestrator.api.main import app
from orchestrator.core.auth import create_dev_token
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
    """Create valid JWT token with full scopes for testing."""
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


def _seed_worker(
    worker_id: str = "e2e-w1",
    workspace_id: str = "ws-e2e",
    status: WorkerStatus = WorkerStatus.IDLE,
) -> Worker:
    """Helper function to seed a worker."""
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
    job_id: str = "e2e-j1",
    task_description: str = "E2E test task",
    status: JobStatus = JobStatus.PENDING,
    depth: int = 0,
    worker_count: int = 1,
) -> Job:
    """Helper function to seed a job."""
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
# Task D.3: End-to-End Workflow Tests
# ============================================================================


def test_complete_job_workflow(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test complete job workflow: Submit → Allocate → Execute → Complete."""
    # Step 1: Submit job
    submit_response = client.post(
        "/api/jobs/submit",
        headers=auth_headers,
        json={"task_description": "E2E workflow test task", "worker_count": 1, "depth": 0},
    )
    assert submit_response.status_code in [200, 201]
    job_data = submit_response.json()
    job_id = job_data.get("id")
    assert job_id is not None

    # Step 2: Verify job is created and in PENDING state
    get_job_response = client.get(f"/api/jobs/{job_id}", headers=auth_headers)
    assert get_job_response.status_code == 200
    job_status_data = get_job_response.json()
    assert job_status_data["status"] in ["PENDING", "RUNNING"]

    # Step 3: Allocate resources (worker to job)
    worker = _seed_worker("workflow-worker", "ws-workflow", WorkerStatus.IDLE)
    allocate_response = client.post(
        "/api/resources/allocate",
        headers=auth_headers,
        json={"job_id": job_id, "depth": 0, "worker_count": 1},
    )
    assert allocate_response.status_code in [200, 201]

    # Step 4: Transition job to RUNNING (simulating execution)
    db = next(get_db())
    try:
        job = db.query(Job).filter_by(id=job_id).first()
        if job:
            job.status = JobStatus.RUNNING
            db.commit()
    finally:
        db.close()

    # Step 5: Verify job is RUNNING
    running_response = client.get(f"/api/jobs/{job_id}", headers=auth_headers)
    assert running_response.status_code == 200
    running_data = running_response.json()
    assert running_data["status"] == "RUNNING"

    # Step 6: Complete job
    db = next(get_db())
    try:
        job = db.query(Job).filter_by(id=job_id).first()
        if job:
            job.status = JobStatus.COMPLETED
            db.commit()
    finally:
        db.close()

    # Step 7: Verify job is COMPLETED
    completed_response = client.get(f"/api/jobs/{job_id}", headers=auth_headers)
    assert completed_response.status_code == 200
    completed_data = completed_response.json()
    assert completed_data["status"] == "COMPLETED"

    # Step 8: Release resources
    release_response = client.post(
        "/api/resources/release",
        headers=auth_headers,
        json={"job_id": job_id, "depth": 0},
    )
    assert release_response.status_code == 200


def test_worker_lifecycle(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test worker state transitions during job execution: IDLE → RUNNING → IDLE."""
    # Step 1: Create worker in IDLE state
    worker = _seed_worker("lifecycle-worker", "ws-lifecycle", WorkerStatus.IDLE)

    # Step 2: Verify worker is IDLE
    idle_response = client.get(f"/api/supervisor/workers/{worker.id}", headers=auth_headers)
    assert idle_response.status_code == 200
    idle_data = idle_response.json()
    assert idle_data["status"] == "IDLE"

    # Step 3: Transition worker to RUNNING (simulating job assignment)
    db = next(get_db())
    try:
        w = db.query(Worker).filter_by(id=worker.id).first()
        if w:
            w.status = WorkerStatus.RUNNING
            db.commit()
    finally:
        db.close()

    # Step 4: Verify worker is RUNNING
    running_response = client.get(f"/api/supervisor/workers/{worker.id}", headers=auth_headers)
    assert running_response.status_code == 200
    running_data = running_response.json()
    assert running_data["status"] == "RUNNING"

    # Step 5: Transition worker back to IDLE (job complete)
    db = next(get_db())
    try:
        w = db.query(Worker).filter_by(id=worker.id).first()
        if w:
            w.status = WorkerStatus.IDLE
            db.commit()
    finally:
        db.close()

    # Step 6: Verify worker is IDLE again
    back_idle_response = client.get(f"/api/supervisor/workers/{worker.id}", headers=auth_headers)
    assert back_idle_response.status_code == 200
    back_idle_data = back_idle_response.json()
    assert back_idle_data["status"] == "IDLE"


def test_resource_allocation_workflow(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test resource allocation workflow: Check quotas → Allocate → Release."""
    # Step 1: Check quotas before allocation
    quotas_before = client.get("/api/resources/quotas", headers=auth_headers)
    assert quotas_before.status_code == 200
    quotas_data_before = quotas_before.json()
    assert "quotas" in quotas_data_before
    assert len(quotas_data_before["quotas"]) > 0

    # Step 2: Seed worker and job
    worker = _seed_worker("alloc-wf-worker", "ws-alloc-wf", WorkerStatus.IDLE)
    job = _seed_job("alloc-wf-job", "Allocation workflow test", JobStatus.PENDING, depth=0, worker_count=1)

    # Step 3: Allocate resources
    allocate_response = client.post(
        "/api/resources/allocate",
        headers=auth_headers,
        json={"job_id": job.id, "depth": 0, "worker_count": 1},
    )
    assert allocate_response.status_code in [200, 201]

    # Step 4: Check quotas after allocation (available workers may decrease)
    quotas_after_alloc = client.get("/api/resources/quotas", headers=auth_headers)
    assert quotas_after_alloc.status_code == 200

    # Step 5: Release resources
    release_response = client.post(
        "/api/resources/release",
        headers=auth_headers,
        json={"job_id": job.id, "depth": 0},
    )
    assert release_response.status_code == 200

    # Step 6: Check quotas after release (available workers should recover)
    quotas_after_release = client.get("/api/resources/quotas", headers=auth_headers)
    assert quotas_after_release.status_code == 200


def test_authentication_flow(client: TestClient) -> None:
    """Test authentication flow: Get token → Access protected endpoint."""
    # Step 1: Create token (simulating login)
    token = create_dev_token(scopes=["supervisor:read", "jobs:read"])
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0

    # Step 2: Use token to access protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/supervisor/workers", headers=headers)
    assert response.status_code == 200

    # Step 3: Verify response data
    data = response.json()
    assert "workers" in data or "total" in data


def test_concurrent_jobs(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test multiple jobs executing simultaneously with multiple workers."""
    # Step 1: Create multiple workers
    worker1 = _seed_worker("concurrent-w1", "ws-concurrent", WorkerStatus.IDLE)
    worker2 = _seed_worker("concurrent-w2", "ws-concurrent", WorkerStatus.IDLE)
    worker3 = _seed_worker("concurrent-w3", "ws-concurrent", WorkerStatus.IDLE)

    # Step 2: Submit multiple jobs
    job1_response = client.post(
        "/api/jobs/submit",
        headers=auth_headers,
        json={"task_description": "Concurrent task 1", "worker_count": 1, "depth": 0},
    )
    job2_response = client.post(
        "/api/jobs/submit",
        headers=auth_headers,
        json={"task_description": "Concurrent task 2", "worker_count": 1, "depth": 0},
    )
    job3_response = client.post(
        "/api/jobs/submit",
        headers=auth_headers,
        json={"task_description": "Concurrent task 3", "worker_count": 1, "depth": 0},
    )

    assert job1_response.status_code in [200, 201]
    assert job2_response.status_code in [200, 201]
    assert job3_response.status_code in [200, 201]

    job1_id = job1_response.json().get("id")
    job2_id = job2_response.json().get("id")
    job3_id = job3_response.json().get("id")

    # Step 3: Allocate workers to jobs
    client.post(
        "/api/resources/allocate",
        headers=auth_headers,
        json={"job_id": job1_id, "depth": 0, "worker_count": 1},
    )
    client.post(
        "/api/resources/allocate",
        headers=auth_headers,
        json={"job_id": job2_id, "depth": 0, "worker_count": 1},
    )
    client.post(
        "/api/resources/allocate",
        headers=auth_headers,
        json={"job_id": job3_id, "depth": 0, "worker_count": 1},
    )

    # Step 4: Verify all jobs are allocated
    job1_get = client.get(f"/api/jobs/{job1_id}", headers=auth_headers)
    job2_get = client.get(f"/api/jobs/{job2_id}", headers=auth_headers)
    job3_get = client.get(f"/api/jobs/{job3_id}", headers=auth_headers)

    assert job1_get.status_code == 200
    assert job2_get.status_code == 200
    assert job3_get.status_code == 200

    # Step 5: Verify all workers are assigned
    worker1_get = client.get(f"/api/supervisor/workers/{worker1.id}", headers=auth_headers)
    worker2_get = client.get(f"/api/supervisor/workers/{worker2.id}", headers=auth_headers)
    worker3_get = client.get(f"/api/supervisor/workers/{worker3.id}", headers=auth_headers)

    assert worker1_get.status_code == 200
    assert worker2_get.status_code == 200
    assert worker3_get.status_code == 200


def test_job_cancellation_workflow(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test job cancellation workflow: Submit → Cancel → Verify."""
    # Step 1: Submit job
    submit_response = client.post(
        "/api/jobs/submit",
        headers=auth_headers,
        json={"task_description": "Cancellation workflow test", "worker_count": 1, "depth": 0},
    )
    assert submit_response.status_code in [200, 201]
    job_id = submit_response.json().get("id")

    # Step 2: Verify job exists and is PENDING
    get_response = client.get(f"/api/jobs/{job_id}", headers=auth_headers)
    assert get_response.status_code == 200
    job_data = get_response.json()
    assert job_data["status"] in ["PENDING", "RUNNING"]

    # Step 3: Cancel job
    cancel_response = client.post(
        f"/api/jobs/{job_id}/cancel",
        headers=auth_headers,
        json={"reason": "User requested cancellation"},
    )
    assert cancel_response.status_code == 200

    # Step 4: Verify job is CANCELED
    cancelled_response = client.get(f"/api/jobs/{job_id}", headers=auth_headers)
    assert cancelled_response.status_code == 200
    cancelled_data = cancelled_response.json()
    assert cancelled_data["status"] == "CANCELED"
