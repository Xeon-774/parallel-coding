"""Supervisor API for worker monitoring and control.

Implements six endpoints under `/api / supervisor` for listing workers,
retrieving details, pausing / resuming / terminating workers, and aggregate
metrics. Secured via bearer tokens with scope - based authorization.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from orchestrator.api.dependencies import get_db
from orchestrator.api.dependencies import require_scope as _require_scope
from orchestrator.core.auth import TokenData
from orchestrator.core.db_models import Worker, WorkerStatus
from orchestrator.core.state_machine import WorkerStateMachine

router = APIRouter(prefix="/api / supervisor", tags=["supervisor"])


class WorkerResponse(BaseModel):
    """Serializable worker representation for responses."""

    id: str
    workspace_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkerListResponse(BaseModel):
    workers: List[WorkerResponse]
    total: int
    limit: int
    offset: int


class MetricsResponse(BaseModel):
    total_workers: int = Field(ge=0)
    by_status: dict[str, int]


@router.get(
    "/workers",
    response_model=WorkerListResponse,
    summary="List all workers",
    description="""
    Retrieve a paginated list of workers with optional filtering.

    **Filters:**
    - `workspace_id`: Filter by workspace
    - `status`: Filter by worker status (IDLE, RUNNING, PAUSED, COMPLETED, FAILED, TERMINATED)

    **Pagination:**
    - `limit`: Maximum number of results (1 - 100, default: 50)
    - `offset`: Number of results to skip (default: 0)

    **Required Scope:** `supervisor:read`

    **Example Response:**
    ```json
    {
      "workers": [
        {
          "id": "worker - 123",
          "workspace_id": "ws - 001",
          "status": "RUNNING",
          "created_at": "2025 - 10 - 28T10:00:00Z",
          "updated_at": "2025 - 10 - 28T10:05:00Z"
        }
      ],
      "total": 1,
      "limit": 50,
      "offset": 0
    }
    ```
    """,
    response_description="List of workers matching the filter criteria",
)
async def list_workers(
    workspace_id: Optional[str] = Query(None, description="Filter by workspace ID"),
    status: Optional[WorkerStatus] = Query(None, description="Filter by worker status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    user: TokenData = Depends(_require_scope("supervisor:read")),
) -> WorkerListResponse:
    """List workers with optional filters and pagination."""

    query = db.query(Worker)
    if workspace_id:
        query = query.filter(Worker.workspace_id == workspace_id)
    if status:
        query = query.filter(Worker.status == status)

    total = query.count()
    workers = query.offset(offset).limit(limit).all()
    return WorkerListResponse(workers=list(workers), total=total, limit=limit, offset=offset)


@router.get("/workers/{worker_id}", response_model=WorkerResponse)
async def get_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    user: TokenData = Depends(_require_scope("supervisor:read")),
) -> WorkerResponse:
    """Get a single worker by id."""

    worker = db.get(Worker, worker_id)
    if worker is None:
        raise HTTPException(status_code=404, detail="Worker not found")
    return WorkerResponse.model_validate(worker)


@router.post("/workers/{worker_id}/pause", response_model=WorkerResponse)
async def pause_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    user: TokenData = Depends(_require_scope("supervisor:write")),
) -> WorkerResponse:
    """Pause worker execution."""

    sm = WorkerStateMachine(db)
    try:
        worker = sm.transition_worker(
            worker_id=worker_id, to_state=WorkerStatus.PAUSED, reason="User paused worker"
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Worker not found")
    return WorkerResponse.model_validate(worker)


@router.post("/workers/{worker_id}/resume", response_model=WorkerResponse)
async def resume_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    user: TokenData = Depends(_require_scope("supervisor:write")),
) -> WorkerResponse:
    """Resume worker execution."""

    sm = WorkerStateMachine(db)
    try:
        worker = sm.transition_worker(
            worker_id=worker_id, to_state=WorkerStatus.RUNNING, reason="User resumed worker"
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Worker not found")
    return WorkerResponse.model_validate(worker)


@router.post("/workers/{worker_id}/terminate", response_model=WorkerResponse)
async def terminate_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    user: TokenData = Depends(_require_scope("supervisor:write")),
) -> WorkerResponse:
    """Terminate a worker."""

    sm = WorkerStateMachine(db)
    try:
        worker = sm.transition_worker(
            worker_id=worker_id, to_state=WorkerStatus.TERMINATED, reason="User terminated worker"
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Worker not found")
    return WorkerResponse.model_validate(worker)


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    db: Session = Depends(get_db),
    user: TokenData = Depends(_require_scope("supervisor:read")),
) -> MetricsResponse:
    """Return aggregate worker metrics (total and counts by status)."""

    total = db.query(Worker).count()
    by_status: dict[str, int] = {}
    for st in WorkerStatus:
        by_status[st.value] = db.query(Worker).filter(Worker.status == st).count()
    return MetricsResponse(total_workers=total, by_status=by_status)
