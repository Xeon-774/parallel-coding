"""Resource Manager API endpoints.

Implements depth-based quotas, allocation, release, and usage endpoints
backed by the in-memory HierarchicalResourceManager. Designed for FastAPI.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from orchestrator.core.hierarchical import HierarchicalResourceManager
from orchestrator.api.dependencies import TokenData, require_scope


router = APIRouter(prefix="/api/resources", tags=["resources"])


_rm_singleton: Optional[HierarchicalResourceManager] = None


def get_rm() -> HierarchicalResourceManager:
    """Return a process-wide resource manager singleton.

    Keeping a singleton aligns usage across requests and tests.
    """
    global _rm_singleton
    if _rm_singleton is None:
        _rm_singleton = HierarchicalResourceManager()
    return _rm_singleton


class QuotaItem(BaseModel):
    depth: int = Field(..., ge=0, le=10)
    max_workers: int = Field(..., ge=0)


class QuotasResponse(BaseModel):
    quotas: List[QuotaItem]


@router.get(
    "/quotas",
    response_model=QuotasResponse,
    summary="Get resource quotas",
    description="""
    Retrieve resource quotas configured for each hierarchy depth level.

    **Hierarchical Resource Model:**
    - Depth 0 (root): Maximum workers available
    - Depth 1-5: Decreasing quotas for nested jobs

    **Default Configuration:**
    ```
    Depth 0: 10 workers
    Depth 1: 8 workers
    Depth 2: 5 workers
    Depth 3: 3 workers
    Depth 4: 2 workers
    Depth 5: 1 worker
    ```

    **Required Scope:** `resources:read`

    **Example Response:**
    ```json
    {
      "quotas": [
        {"depth": 0, "max_workers": 10},
        {"depth": 1, "max_workers": 8},
        {"depth": 2, "max_workers": 5}
      ]
    }
    ```
    """,
    response_description="Resource quotas by depth level",
)
async def get_quotas(
    rm: HierarchicalResourceManager = Depends(get_rm),
    user: TokenData = Depends(require_scope("resources:read")),
) -> QuotasResponse:
    """Get configured quotas by depth level."""
    usage = await rm.get_hierarchy_usage()
    items: List[QuotaItem] = [
        QuotaItem(depth=d, max_workers=u.quota) for d, u in sorted(usage.items())
    ]
    return QuotasResponse(quotas=items)


class AllocateRequest(BaseModel):
    job_id: str = Field(..., min_length=1)
    depth: int = Field(..., ge=0, le=10)
    worker_count: int = Field(..., ge=1, description="Requested number of workers")


class AllocationResponse(BaseModel):
    job_id: str
    depth: int
    requested: int
    granted: int


@router.post("/allocate", response_model=AllocationResponse, status_code=status.HTTP_201_CREATED)
async def allocate_resources(
    payload: AllocateRequest,
    rm: HierarchicalResourceManager = Depends(get_rm),
    user: TokenData = Depends(require_scope("resources:write")),
) -> AllocationResponse:
    """Allocate resources for a job at a specific depth."""
    try:
        alloc = await rm.allocate_resources(
            job_id=payload.job_id, depth=payload.depth, requested_workers=payload.worker_count
        )
    except Exception as exc:
        # Map allocation failures to a conflict error without internal details
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return AllocationResponse(
        job_id=alloc.job_id, depth=alloc.depth, requested=alloc.requested, granted=alloc.granted
    )


class ReleaseRequest(BaseModel):
    job_id: str = Field(..., min_length=1)
    depth: int = Field(..., ge=0, le=10)


class ReleaseResponse(BaseModel):
    job_id: str
    depth: int
    released: bool


@router.post("/release", response_model=ReleaseResponse)
async def release_resources(
    payload: ReleaseRequest,
    rm: HierarchicalResourceManager = Depends(get_rm),
    user: TokenData = Depends(require_scope("resources:write")),
) -> ReleaseResponse:
    """Release any resources held by a job at a depth."""
    released = await rm.release_resources(job_id=payload.job_id, depth=payload.depth)
    return ReleaseResponse(job_id=payload.job_id, depth=payload.depth, released=released)


class UsageItem(BaseModel):
    depth: int
    allocated: int
    available: int


class UsageResponse(BaseModel):
    usage: List[UsageItem]


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    rm: HierarchicalResourceManager = Depends(get_rm),
    user: TokenData = Depends(require_scope("resources:read")),
) -> UsageResponse:
    """Get current resource usage by depth (allocated and available)."""
    usage = await rm.get_hierarchy_usage()
    items: List[UsageItem] = []
    for depth, u in sorted(usage.items()):
        items.append(UsageItem(depth=depth, allocated=u.used, available=max(u.quota - u.used, 0)))
    return UsageResponse(usage=items)

