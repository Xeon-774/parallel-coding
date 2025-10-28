import pytest

from orchestrator.core.hierarchical import HierarchicalJobOrchestrator


@pytest.mark.asyncio
async def test_3_level_recursion():
    orch = HierarchicalJobOrchestrator()
    req = """
    Task: Implement feature
    - Design
    - Build
    - Test
    """
    root = await orch.submit_job(req, depth=0)
    await orch._tasks[root.job_id]
    tree = await orch.get_tree(root.job_id)
    # Depth 0 root, depth 1 children; leaf children may create no further depth
    assert tree["depth"] == 0
    assert all(ch["depth"] == 1 for ch in tree["children"])

