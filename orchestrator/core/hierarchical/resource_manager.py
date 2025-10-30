"""Hierarchical resource manager with depth - based quotas.

This module provides an async, thread - safe resource manager for hierarchical
orchestration. It enforces quotas per depth, tracks allocations by job, and
exposes usage metrics suitable for dashboards.

Design goals:
- Non - blocking, asyncio - friendly
- Atomic allocation and release
- Depth - scoped quotas with warning thresholds
- Leak detection and safe cleanup

Examples:
    >>> import asyncio
    >>> async def main():
    ...     rm = HierarchicalResourceManager()
    ...     alloc = await rm.allocate_resources(job_id="job - 1", depth=1, requested_workers=3)
    ...     assert alloc.granted == 3
    ...     await rm.release_resources(job_id="job - 1", depth=1)
    ...
    >>> asyncio.run(main())
"""

from __future__ import annotations

import asyncio
from typing import AsyncContextManager, Dict, Optional, Tuple

from pydantic import BaseModel, Field, model_validator

# Default allocation strategy (can be overridden via constructor)
DEFAULT_WORKERS_BY_DEPTH: Dict[int, int] = {
    0: 10,  # Root (CTO)
    1: 8,  # PM
    2: 5,  # Tech Lead
    3: 3,  # Engineer
    4: 2,  # Junior
    5: 1,  # Intern
}

WARN_80 = 0.8
WARN_90 = 0.9


class ResourceUsage(BaseModel):
    """Usage metrics for a single depth level.

    Attributes:
        depth: Hierarchy depth (0..5)
        used: Currently allocated workers
        quota: Maximum allowed concurrent workers
        warn_80: Whether 80% threshold reached
        warn_90: Whether 90% threshold reached
    """

    depth: int = Field(..., ge=0, le=10)
    used: int = Field(..., ge=0)
    quota: int = Field(..., ge=0)
    warn_80: bool = Field(default=False)
    warn_90: bool = Field(default=False)

    @model_validator(mode="after")
    def used_not_exceed_quota(self) -> "ResourceUsage":
        if self.used > self.quota:
            raise ValueError("used cannot exceed quota")
        return self


class QuotaStatus(BaseModel):
    """Quota status for a depth level."""

    depth: int
    available: int
    quota: int
    warnings: Tuple[bool, bool]  # (warn_80, warn_90)


class ResourceAllocation(BaseModel):
    """Allocation result for a job request."""

    job_id: str
    depth: int
    requested: int
    granted: int


class AllocationError(RuntimeError):
    """Typed error for allocation failures."""


