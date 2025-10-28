import asyncio
import pytest

from orchestrator.core.hierarchical.resource_manager import (
    HierarchicalResourceManager,
    AllocationError,
)


@pytest.mark.asyncio
async def test_allocate_and_release_happy_path():
    rm = HierarchicalResourceManager({0: 2})
    a1 = await rm.allocate_resources(job_id="j1", depth=0, requested_workers=1)
    assert a1.granted == 1
    a2 = await rm.allocate_resources(job_id="j2", depth=0, requested_workers=2)
    assert a2.granted == 1  # only one left
    status = await rm.check_quota(0)
    assert status.available == 0
    released = await rm.release_resources(job_id="j1", depth=0)
    assert released is True
    status2 = await rm.check_quota(0)
    assert status2.available == 1


@pytest.mark.asyncio
async def test_allocation_error_when_full():
    rm = HierarchicalResourceManager({0: 1})
    await rm.allocate_resources(job_id="j1", depth=0, requested_workers=1)
    with pytest.raises(AllocationError):
        await rm.allocate_resources(job_id="j2", depth=0, requested_workers=1)


@pytest.mark.asyncio
async def test_cleanup_job_releases_all_depths():
    rm = HierarchicalResourceManager({0: 2, 1: 2})
    await rm.allocate_resources(job_id="job", depth=0, requested_workers=2)
    await rm.allocate_resources(job_id="job", depth=1, requested_workers=1)
    usage = await rm.get_hierarchy_usage()
    assert usage[0].used == 2 and usage[1].used == 1
    released = await rm.cleanup_job("job")
    assert released == 3
    usage2 = await rm.get_hierarchy_usage()
    assert usage2[0].used == 0 and usage2[1].used == 0


@pytest.mark.asyncio
async def test_concurrent_allocations_safely_enforced():
    rm = HierarchicalResourceManager({0: 3})

    async def worker(jid):
        try:
            async with (await rm.resource_scope(job_id=jid, depth=0, requested_workers=1)):
                await asyncio.sleep(0.01)
        except AllocationError:
            # Expected when quota is full
            pass

    await asyncio.gather(*(worker(f"w{i}") for i in range(6)))
    usage = await rm.get_hierarchy_usage()
    assert usage[0].used == 0

