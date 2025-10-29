"""Unit tests for HierarchicalResourceManager.

Tests edge cases, error handling, and validation logic not covered by integration tests.
"""

import asyncio

import pytest

from orchestrator.core.hierarchical.resource_manager import (
    AllocationError,
    HierarchicalResourceManager,
    QuotaStatus,
    ResourceUsage,
)


class TestResourceUsageValidation:
    """Test ResourceUsage model validation."""

    def test_used_exceeds_quota_raises_error(self):
        """Test that used > quota raises ValidationError."""
        with pytest.raises(ValueError, match="used cannot exceed quota"):
            ResourceUsage(depth=0, quota=10, used=15)

    def test_used_equals_quota_is_valid(self):
        """Test that used == quota is valid."""
        usage = ResourceUsage(depth=0, quota=10, used=10)
        assert usage.used == 10
        assert usage.quota == 10

    def test_used_less_than_quota_is_valid(self):
        """Test that used < quota is valid."""
        usage = ResourceUsage(depth=0, quota=10, used=5)
        assert usage.used == 5
        assert usage.quota == 10


class TestHierarchicalResourceManager:
    """Test HierarchicalResourceManager edge cases."""

    @pytest.mark.asyncio
    async def test_allocate_resources_at_max_depth(self):
        """Test resource allocation at maximum depth (5)."""
        rm = HierarchicalResourceManager()

        # Allocate at max depth
        allocation = await rm.allocate_resources(
            job_id="test-max-depth", depth=5, requested_workers=1
        )

        assert allocation.job_id == "test-max-depth"
        assert allocation.depth == 5
        assert allocation.granted >= 0
        assert allocation.granted <= 1  # Max quota at depth 5

    @pytest.mark.asyncio
    async def test_allocate_resources_exceeds_quota(self):
        """Test allocation request that exceeds available quota."""
        rm = HierarchicalResourceManager()

        # Request more than quota at depth 5 (quota = 1)
        allocation = await rm.allocate_resources(
            job_id="test-exceed-quota", depth=5, requested_workers=10
        )

        # Should grant only what's available
        assert allocation.granted <= 1
        assert allocation.requested == 10

    @pytest.mark.asyncio
    async def test_release_nonexistent_job(self):
        """Test releasing resources for non-existent job."""
        rm = HierarchicalResourceManager()

        # Release for job that was never allocated
        released = await rm.release_resources(job_id="nonexistent-job", depth=0)

        # Should return False (nothing to release)
        assert released is False

    @pytest.mark.asyncio
    async def test_get_hierarchy_usage_all_depths(self):
        """Test getting usage for all hierarchy depths."""
        rm = HierarchicalResourceManager()

        usage = await rm.get_hierarchy_usage()

        # Should have entries for depths 0-5
        assert len(usage) == 6
        for depth in range(6):
            assert depth in usage
            assert usage[depth].quota > 0
            assert usage[depth].used >= 0

    @pytest.mark.asyncio
    async def test_allocate_zero_workers(self):
        """Test allocation with zero workers raises AllocationError."""
        rm = HierarchicalResourceManager()

        with pytest.raises(AllocationError, match="requested_workers must be positive"):
            await rm.allocate_resources(job_id="test-zero-workers", depth=0, requested_workers=0)

    @pytest.mark.asyncio
    async def test_multiple_allocations_same_depth(self):
        """Test multiple allocations at the same depth level."""
        rm = HierarchicalResourceManager()

        # First allocation
        alloc1 = await rm.allocate_resources(job_id="job-1", depth=0, requested_workers=3)

        # Second allocation
        alloc2 = await rm.allocate_resources(job_id="job-2", depth=0, requested_workers=3)

        # Total granted should not exceed quota
        usage = await rm.get_hierarchy_usage()
        depth_0_usage = usage[0]
        assert depth_0_usage.used <= depth_0_usage.quota

    @pytest.mark.asyncio
    async def test_allocate_release_cycle(self):
        """Test full allocate-release cycle."""
        rm = HierarchicalResourceManager()

        # Get initial usage
        initial_usage = await rm.get_hierarchy_usage()
        initial_used = initial_usage[0].used

        # Allocate resources
        await rm.allocate_resources(job_id="test-cycle", depth=0, requested_workers=2)

        # Check usage increased
        after_alloc = await rm.get_hierarchy_usage()
        assert after_alloc[0].used >= initial_used

        # Release resources
        released = await rm.release_resources(job_id="test-cycle", depth=0)

        assert released is True

        # Check usage decreased back
        after_release = await rm.get_hierarchy_usage()
        assert after_release[0].used <= after_alloc[0].used


