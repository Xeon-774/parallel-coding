"""Hierarchical job orchestrator.

Coordinates recursive job execution across depth levels using a
HierarchicalResourceManager. This implementation uses in - memory tracking and
simulated worker tasks suitable for unit and integration tests.

It is designed for extensibility and safe recursion limits, leveraging the
existing RecursionValidator for safety checks.

Extended features:
- Document review delegation to AI providers (Codex, Claude Code, etc.)
- Multi - perspective parallel review support
- Review result aggregation
"""

from __future__ import annotations

import asyncio
import itertools
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from orchestrator.core.ai_providers.base_review_provider import (
    AggregatedReview,
    BaseReviewProvider,
    ReviewPerspective,
    ReviewRequest,
    ReviewResult,
)
from orchestrator.core.hierarchical.resource_manager import (
    HierarchicalResourceManager,
)
from orchestrator.recursive.recursion_validator import RecursionValidator


class OrchestratorError(RuntimeError):
    """Base orchestrator error."""


class DepthLimitError(OrchestratorError):
    """Raised when a submission exceeds depth limits."""


class RetryDecision(BaseModel):
    """Decision on whether to retry a failed sub - job."""

    should_retry: bool
    delay_seconds: float = 0.0
    max_retries: int = 0


class JobResult(BaseModel):
    """Result / status of a single job."""

    job_id: str
    depth: int
    status: str  # pending|running|completed|failed|canceled
    started_at: float
    finished_at: Optional[float] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    children: List[str] = Field(default_factory=list)


class AggregatedResult(BaseModel):
    """Aggregate result of a parent job combining sub - jobs."""

    job_id: str
    success: bool
    results: Dict[str, Any]


def _now() -> float:
    return time.time()


def _new_job_id() -> str:
    return uuid.uuid4().hex


