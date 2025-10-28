from __future__ import annotations

import asyncio
from typing import Any, Dict

import pytest
import respx
from httpx import Response

from orchestrator.recursive import (
    APIError,
    AuthenticationError,
    ClientValidationError,
    NetworkError,
    RecursiveOrchestratorClient,
)


VALID_KEY = "sk-orch-" + "x" * 32
BASE = "https://orch.test"


@pytest.mark.asyncio
async def test_submit_poll_results_happy_path():
    with respx.mock(base_url=BASE) as router:
        # Submit
        router.post("/api/v1/orchestrate").mock(
            return_value=Response(200, json={"job_id": "job-123"})
        )
        # Poll running -> completed
        router.get("/api/v1/jobs/job-123/status").mock(
            side_effect=[
                Response(
                    200,
                    json={
                        "job_id": "job-123",
                        "status": "running",
                        "progress": {"pct": 50},
                        "results": None,
                    },
                ),
                Response(
                    200,
                    json={
                        "job_id": "job-123",
                        "status": "completed",
                        "progress": {"pct": 100},
                        "results": {"ok": True},
                    },
                ),
            ]
        )
        # Results
        router.get("/api/v1/jobs/job-123/results").mock(
            return_value=Response(200, json={"status": "completed", "results": {"ok": True}})
        )

        async with RecursiveOrchestratorClient(BASE, VALID_KEY) as client:
            job_id = await client.submit_job(
                request="Implement feature ABC",
                max_workers=2,
                current_depth=0,
            )
            assert job_id == "job-123"

            updates = []
            async for status in client.poll_job(job_id, poll_interval=0.01):
                updates.append(status.status)
            assert updates[-1] == "completed"

            results = await client.get_results(job_id)
            assert results["status"] == "completed"


def test_sync_wrapper_roundtrip(monkeypatch):
    # Use the async client but run via asyncio to validate wrapper behavior
    async def scenario() -> Dict[str, Any]:
        with respx.mock(base_url=BASE) as router:
            router.post("/api/v1/orchestrate").mock(
                return_value=Response(200, json={"job_id": "job-xyz"})
            )
            router.get("/api/v1/jobs/job-xyz/status").mock(
                side_effect=[
                    Response(200, json={"job_id": "job-xyz", "status": "completed", "progress": {}, "results": {}}),
                ]
            )
            router.get("/api/v1/jobs/job-xyz/results").mock(
                return_value=Response(200, json={"ok": True})
            )
            async with RecursiveOrchestratorClient(BASE, VALID_KEY) as client:
                job_id = await client.submit_job("Do something useful", max_workers=1)
                async for _ in client.poll_job(job_id, poll_interval=0.01):
                    break
                return await client.get_results(job_id)

    results = asyncio.run(scenario())
    assert results["ok"] is True


@pytest.mark.asyncio
async def test_validation_errors_raised():
    with pytest.raises(ClientValidationError):
        RecursiveOrchestratorClient("invalid-url", VALID_KEY)

    with pytest.raises(ClientValidationError):
        RecursiveOrchestratorClient(BASE, "short")

    with pytest.raises(ClientValidationError):
        RecursiveOrchestratorClient(BASE, "sk-orch-too-short")

    async with RecursiveOrchestratorClient(BASE, VALID_KEY) as client:
        with pytest.raises(ClientValidationError):
            await client.submit_job("short", max_workers=1)

        with pytest.raises(ClientValidationError):
            await client.submit_job("Valid request body", max_workers=0)

        with pytest.raises(ClientValidationError):
            await client.submit_job("Valid request body", max_workers=11)

        with pytest.raises(ClientValidationError):
            await client.submit_job("Valid request body", current_depth=6)

        with pytest.raises(ClientValidationError):
            async for _ in client.poll_job("", poll_interval=0.01):
                pass


@pytest.mark.asyncio
async def test_authentication_error_401():
    with respx.mock(base_url=BASE) as router:
        router.post("/api/v1/orchestrate").mock(return_value=Response(401, json={"error": "nope"}))
        async with RecursiveOrchestratorClient(BASE, VALID_KEY) as client:
            with pytest.raises(AuthenticationError):
                await client.submit_job("A valid submission body", max_workers=1)


@pytest.mark.asyncio
async def test_retry_on_5xx_then_success():
    with respx.mock(base_url=BASE) as router:
        calls = {
            "count": 0
        }

        def handler(request):
            calls["count"] += 1
            if calls["count"] < 2:
                return Response(503, json={"error": "temporary"})
            return Response(200, json={"job_id": "job-r"})

        router.post("/api/v1/orchestrate").mock(side_effect=handler)

        async with RecursiveOrchestratorClient(BASE, VALID_KEY, max_retries=2) as client:
            job_id = await client.submit_job("This will succeed after retry", max_workers=1)
            assert job_id == "job-r"


@pytest.mark.asyncio
async def test_network_error_after_retries():
    with respx.mock(base_url=BASE) as router:
        # Any request errors out with 503, exceeding retries
        router.post("/api/v1/orchestrate").mock(
            return_value=Response(503, json={"error": "down"})
        )
        async with RecursiveOrchestratorClient(BASE, VALID_KEY, max_retries=1) as client:
            with pytest.raises(APIError):
                await client.submit_job("Will fail after retries", max_workers=1)


@pytest.mark.asyncio
async def test_performance_overhead_under_100ms():
    with respx.mock(base_url=BASE) as router:
        router.post("/api/v1/orchestrate").mock(
            return_value=Response(200, json={"job_id": "perf-1"})
        )
        async with RecursiveOrchestratorClient(BASE, VALID_KEY) as client:
            import time

            start = time.perf_counter()
            _ = await client.submit_job("Performance check request", max_workers=1)
            elapsed = (time.perf_counter() - start) * 1000.0
            assert elapsed < 100.0

