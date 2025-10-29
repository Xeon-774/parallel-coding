from __future__ import annotations

from typing import Generator

import pytest
from fastapi.testclient import TestClient

from orchestrator.api.main import app
from orchestrator.core.auth import create_dev_token
from orchestrator.core.database import get_db
from orchestrator.core.db_models import Worker, WorkerStatus


@pytest.fixture(autouse=True)
def cleanup_db() -> Generator[None, None, None]:
    # Ensure a clean slate by deleting all workers before each test module run.
    db = next(get_db())
    try:
        db.query(Worker).delete()
        db.commit()
        yield
    finally:
        db.close()


client = TestClient(app)


def _auth_headers(scopes: list[str] | None = None) -> dict[str, str]:
    token = create_dev_token(scopes)
    return {"Authorization": f"Bearer {token}"}


def _seed_worker(
    worker_id: str = "w1", workspace_id: str = "ws1", status: WorkerStatus = WorkerStatus.RUNNING
) -> Worker:
    db = next(get_db())
    try:
        w = Worker(id=worker_id, workspace_id=workspace_id, status=status)
        db.add(w)
        db.commit()
        return w
    finally:
        db.close()


def test_list_workers_empty():
    r = client.get("/api/supervisor/workers", headers=_auth_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["workers"] == []


def test_list_workers_with_filters_and_pagination():
    _seed_worker("a", "ws1", WorkerStatus.RUNNING)
    _seed_worker("b", "ws1", WorkerStatus.PAUSED)
    _seed_worker("c", "ws2", WorkerStatus.RUNNING)
    # Filter by workspace
    r = client.get("/api/supervisor/workers?workspace_id=ws1", headers=_auth_headers())
    assert r.status_code == 200
    assert r.json()["total"] == 2
    # Filter by status
    r2 = client.get("/api/supervisor/workers?status=RUNNING", headers=_auth_headers())
    assert r2.status_code == 200
    assert r2.json()["total"] == 2
    # Pagination
    r3 = client.get("/api/supervisor/workers?limit=1&offset=1", headers=_auth_headers())
    assert r3.status_code == 200
    assert r3.json()["limit"] == 1


def test_get_worker_and_not_found():
    _seed_worker("z")
    ok = client.get("/api/supervisor/workers/z", headers=_auth_headers())
    assert ok.status_code == 200
    missing = client.get("/api/supervisor/workers/nope", headers=_auth_headers())
    assert missing.status_code == 404


def test_pause_resume_terminate_flow():
    _seed_worker("flow", status=WorkerStatus.RUNNING)
    pause = client.post("/api/supervisor/workers/flow/pause", headers=_auth_headers())
    assert pause.status_code == 200
    assert pause.json()["status"] == "PAUSED"
    resume = client.post("/api/supervisor/workers/flow/resume", headers=_auth_headers())
    assert resume.status_code == 200
    assert resume.json()["status"] == "RUNNING"
    term = client.post("/api/supervisor/workers/flow/terminate", headers=_auth_headers())
    assert term.status_code == 200
    assert term.json()["status"] == "TERMINATED"


def test_metrics_endpoint_counts():
    _seed_worker("m1", status=WorkerStatus.RUNNING)
    _seed_worker("m2", status=WorkerStatus.PAUSED)
    r = client.get("/api/supervisor/metrics", headers=_auth_headers())
    assert r.status_code == 200
    body = r.json()
    assert body["total_workers"] >= 2
    assert isinstance(body["by_status"], dict)


def test_auth_rejections_missing_and_scope():
    # Missing token
    r = client.get("/api/supervisor/workers")
    assert r.status_code == 403 or r.status_code == 401
    # Missing scope for write
    _seed_worker("s1")
    token = create_dev_token(["supervisor:read"])  # no write
    r2 = client.post(
        "/api/supervisor/workers/s1/pause",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 403
