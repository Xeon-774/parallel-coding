from __future__ import annotations

import asyncio

import pytest
import respx
from httpx import Response

from orchestrator.recursive import RecursiveOrchestratorClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_2_level_recursion_success():
    """Simulate a 2-level recursive orchestration end-to-end via mocked API.

    Hierarchy:
        Root Orchestrator (Depth 0)
            ├─ Worker 1: Submit sub-orchestration
            │   └─ Sub-Orchestrator (Depth 1)
            │       ├─ Worker 1.1: Task A
            │       └─ Worker 1.2: Task B
            └─ Worker 2: Direct task
    """

    base = "https://orch.itest"
    api_key = "sk-orch-" + "y" * 32

    with respx.mock(base_url=base) as router:
        # Root submission -> job root-1
        router.post("/api/v1/orchestrate").mock(
            return_value=Response(200, json={"job_id": "root-1"})
        )

        # Root polling: running -> completed
        router.get("/api/v1/jobs/root-1/status").mock(
            side_effect=[
                Response(
                    200,
                    json={
                        "job_id": "root-1",
                        "status": "running",
                        "progress": {"pct": 50},
                        "results": None,
                    },
                ),
                Response(
                    200,
                    json={
                        "job_id": "root-1",
                        "status": "completed",
                        "progress": {"pct": 100},
                        "results": {
                            "tasks": [
                                {
                                    "name": "sub-orchestrator",
                                    "success": True,
                                    "output": "Sub-orchestrator handled Task A and B",
                                },
                                {
                                    "name": "direct-task",
                                    "success": True,
                                    "output": "API endpoints implemented",
                                },
                            ]
                        },
                    },
                ),
            ]
        )

        # Root results
        router.get("/api/v1/jobs/root-1/results").mock(
            return_value=Response(
                200,
                json={
                    "status": "completed",
                    "results": {
                        "tasks": [
                            {
                                "name": "sub-orchestrator",
                                "success": True,
                                "output": "Sub-orchestrator handled Task A and B",
                            },
                            {
                                "name": "direct-task",
                                "success": True,
                                "output": "API endpoints implemented",
                            },
                        ]
                    },
                },
            )
        )

        async with RecursiveOrchestratorClient(base, api_key) as client:
            root_job_id = await client.submit_job(
                request=(
                    "Task: Create authentication module\n"
                    "Sub-tasks:\n1. Database models (delegate to sub-orchestrator)\n"
                    "2. API endpoints (direct task)\n"
                ),
                max_workers=2,
                current_depth=0,
            )
            assert root_job_id == "root-1"

            results = None
            async for status in client.poll_job(root_job_id, poll_interval=0.01):
                if status.status == "completed":
                    results = await client.get_results(root_job_id)
                    break

    assert results is not None
    assert results["status"] == "completed"
    assert len(results["results"]["tasks"]) == 2

    sub_task = next(
        t for t in results["results"]["tasks"] if "sub-orchestrator" in t["name"].lower()
    )
    assert sub_task["success"] is True

