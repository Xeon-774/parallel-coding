"""Supervisor API routes.

Provides FastAPI endpoints for managing supervised Claude Code processes.

Endpoints:
    POST   /api / v1 / supervisor / spawn       -> Spawn new supervisor
    GET    /api / v1 / supervisor/{id}        -> Get supervisor status
    DELETE /api / v1 / supervisor/{id}        -> Terminate supervisor
    GET    /api / v1 / supervisor             -> List active supervisors
    POST   /api / v1 / supervisor/{id}/respond-> Respond to confirmation
    GET    /api / v1 / supervisor/{id}/output -> Get buffered output

All endpoints require an Authorization token and validate inputs via Pydantic.
"""

from __future__ import annotations

import os
from typing import Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, ValidationError, field_validator

from orchestrator.core.worker.worker_manager import (
    WorkerManager,
)

# Constants
DEFAULT_LIMIT = 50
MAX_LIMIT = 200
DEFAULT_TIMEOUT = 300


# Authentication
def _get_expected_token() -> str:
    return os.environ.get("API_TOKEN", "dev - token")


def authenticate(request: Request) -> None:
    """Simple bearer token authentication dependency.

    Raises 401 when the Authorization header is missing / invalid.

    Examples:
        In tests, set header: Authorization: Bearer dev - token
    """

    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    token = auth.split(" ", 1)[1].strip()
    if token != _get_expected_token():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


# Request / Response models
class SpawnSupervisorRequest(BaseModel):
    """Request validation for spawning a supervisor process."""

    task_file: str = Field(..., min_length=1, max_length=255)
    workspace_root: str = Field(..., min_length=1, max_length=255)
    timeout: int = Field(default=DEFAULT_TIMEOUT, ge=10, le=3600)

    @field_validator("task_file")
    @classmethod
    def validate_task_file_path(cls, v: str) -> str:
        if ".." in v or v.startswith("/") or "\\.." in v:
            raise ValueError("Invalid task file path")
        return v


class SpawnSupervisorResponse(BaseModel):
    supervisor_id: str
    status: Literal["spawning", "running", "terminated", "error"]


class SupervisorStatusResponse(BaseModel):
    supervisor_id: str
    status: Literal["spawning", "running", "terminated", "error"]
    alive: bool
    last_error: Optional[str] = None
    uptime_secs: float = 0.0
    output_lines: int = 0


class ListSupervisorsResponse(BaseModel):
    total: int
    items: List[SupervisorStatusResponse]


class RespondToConfirmationRequest(BaseModel):
    """Request validation for confirmation responses."""

    decision: Literal["APPROVE", "DENY", "ESCALATE"]
    reason: str = Field(default="", max_length=500)


class OutputLine(BaseModel):
    timestamp: float
    content: str


class OutputResponse(BaseModel):
    supervisor_id: str
    items: List[OutputLine]
    next_offset: int


# In - memory app state
_worker_manager: Optional[WorkerManager] = None


def get_worker_manager() -> WorkerManager:
    """Singleton WorkerManager accessor for API layer.

    Uses dependency injection - friendly factory; tests can monkeypatch this
    function to return a mocked manager.
    """

    global _worker_manager
    if _worker_manager is None:
        from orchestrator.config import OrchestratorConfig
        from orchestrator.utils.logger import get_logger  # type: ignore[import-not-found]

        config = OrchestratorConfig()
        logger = get_logger("supervisor_api")
        _worker_manager = WorkerManager(config=config, logger=logger)
    return _worker_manager


router = APIRouter(prefix="/api / v1 / supervisor", tags=["supervisor"])


@router.post("/spawn", response_model=SpawnSupervisorResponse, status_code=status.HTTP_201_CREATED)
async def spawn_supervisor(
    payload: SpawnSupervisorRequest,
    _auth: None = Depends(authenticate),
    manager: WorkerManager = Depends(get_worker_manager),
) -> SpawnSupervisorResponse:
    """Spawn a new supervised Claude Code instance.

    Validates input paths and delegates to WorkerManager.
    """

    try:
        result = await manager.spawn_supervised_worker(
            task_file=payload.task_file,
            workspace_root=payload.workspace_root,
            timeout=payload.timeout,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="spawn failed"
        ) from exc

    return SpawnSupervisorResponse(supervisor_id=result.supervisor_id, status=result.status.value)


