import pytest

from orchestrator.core.hierarchical import HierarchicalJobOrchestrator


@pytest.mark.asyncio
async def test_5_level_depth_limit_enforced():
    orch = HierarchicalJobOrchestrator(max_depth=2)
    # Compose sub tasks to attempt deep recursion; with max_depth=2 should stop at depth 2
    req = """
    - Level1 A
    - Level1 B
    """
    root = await orch.submit_job(req, depth=0)
    await orch._tasks[root.job_id]
    tree = await orch.get_tree(root.job_id)

    # Ensure no node deeper than 2
    def collect_depths(node):
        depths = [node["depth"]]
        for c in node.get("children", []):
            depths.extend(collect_depths(c))
        return depths

    depths = collect_depths(tree)
    assert max(depths) <= 2
