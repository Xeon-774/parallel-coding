from __future__ import annotations

from typing import Dict, Generator

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from orchestrator.api.app import create_app
from orchestrator.api import dependencies
from orchestrator.core.db_models import Base, Job, JobStatus


@pytest.fixture(scope="function")
def db_session_override() -> Generator[None, None, None]:
    # Use a temporary SQLite file to ensure persistence across sessions
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        def _get_db():
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()

        old_get_db = dependencies.get_db
        dependencies.get_db = _get_db  # type: ignore[assignment]
        try:
            yield
        finally:
            dependencies.get_db = old_get_db  # type: ignore[assignment]


@pytest.fixture()
def client(db_session_override: None) -> TestClient:  # noqa: PT004: effect-only fixture
    app = create_app()
    return TestClient(app)


def auth_headers(scopes: str) -> Dict[str, str]:
    return {"X-Scopes": scopes}


def submit_sample_job(client: TestClient, **overrides):
    payload = {
        "task_description": "Sample Task",
        "worker_count": 2,
        "depth": 0,
        "parent_job_id": None,
    }
    payload.update(overrides)
    resp = client.post("/api/jobs/submit", json=payload, headers=auth_headers("jobs:write jobs:read"))
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_submit_job_transitions_to_pending(client: TestClient):
    data = submit_sample_job(client)
    assert data["status"] == "PENDING"
    assert data["worker_count"] == 2
    assert data["task_description"] == "Sample Task"


def test_get_job_details(client: TestClient):
    created = submit_sample_job(client)
    job_id = created["id"]
    resp = client.get(f"/api/jobs/{job_id}", headers=auth_headers("jobs:read"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == job_id
    assert body["status"] == "PENDING"


def test_cancel_job_from_pending(client: TestClient):
    created = submit_sample_job(client)
    job_id = created["id"]
    resp = client.post(f"/api/jobs/{job_id}/cancel", headers=auth_headers("jobs:write jobs:read"))
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"


def test_cancel_completed_job_returns_400(client: TestClient):
    created = submit_sample_job(client)
    job_id = created["id"]

    # Manually set to COMPLETED using the same DB dependency
    for db in dependencies.get_db():  # type: ignore[misc]
        job = db.get(Job, job_id)
        job.status = JobStatus.COMPLETED
        db.add(job)
        db.commit()
        break

    resp = client.post(f"/api/jobs/{job_id}/cancel", headers=auth_headers("jobs:write"))
    assert resp.status_code == 400
    assert "Invalid transition" in resp.json()["detail"]


def test_list_jobs_with_filters_and_pagination(client: TestClient):
    root = submit_sample_job(client, depth=0)
    child1 = submit_sample_job(client, depth=1, parent_job_id=root["id"])  # noqa: F841
    child2 = submit_sample_job(client, depth=1, parent_job_id=root["id"])  # noqa: F841
    other_root = submit_sample_job(client, depth=0)  # noqa: F841

    # Filter by depth
    resp = client.get("/api/jobs", params={"depth": 1}, headers=auth_headers("jobs:read"))
    assert resp.status_code == 200
    jobs = resp.json()
    assert all(j["depth"] == 1 for j in jobs)
    assert len(jobs) == 2

    # Filter by parent_job_id
    resp = client.get(
        "/api/jobs",
        params={"parent_job_id": root["id"]},
        headers=auth_headers("jobs:read"),
    )
    assert resp.status_code == 200
    jobs = resp.json()
    assert len(jobs) == 2
    assert all(j["parent_job_id"] == root["id"] for j in jobs)

    # Pagination
    resp = client.get("/api/jobs", params={"limit": 1, "offset": 0}, headers=auth_headers("jobs:read"))
    assert resp.status_code == 200
    jobs = resp.json()
    assert len(jobs) == 1


def test_security_scopes_enforced(client: TestClient):
    # Missing write scope
    payload = {
        "task_description": "Nope",
        "worker_count": 1,
        "depth": 0,
        "parent_job_id": None,
    }
    resp = client.post("/api/jobs/submit", json=payload, headers=auth_headers("jobs:read"))
    assert resp.status_code == 403

    # Missing read scope
    created = submit_sample_job(client)
    resp = client.get(f"/api/jobs/{created['id']}")
    assert resp.status_code == 403