@router.get("/{supervisor_id}", response_model=SupervisorStatusResponse)
async def get_supervisor(
    supervisor_id: str,
    _auth: None = Depends(authenticate),
    manager: WorkerManager = Depends(get_worker_manager),
) -> SupervisorStatusResponse:
    """Get status for a supervisor by id."""

    status_info = await manager.get_supervisor_status(worker_id=supervisor_id)
    if status_info is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return SupervisorStatusResponse(
        supervisor_id=supervisor_id,
        status=status_info.status.value,
        alive=status_info.alive,
        last_error=status_info.last_error,
        uptime_secs=status_info.uptime_secs,
        output_lines=status_info.output_lines,
    )


@router.delete("/{supervisor_id}")
async def delete_supervisor(
    supervisor_id: str,
    _auth: None = Depends(authenticate),
    manager: WorkerManager = Depends(get_worker_manager),
) -> Dict[str, bool]:
    """Terminate a supervisor and cleanup resources."""

    ok = await manager.terminate_supervisor(worker_id=supervisor_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return {"terminated": True}


@router.get("/")
async def list_supervisors(
    _auth: None = Depends(authenticate),
    manager: WorkerManager = Depends(get_worker_manager),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    status_filter: Optional[Literal["spawning", "running", "terminated", "error"]] = Query(
        default=None
    ),
) -> ListSupervisorsResponse:
    """List active supervisors with optional filtering and pagination."""

    items = await manager.list_supervisors()
    if status_filter:
        items = [s for s in items if s.status.value == status_filter]
    total = len(items)
    page = items[offset : offset + limit]
    return ListSupervisorsResponse(
        total=total,
        items=[
            SupervisorStatusResponse(
                supervisor_id=s.supervisor_id,
                status=s.status.value,
                alive=s.alive,
                last_error=s.last_error,
                uptime_secs=s.uptime_secs,
                output_lines=s.output_lines,
            )
            for s in page
        ],
    )


@router.post("/{supervisor_id}/respond")
async def respond_to_confirmation(
    supervisor_id: str,
    payload: RespondToConfirmationRequest,
    _auth: None = Depends(authenticate),
    manager: WorkerManager = Depends(get_worker_manager),
) -> Dict[str, str]:
    """Respond to a pending confirmation prompt.

    In this reference implementation, responses are recorded and surfaced in
    status; integration with an actual TTY is left to the supervisor layer.
    """

    ok = await manager.record_confirmation_response(
        worker_id=supervisor_id, decision=payload.decision, reason=payload.reason
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return {"status": "recorded"}


@router.get("/{supervisor_id}/output", response_model=OutputResponse)
async def get_output(
    supervisor_id: str,
    _auth: None = Depends(authenticate),
    manager: WorkerManager = Depends(get_worker_manager),
    offset: int = Query(default=0, ge=0),
    start_ts: Optional[float] = Query(default=None, ge=0.0),
    end_ts: Optional[float] = Query(default=None, ge=0.0),
) -> OutputResponse:
    """Retrieve buffered output lines with pagination and optional time range."""

    lines = await manager.get_output(worker_id=supervisor_id)
    if lines is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")

    def _in_range(ts: float) -> bool:
        if start_ts is not None and ts < start_ts:
            return False
        if end_ts is not None and ts > end_ts:
            return False
        return True

    filtered = [ln for ln in lines if _in_range(ln[0])]
    items = [OutputLine(timestamp=ts, content=content) for ts, content in filtered[offset:]]
    next_offset = offset + len(items)
    return OutputResponse(supervisor_id=supervisor_id, items=items, next_offset=next_offset)
