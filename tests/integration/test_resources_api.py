from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from orchestrator.api.resources_api import router as resources_router
from orchestrator.core.hierarchical.resource_manager import DEFAULT_WORKERS_BY_DEPTH


@pytest.mark.asyncio
async def test_get_quotas_matches_defaults():
    app = FastAPI()
    app.include_router(resources_router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/resources/quotas")
        assert res.status_code == 200
        data = res.json()
        by_depth = {q["depth"]: q["max_workers"] for q in data["quotas"]}
        for d, maxw in DEFAULT_WORKERS_BY_DEPTH.items():
            assert by_depth.get(d) == maxw


@pytest.mark.asyncio
async def test_allocate_release_and_usage_flow():
    app = FastAPI()
    app.include_router(resources_router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Initial usage
        res0 = await client.get("/api/resources/usage")
        assert res0.status_code == 200
        usage0 = {u["depth"]: (u["allocated"], u["available"]) for u in res0.json()["usage"]}

        # Allocate some workers at depth 1
        res = await client.post(
            "/api/resources/allocate",
            json={"job_id": "job-xyz", "depth": 1, "worker_count": 3},
        )
        assert res.status_code == 201
        alloc = res.json()
        assert alloc["job_id"] == "job-xyz"
        assert alloc["depth"] == 1
        assert alloc["requested"] == 3
        assert 1 <= alloc["granted"] <= 3

        # Usage reflects allocation
        res2 = await client.get("/api/resources/usage")
        assert res2.status_code == 200
        usage = {u["depth"]: (u["allocated"], u["available"]) for u in res2.json()["usage"]}
        before_alloc, before_avail = usage0[1]
        after_alloc, after_avail = usage[1]
        assert after_alloc == before_alloc + alloc["granted"]
        assert after_avail == before_avail - alloc["granted"]

        # Release and verify usage resets
        rel = await client.post("/api/resources/release", json={"job_id": "job-xyz", "depth": 1})
        assert rel.status_code == 200
        assert rel.json()["released"] is True

        res3 = await client.get("/api/resources/usage")
        usage3 = {u["depth"]: (u["allocated"], u["available"]) for u in res3.json()["usage"]}
        assert usage3[1][0] == before_alloc


@pytest.mark.asyncio
async def test_allocation_conflict_when_full_then_release():
    app = FastAPI()
    app.include_router(resources_router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        depth = 2
        quota = DEFAULT_WORKERS_BY_DEPTH[depth]

        # Allocate up to quota across two jobs
        res1 = await client.post(
            "/api/resources/allocate",
            json={"job_id": "j1", "depth": depth, "worker_count": quota - 1},
        )
        assert res1.status_code == 201
        g1 = res1.json()["granted"]
        res2 = await client.post(
            "/api/resources/allocate",
            json={"job_id": "j2", "depth": depth, "worker_count": 2},
        )
        assert res2.status_code == 201
        g2 = res2.json()["granted"]
        assert g1 + g2 <= quota

        # When full, further allocation returns 409
        res3 = await client.post(
            "/api/resources/allocate",
            json={"job_id": "j3", "depth": depth, "worker_count": 1},
        )
        if g1 + g2 == quota:
            assert res3.status_code == 409
        else:
            # Not yet full, allocate remaining to reach full
            assert res3.status_code == 201
            remaining = quota - (g1 + g2 + res3.json()["granted"])
            if remaining > 0:
                res4 = await client.post(
                    "/api/resources/allocate",
                    json={"job_id": "j4", "depth": depth, "worker_count": remaining},
                )
                assert res4.status_code in (201, 409)

        # Release all jobs and ensure available resets to quota
        for jid in ("j1", "j2", "j3", "j4"):
            await client.post("/api/resources/release", json={"job_id": jid, "depth": depth})

        res_final = await client.get("/api/resources/usage")
        usage = {u["depth"]: (u["allocated"], u["available"]) for u in res_final.json()["usage"]}
        assert usage[depth][0] == 0
        assert usage[depth][1] == quota


@pytest.mark.asyncio
async def test_release_nonexistent_returns_false():
    app = FastAPI()
    app.include_router(resources_router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/resources/release", json={"job_id": "none", "depth": 0})
        assert res.status_code == 200
        assert res.json()["released"] is False


@pytest.mark.asyncio
async def test_usage_shape_and_values():
    app = FastAPI()
    app.include_router(resources_router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/resources/usage")
        assert res.status_code == 200
        data = res.json()
        assert "usage" in data
        assert isinstance(data["usage"], list)
        first = data["usage"][0]
        assert set(first.keys()) == {"depth", "allocated", "available"}
        assert first["allocated"] + first["available"] == DEFAULT_WORKERS_BY_DEPTH[first["depth"]]