class HierarchicalResourceManager:
    """Depth - scoped resource manager with atomic operations.

    The manager is safe for concurrent use by async tasks. Each allocation
    is recorded per job and depth, allowing precise release and leak checks.
    """

    def __init__(self, workers_by_depth: Optional[Dict[int, int]] = None) -> None:
        self._quotas: Dict[int, int] = dict((workers_by_depth or DEFAULT_WORKERS_BY_DEPTH))
        self._used: Dict[int, int] = {d: 0 for d in self._quotas}
        self._by_job_depth: Dict[Tuple[str, int], int] = {}
        self._lock = asyncio.Lock()

    # ---------------------------- Internal helpers ----------------------------
    def _quota_for(self, depth: int) -> int:
        return self._quotas.get(depth, 0)

    def _usage(self, depth: int) -> int:
        return self._used.get(depth, 0)

    # ------------------------------- Public API -------------------------------
    async def check_quota(self, depth: int) -> QuotaStatus:
        """Return current quota status for a depth.

        Args:
            depth: Depth level to query.

        Returns:
            QuotaStatus including availability and warning flags.
        """
        async with self._lock:
            quota = self._quota_for(depth)
            used = self._usage(depth)
            available = max(quota - used, 0)
            ratio = (used / quota) if quota else 1.0
            return QuotaStatus(
                depth=depth,
                available=available,
                quota=quota,
                warnings=(ratio >= WARN_80, ratio >= WARN_90),
            )

    async def allocate_resources(
        self, *, job_id: str, depth: int, requested_workers: int
    ) -> ResourceAllocation:
        """Atomically allocate workers at a depth for a job.

        Args:
            job_id: Job identifier requesting resources.
            depth: Hierarchy depth level.
            requested_workers: Desired number of workers (>=1).

        Returns:
            ResourceAllocation indicating the granted workers (may be less
            than requested if nearing quota).

        Raises:
            AllocationError: If no workers are available.
        """
        if requested_workers <= 0:
            raise AllocationError("requested_workers must be positive")
        if not job_id:
            raise AllocationError("job_id is required")

        async with self._lock:
            quota = self._quota_for(depth)
            used = self._usage(depth)
            if used >= quota:
                raise AllocationError("No capacity available at this depth")

            available = quota - used
            granted = min(requested_workers, available)
            self._used[depth] = used + granted
            self._by_job_depth[(job_id, depth)] = (
                self._by_job_depth.get((job_id, depth), 0) + granted
            )
            return ResourceAllocation(
                job_id=job_id, depth=depth, requested=requested_workers, granted=granted
            )

    async def release_resources(self, *, job_id: str, depth: int) -> bool:
        """Release all resources held by a job at a depth.

        Args:
            job_id: Job identifier.
            depth: Depth level.

        Returns:
            True if any resources were released.
        """
        async with self._lock:
            key = (job_id, depth)
            held = self._by_job_depth.get(key, 0)
            if held <= 0:
                return False
            self._by_job_depth.pop(key, None)
            self._used[depth] = max(self._used.get(depth, 0) - held, 0)
            return True

    async def get_hierarchy_usage(self) -> Dict[int, ResourceUsage]:
        """Return usage metrics for all known depths.

        Returns:
            Mapping of depth->ResourceUsage.
        """
        async with self._lock:
            result: Dict[int, ResourceUsage] = {}
            for depth in sorted(self._quotas):
                quota = self._quota_for(depth)
                used = self._usage(depth)
                ratio = (used / quota) if quota else 1.0
                result[depth] = ResourceUsage(
                    depth=depth,
                    used=used,
                    quota=quota,
                    warn_80=ratio >= WARN_80,
                    warn_90=ratio >= WARN_90,
                )
            return result

    async def cleanup_job(self, job_id: str) -> int:
        """Release all resources for a job across all depths.

        Args:
            job_id: Job identifier to clean up.

        Returns:
            Total workers released.
        """
        async with self._lock:
            released = 0
            to_delete = [k for k in self._by_job_depth if k[0] == job_id]
            for key in to_delete:
                count = self._by_job_depth.pop(key, 0)
                depth = key[1]
                self._used[depth] = max(self._used.get(depth, 0) - count, 0)
                released += count
            return released

    # ----------------------------- Context manager ----------------------------
    async def resource_scope(
        self, *, job_id: str, depth: int, requested_workers: int
    ) -> AsyncContextManager[ResourceAllocation]:
        """Async context manager allocating and releasing resources.

        Usage:
            async with rm.resource_scope(job_id=jid, depth=1, requested_workers=2):
                ...
        """

        class _Scope:
            def __init__(self, outer: "HierarchicalResourceManager") -> None:
                self._outer = outer
                self._job_id = job_id
                self._depth = depth
                self.allocated = 0

            async def __aenter__(self) -> ResourceAllocation:
                alloc = await self._outer.allocate_resources(
                    job_id=self._job_id, depth=self._depth, requested_workers=requested_workers
                )
                self.allocated = alloc.granted
                return alloc

            async def __aexit__(
                self,
                exc_type: Optional[type[BaseException]],
                exc: Optional[BaseException],
                tb: Optional[object],
            ) -> None:
                await self._outer.release_resources(job_id=self._job_id, depth=self._depth)

        return _Scope(self)
