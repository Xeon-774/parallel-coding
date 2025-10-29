"""Jobs API endpoints for the Job Orchestrator.

Implements job submission, retrieval, cancellation, and listing.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from orchestrator.api.dependencies import TokenData, get_db, require_scope
from orchestrator.api.schemas import JobResponse, JobSubmitRequest
from orchestrator.core.db_models import Job, JobStatus
from orchestrator.core.state_machine import (
    EntityNotFoundError,
    JobStateMachine,
    StateTransitionError,
)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _get_job_or_404(db: Session, job_id: str) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.post(
    "/submit",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new job",
    description="""
    Create and submit a new job for hierarchical execution.

    **Request Body:**
    - `task_description`: Task to execute (required, 1-4096 chars)
    - `worker_count`: Number of workers to allocate (1-1000)
    - `depth`: Hierarchy depth level (0-1000, default: 0)
    - `parent_job_id`: Parent job ID for hierarchical jobs (optional)

    **Job Lifecycle:**
    ```
    SUBMITTED → PENDING → RUNNING → COMPLETED
             → PENDING → RUNNING → FAILED
             → PENDING → CANCELED
    ```

    **Required Scope:** `jobs:write`

    **Example Request:**
    ```json
    {
      "task_description": "Implement user authentication",
      "worker_count": 3,
      "depth": 0
    }
    ```

    **Example Response:**
    ```json
    {
      "id": "j_a1b2c3d4e5f6",
      "status": "PENDING",
      "task_description": "Implement user authentication",
      "worker_count": 3,
      "depth": 0,
      "parent_job_id": null,
      "created_at": "2025-10-28T10:00:00Z",
      "updated_at": "2025-10-28T10:00:01Z"
    }
    ```
    """,
    response_description="Created job with PENDING status",
)
async def submit_job(
    request: JobSubmitRequest,
    db: Session = Depends(get_db),
    user: TokenData = Depends(require_scope("jobs:write")),
) -> JobResponse:
    """Submit a new job and transition it to PENDING.

    Creates a ``SUBMITTED`` job, persists it, then uses the state machine to
    transition to ``PENDING``.
    """

    job = Job(
        depth=request.depth,
        worker_count=request.worker_count,
        task_description=request.task_description,
        parent_job_id=request.parent_job_id,
        status=JobStatus.SUBMITTED,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    sm = JobStateMachine(db)
    job = sm.transition_job(job.id, JobStatus.PENDING)
    return JobResponse.model_validate(job)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    _: TokenData = Depends(require_scope("jobs:read")),
) -> JobResponse:
    """Return job details by identifier."""

    job = _get_job_or_404(db, job_id)
    return JobResponse.model_validate(job)


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    _: TokenData = Depends(require_scope("jobs:write")),
) -> JobResponse:
    """Cancel a job using the state machine.

    Returns the updated job representation. If cancellation is not allowed
    from the current state, returns ``400``.
    """

    sm = JobStateMachine(db)
    try:
        job = sm.cancel_job(job_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    except StateTransitionError as exc:  # noqa: PERF203 keep explicit mapping
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return JobResponse.model_validate(job)


@router.get("", response_model=List[JobResponse])
async def list_jobs(
    depth: Optional[int] = Query(default=None, ge=0),
    status_: Optional[JobStatus] = Query(default=None, alias="status"),
    parent_job_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: TokenData = Depends(require_scope("jobs:read")),
) -> List[JobResponse]:
    """List jobs with optional filters and pagination."""

    stmt = select(Job)
    if depth is not None:
        stmt = stmt.where(Job.depth == depth)
    if status_ is not None:
        stmt = stmt.where(Job.status == status_)
    if parent_job_id is not None:
        stmt = stmt.where(Job.parent_job_id == parent_job_id)
    stmt = stmt.offset(offset).limit(limit)

    rows = db.execute(stmt).scalars().all()
    return [JobResponse.model_validate(j) for j in rows]
