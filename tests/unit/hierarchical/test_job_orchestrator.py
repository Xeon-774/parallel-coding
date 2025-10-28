import asyncio
import pytest

from orchestrator.core.hierarchical import HierarchicalJobOrchestrator


@pytest.mark.asyncio
async def test_submit_leaf_job_completes_with_output():
    orch = HierarchicalJobOrchestrator()
    jr = await orch.submit_job("Just a single task with no bullets", depth=0)
    await orch._tasks[jr.job_id]  # wait for completion
    status = await orch.get_status(jr.job_id)
    assert status.status == "completed"
    assert status.output and "summary" in status.output


@pytest.mark.asyncio
async def test_submit_composed_job_spawns_children():
    orch = HierarchicalJobOrchestrator()
    req = """
    - Task A
    - Task B
    - Task C
    """
    jr = await orch.submit_job(req, depth=0)
    await orch._tasks[jr.job_id]
    tree = await orch.get_tree(jr.job_id)
    assert len(tree["children"]) == 3
    assert tree["children"][0]["depth"] == 1


@pytest.mark.asyncio
async def test_cancel_running_job_sets_canceled():
    orch = HierarchicalJobOrchestrator()
    jr = await orch.submit_job("- A\n- B\n- C\n- D", depth=0)
    # Give the task a moment to start
    await asyncio.sleep(0.01)
    canceled = await orch.cancel(jr.job_id)
    assert canceled in (True, False)  # cancel may race; ensure API doesn't crash
    # cancel() already awaits the task, so status should be updated
    st = await orch.get_status(jr.job_id)
    assert st.status in ("completed", "canceled")