class HierarchicalJobOrchestrator:
    """In - memory hierarchical job orchestrator.

    Responsibilities:
    - Validate recursion via RecursionValidator
    - Allocate / release resources by depth
    - Split a request into sub - tasks and schedule them
    - Track job graph and aggregate results
    - Provide status queries for APIs
    """

    def __init__(
        self,
        resource_manager: Optional[HierarchicalResourceManager] = None,
        *,
        max_depth: int = 5,
    ) -> None:
        self._rm = resource_manager or HierarchicalResourceManager()
        self._jobs: Dict[str, JobResult] = {}
        self._parents: Dict[str, Optional[str]] = {}
        self._children: Dict[str, List[str]] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._max_depth = max_depth
        self._metrics = {
            "submitted": 0,
            "completed": 0,
            "failed": 0,
            "canceled": 0,
        }
        # Review provider registry
        self._review_providers: Dict[str, BaseReviewProvider] = {}
        self._default_review_provider: Optional[str] = None

    # --------------------------------- Metrics --------------------------------
    def stats(self) -> Dict[str, Any]:
        return dict(self._metrics)

    # -------------------------------- Lifecycle --------------------------------
    async def submit_job(self, request: str, depth: int = 0) -> JobResult:
        """Submit a job at a depth.

        Splits the request into sub - tasks if possible and schedules
        asynchronous execution. Returns initial JobResult.
        """
        if not (0 <= depth <= self._max_depth):
            raise DepthLimitError("Depth out of bounds")

        jid = _new_job_id()
        jr = JobResult(job_id=jid, depth=depth, status="pending", started_at=_now())
        async with self._lock:
            self._jobs[jid] = jr
            self._parents[jid] = None
            self._children[jid] = []
            self._metrics["submitted"] += 1

        task = asyncio.create_task(self._run_job(jid, request))
        async with self._lock:
            self._tasks[jid] = task
        return jr

    async def spawn_sub_orchestrator(self, subtask: str, parent_depth: int) -> JobResult:
        """Spawn a sub - job one level deeper than parent."""
        depth = parent_depth + 1
        if depth > self._max_depth:
            raise DepthLimitError("Max depth reached")
        return await self.submit_job(subtask, depth=depth)

    async def _run_job(self, job_id: str, request: str) -> None:
        try:
            async with self._lock:
                jr = self._jobs[job_id]
                jr.status = "running"

            # Determine sub - tasks and concurrency by validation
            sub_tasks = self._decompose_request(request)
            val = RecursionValidator.validate_depth(
                current_depth=jr.depth,
                max_depth=self._max_depth,
                workers_by_depth={i: self._rm._quotas.get(i, 1) for i in range(0, 10)},
            )

            if not sub_tasks or not val.is_valid:
                # Leaf task or cannot go deeper: simulate unit of work
                await self._execute_leaf(job_id, request)
            else:
                # Parallelize sub - tasks with limited workers at next depth
                await self._execute_composed(job_id, jr.depth, sub_tasks, val.max_workers or 1)

            async with self._lock:
                jr = self._jobs[job_id]
                if jr.status not in ("failed", "canceled"):
                    jr.status = "completed"
                    jr.finished_at = _now()
                    self._metrics["completed"] += 1
        except asyncio.CancelledError:
            async with self._lock:
                jr = self._jobs[job_id]
                jr.status = "canceled"
                jr.finished_at = _now()
                self._metrics["canceled"] += 1
            raise
        except Exception as e:  # pylint: disable=broad - except
            async with self._lock:
                jr = self._jobs[job_id]
                jr.status = "failed"
                jr.error = str(e)
                jr.finished_at = _now()
                self._metrics["failed"] += 1
        finally:
            # Ensure resources are released if held
            await self._rm.cleanup_job(job_id)

    async def _execute_leaf(self, job_id: str, request: str) -> None:
        # Simulate unit of work with minimal delay proportional to size
        delay = min(max(len(request.strip()) / 200.0, 0.01), 0.05)
        async with await self._rm.resource_scope(
            job_id=job_id, depth=max(0, self._jobs[job_id].depth), requested_workers=1
        ):
            await asyncio.sleep(delay)
        async with self._lock:
            jr = self._jobs[job_id]
            jr.output = {"summary": request[:100]}

    async def _execute_composed(
        self, job_id: str, parent_depth: int, sub_tasks: List[str], max_workers: int
    ) -> None:
        # Limit parallelism using a semaphore and allocate resources accordingly
        sem = asyncio.Semaphore(max_workers)

        results: List[Tuple[str, Optional[str]]] = []

        async def run_task(st: str) -> None:
            await sem.acquire()
            try:
                child = await self.spawn_sub_orchestrator(st, parent_depth)
                async with self._lock:
                    self._parents[child.job_id] = job_id
                    self._children[job_id].append(child.job_id)
                # Wait for child completion
                await self._tasks[child.job_id]
                async with self._lock:
                    cres = self._jobs[child.job_id]
                    results.append((child.job_id, cres.error))
            finally:
                sem.release()

        await asyncio.gather(*(run_task(st) for st in sub_tasks))
        # Aggregate child summaries
        async with self._lock:
            jr = self._jobs[job_id]
            jr.output = {
                "children": [cid for cid, _ in results],
                "errors": [e for _, e in results if e],
            }

    def _decompose_request(self, request: str) -> List[str]:
        # Very simple splitter: look for lines starting with '-' or numbered list
        lines = [ln.strip() for ln in request.splitlines() if ln.strip()]
        subs: List[str] = []
        for ln in lines:
            if ln.startswith("-") or ln[:2].isdigit() or ln.lower().startswith("task"):
                subs.append(ln.lstrip("-0123456789. "))
        return subs

    # --------------------------------- Queries ---------------------------------
    async def get_status(self, job_id: str) -> JobResult:
        async with self._lock:
            return self._jobs[job_id]

    async def get_tree(self, job_id: str) -> Dict[str, Any]:
        async with self._lock:

            def build(node: str) -> Dict[str, Any]:
                jr = self._jobs[node]
                return {
                    "job_id": node,
                    "depth": jr.depth,
                    "status": jr.status,
                    "children": [build(c) for c in self._children.get(node, [])],
                }

            return build(job_id)

    async def cancel(self, job_id: str) -> bool:
        async with self._lock:
            task = self._tasks.get(job_id)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            return True
        return False

    async def aggregate_results(self, sub_jobs: List[JobResult]) -> AggregatedResult:
        success = all(j.status == "completed" for j in sub_jobs)
        results: Dict[str, Any] = {}
        for j in sub_jobs:
            results[j.job_id] = j.output or {"error": j.error}
        parent = sub_jobs[0].job_id if sub_jobs else ""
        return AggregatedResult(job_id=parent, success=success, results=results)

    async def handle_sub_job_failure(self, job_id: str, error: Exception) -> RetryDecision:
        # Simple policy: retry up to 2 times with exponential backoff based on depth
        depth = (await self.get_status(job_id)).depth
        backoff = 0.05 * (2**depth)
        return RetryDecision(should_retry=True, delay_seconds=backoff, max_retries=2)

    # ----------------------------- Review Functions -----------------------------
    def register_review_provider(
        self, provider: BaseReviewProvider, set_as_default: bool = False
    ) -> None:
        """
        Register a review provider.

        Args:
            provider: Review provider to register
            set_as_default: Whether to set as default provider

        Example:
            >>> orchestrator = HierarchicalJobOrchestrator()
            >>> codex_provider = CodexReviewProvider(executor)
            >>> orchestrator.register_review_provider(codex_provider, set_as_default=True)
        """
        self._review_providers[provider.provider_name] = provider
        if set_as_default or not self._default_review_provider:
            self._default_review_provider = provider.provider_name

    def get_available_review_providers(self) -> List[str]:
        """
        Get list of available review providers.

        Returns:
            List of provider names

        Example:
            >>> providers = orchestrator.get_available_review_providers()
            >>> print(providers)
            ['codex', 'claude_code']
        """
        return [
            name for name, provider in self._review_providers.items() if provider.is_available()
        ]

    async def review_document(self, request: ReviewRequest, provider: str = "auto") -> ReviewResult:
        """
        Execute document review using specified or auto - selected provider.

        Args:
            request: Review request with document path and parameters
            provider: Provider to use ("auto"|"codex"|"claude_code"|etc.)

        Returns:
            ReviewResult with feedback and scores

        Raises:
            ValueError: If provider not found or no providers available
            RuntimeError: If review execution fails

        Example:
            >>> request = ReviewRequest(
            ...     document_path="docs / ROADMAP.md",
            ...     review_type=ReviewType.ROADMAP,
            ...     perspective=ReviewPerspective.FEASIBILITY
            ... )
            >>> result = await orchestrator.review_document(request, provider="codex")
            >>> print(f"Score: {result.overall_score}")
        """
        # Auto - select provider
        if provider == "auto":
            provider = self._select_best_provider()

        # Get provider
        selected_provider = self._review_providers.get(provider)
        if not selected_provider:
            raise ValueError(
                f"Review provider not found: {provider}. "
                f"Available: {list(self._review_providers.keys())}"
            )

        if not selected_provider.is_available():
            raise ValueError(f"Review provider not available: {provider}")

        # Execute review
        return await selected_provider.review_document(request)

    async def parallel_review(
        self,
        document_path: str,
        review_type: str,
        perspectives: List[ReviewPerspective],
        provider: str = "auto",
    ) -> AggregatedReview:
        """
        Execute parallel reviews from multiple perspectives.

        Args:
            document_path: Path to document to review
            review_type: Type of review (design, roadmap, etc.)
            perspectives: List of perspectives to review from
            provider: Provider to use for all reviews

        Returns:
            AggregatedReview with combined results

        Example:
            >>> from orchestrator.core.ai_providers.base_review_provider import ReviewType, ReviewPerspective
            >>> result = await orchestrator.parallel_review(
            ...     document_path="docs / DESIGN.md",
            ...     review_type=ReviewType.DESIGN,
            ...     perspectives=[
            ...         ReviewPerspective.ARCHITECTURE,
            ...         ReviewPerspective.SECURITY,
            ...         ReviewPerspective.PERFORMANCE
            ...     ]
            ... )
            >>> print(f"Overall score: {result.overall_score}")
            >>> print(f"Critical issues: {result.critical_count}")
        """
        # Create review requests
        tasks = []
        for perspective in perspectives:
            request = ReviewRequest(
                document_path=document_path,
                review_type=review_type,
                perspective=perspective,
            )
            tasks.append(self.review_document(request, provider=provider))

        # Execute in parallel
        results = await asyncio.gather(*tasks)

        # Aggregate results
        return self._aggregate_review_results(document_path, review_type, results)

    def _select_best_provider(self) -> str:
        """
        Select best available review provider.

        Priority order:
        1. Default provider (if set and available)
        2. First available provider in registry

        Returns:
            Provider name

        Raises:
            ValueError: If no providers available
        """
        # Try default provider first
        if self._default_review_provider:
            provider = self._review_providers.get(self._default_review_provider)
            if provider and provider.is_available():
                return self._default_review_provider

        # Try any available provider
        for name, provider in self._review_providers.items():
            if provider.is_available():
                return name

        raise ValueError("No review providers available")

    def _aggregate_review_results(
        self, document_path: str, review_type: str, results: List[ReviewResult]
    ) -> AggregatedReview:
        """
        Aggregate multiple review results.

        Args:
            document_path: Document path
            review_type: Review type
            results: List of review results

        Returns:
            AggregatedReview with combined metrics
        """
        if not results:
            raise ValueError("No review results to aggregate")

        # Calculate metrics
        perspectives = [r.perspective for r in results]
        overall_score = sum(r.overall_score for r in results) / len(results)
        critical_count = sum(len(r.critical_issues) for r in results)
        warning_count = sum(len(r.warnings) for r in results)
        execution_time = sum(r.execution_time_seconds for r in results)

        return AggregatedReview(
            document_path=document_path,
            review_type=review_type,
            perspectives=perspectives,
            results=results,
            overall_score=overall_score,
            critical_count=critical_count,
            warning_count=warning_count,
            execution_time_seconds=execution_time,
        )
