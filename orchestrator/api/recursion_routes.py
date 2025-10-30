"""Recursion API routes for hierarchical orchestration.

Provides endpoints to submit jobs, query status, cancel jobs, view the active
hierarchy, fetch statistics, and validate configurations. Designed for use
with FastAPI and Pydantic v1.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator

from orchestrator.core.hierarchical import (
    HierarchicalJobOrchestrator,
    HierarchicalResourceManager,
)

router = APIRouter(prefix="/api / v1 / recursion", tags=["recursion"])


class RecursionConfig(BaseModel):
    max_depth: int = Field(default=3, ge=0, le=5)
    current_depth: int = Field(default=0, ge=0)
    workers_by_depth: Dict[int, int] = Field(default_factory=dict)
    orchestrator_api_key: str = Field(..., min_length=32)

    @validator("current_depth")
    def _validate_current_depth(cls, v: int, values: Dict[str, Any]) -> int:
        max_depth = values.get("max_depth", 3)
        if v > max_depth:
            raise ValueError(f"Current depth {v} exceeds max depth {max_depth}")
        return v

    @validator("orchestrator_api_key")
    def _validate_api_key(cls, v: str) -> str:
        if not v.startswith("sk - orch-"):
            raise ValueError("Invalid API key format")
        return v


class SubmitJobRequest(BaseModel):
    request: str = Field(..., min_length=10)
    config: Optional[RecursionConfig] = None


class SubmitJobResponse(BaseModel):
    job_id: str
    status: str
    depth: int


class StatusResponse(BaseModel):
    job_id: str
    status: str
    depth: int
    tree: Dict[str, Any]


class CancelResponse(BaseModel):
    job_id: str
    canceled: bool


class HierarchyResponse(BaseModel):
    usage: Dict[int, Dict[str, Any]]
    active_jobs: int


class StatsResponse(BaseModel):
    submitted: int
    completed: int
    failed: int
    canceled: int


class ValidationRequest(BaseModel):
    config: RecursionConfig


class ValidationResponse(BaseModel):
    valid: bool
    reason: Optional[str] = None


_rm_singleton: Optional[HierarchicalResourceManager] = None
_orch_singleton: Optional[HierarchicalJobOrchestrator] = None


def get_rm() -> HierarchicalResourceManager:
    global _rm_singleton
    if _rm_singleton is None:
        _rm_singleton = HierarchicalResourceManager()
    return _rm_singleton


def get_orchestrator(
    rm: HierarchicalResourceManager = Depends(get_rm),
) -> HierarchicalJobOrchestrator:
    global _orch_singleton
    if _orch_singleton is None:
        _orch_singleton = HierarchicalJobOrchestrator(resource_manager=rm)
    return _orch_singleton


@router.post("/job", response_model=SubmitJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_job(
    payload: SubmitJobRequest, orch: HierarchicalJobOrchestrator = Depends(get_orchestrator)
) -> SubmitJobResponse:
    jr = await orch.submit_job(
        payload.request, depth=(payload.config.current_depth if payload.config else 0)
    )
    return SubmitJobResponse(job_id=jr.job_id, status=jr.status, depth=jr.depth)


@router.get("/job/{job_id}", response_model=StatusResponse)
async def get_job(
    job_id: str, orch: HierarchicalJobOrchestrator = Depends(get_orchestrator)
) -> StatusResponse:
    try:
        jr = await orch.get_status(job_id)
        tree = await orch.get_tree(job_id)
        return StatusResponse(job_id=jr.job_id, status=jr.status, depth=jr.depth, tree=tree)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")


@router.delete("/job/{job_id}", response_model=CancelResponse)
async def cancel_job(
    job_id: str, orch: HierarchicalJobOrchestrator = Depends(get_orchestrator)
) -> CancelResponse:
    canceled = await orch.cancel(job_id)
    return CancelResponse(job_id=job_id, canceled=canceled)


@router.get("/hierarchy", response_model=HierarchyResponse)
async def get_hierarchy(
    rm: HierarchicalResourceManager = Depends(get_rm),
    orch: HierarchicalJobOrchestrator = Depends(get_orchestrator),
) -> HierarchyResponse:
    usage = await rm.get_hierarchy_usage()
    # Convert pydantic models to dict for response model typing
    usage_dict = {d: u.model_dump() for d, u in usage.items()}
    active_jobs = len([1 for _, t in orch._tasks.items() if not t.done()])
    return HierarchyResponse(usage=usage_dict, active_jobs=active_jobs)


@router.get("/stats", response_model=StatsResponse)
async def get_stats(orch: HierarchicalJobOrchestrator = Depends(get_orchestrator)) -> StatsResponse:
    st = orch.stats()
    return StatsResponse(
        submitted=st.get("submitted", 0),
        completed=st.get("completed", 0),
        failed=st.get("failed", 0),
        canceled=st.get("canceled", 0),
    )


@router.post("/validate", response_model=ValidationResponse)
async def validate_config(payload: ValidationRequest) -> ValidationResponse:
    # Basic validation handled by pydantic validators; enforce depth limits here too
    try:
        cfg = payload.config
        if cfg.current_depth > cfg.max_depth:
            return ValidationResponse(valid=False, reason="current_depth exceeds max_depth")
        return ValidationResponse(valid=True)
    except Exception as e:  # pragma: no cover - defensive
        return ValidationResponse(valid=False, reason=str(e))