class TestQuotaStatus:
    """Test QuotaStatus model."""

    def test_quota_status_creation(self):
        """Test creating QuotaStatus with warnings."""
        status = QuotaStatus(
            depth=0, available=2, quota=10, warnings=(True, False)  # 80% warning active
        )

        assert status.depth == 0
        assert status.available == 2
        assert status.quota == 10
        assert status.warnings == (True, False)

    def test_quota_status_both_warnings(self):
        """Test QuotaStatus with both warnings active."""
        status = QuotaStatus(depth=1, available=0, quota=8, warnings=(True, True))  # Both warnings

        assert status.warnings[0] is True  # 80% warning
        assert status.warnings[1] is True  # 90% warning


class TestResourceManagerAdvanced:
    """Test advanced resource manager functionality."""

    @pytest.mark.asyncio
    async def test_allocate_empty_job_id(self):
        """Test allocation with empty job_id raises AllocationError."""
        rm = HierarchicalResourceManager()

        with pytest.raises(AllocationError, match="job_id is required"):
            await rm.allocate_resources(job_id="", depth=0, requested_workers=1)

    @pytest.mark.asyncio
    async def test_allocate_no_capacity(self):
        """Test allocation when quota is fully used."""
        rm = HierarchicalResourceManager()

        # Exhaust all quota at depth 5 (quota=1)
        await rm.allocate_resources(job_id="job-1", depth=5, requested_workers=1)

        # Try to allocate more - should fail
        with pytest.raises(AllocationError, match="No capacity available"):
            await rm.allocate_resources(job_id="job-2", depth=5, requested_workers=1)

    @pytest.mark.asyncio
    async def test_cleanup_job_multiple_depths(self):
        """Test cleanup_job releases resources across all depths."""
        rm = HierarchicalResourceManager()

        job_id = "multi-depth-job"

        # Allocate at multiple depths
        await rm.allocate_resources(job_id=job_id, depth=0, requested_workers=2)
        await rm.allocate_resources(job_id=job_id, depth=1, requested_workers=1)
        await rm.allocate_resources(job_id=job_id, depth=2, requested_workers=1)

        # Cleanup should release all
        released = await rm.cleanup_job(job_id)
        assert released == 4  # 2 + 1 + 1

        # Verify all resources released
        usage = await rm.get_hierarchy_usage()
        assert usage[0].used == 0
        assert usage[1].used == 0
        assert usage[2].used == 0

    @pytest.mark.asyncio
    async def test_resource_scope_context_manager(self):
        """Test resource_scope async context manager."""
        rm = HierarchicalResourceManager()

        initial_usage = await rm.get_hierarchy_usage()
        initial_used = initial_usage[0].used

        # Use context manager
        async with await rm.resource_scope(job_id="ctx-job", depth=0, requested_workers=3) as alloc:
            assert alloc.granted == 3
            assert alloc.job_id == "ctx-job"

            # Check resources are allocated
            mid_usage = await rm.get_hierarchy_usage()
            assert mid_usage[0].used == initial_used + 3

        # After context, resources should be released
        final_usage = await rm.get_hierarchy_usage()
        assert final_usage[0].used == initial_used

    @pytest.mark.asyncio
    async def test_check_quota_warnings(self):
        """Test check_quota returns correct warning flags."""
        rm = HierarchicalResourceManager()

        # Allocate 8 workers at depth 0 (quota=10)
        await rm.allocate_resources(job_id="warn-job", depth=0, requested_workers=8)

        status = await rm.check_quota(depth=0)
        assert status.depth == 0
        assert status.quota == 10
        assert status.available == 2
        assert status.warnings[0] is True  # 80% threshold reached
        assert status.warnings[1] is False  # 90% not reached yet

        # Allocate 1 more to reach 90%
        await rm.allocate_resources(job_id="warn-job-2", depth=0, requested_workers=1)

        status2 = await rm.check_quota(depth=0)
        assert status2.warnings[0] is True  # 80% still true
        assert status2.warnings[1] is True  # 90% now reached


# Legacy tests from original file (kept for backward compatibility)


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
            async with await rm.resource_scope(job_id=jid, depth=0, requested_workers=1):
                await asyncio.sleep(0.01)
        except AllocationError:
            # Expected when quota is full
            pass

    await asyncio.gather(*(worker(f"w{i}") for i in range(6)))
    usage = await rm.get_hierarchy_usage()
    assert usage[0].used == 0
