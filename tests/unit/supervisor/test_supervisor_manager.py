import asyncio

import pytest

from orchestrator.core.supervisor.claude_code_supervisor import (
    ClaudeCodeSupervisor,
    ConfirmationPrompt,
    ProcessResult,
)
from orchestrator.core.supervisor.supervisor_manager import SupervisorManager


class DummySupervisor(ClaudeCodeSupervisor):
    def __init__(self):
        super().__init__(workspace_root=".")
        self._lines = []
        self._alive = False

    def spawn_claude_code(
        self, task_file: str, timeout: int = 300
    ) -> ProcessResult:  # noqa: ARG002
        self._alive = True
        return ProcessResult(True, process_id=1)

    async def monitor_output(self):
        class DummyIO:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return None

            async def read_async(self):
                for x in ["normal", "Are you sure?", "done"]:
                    yield x

            async def close(self):
                return None

        return DummyIO(), object()

    def detect_confirmation_prompt(self, output: str):  # noqa: D401
        return (
            ConfirmationPrompt(output, pattern="are you sure", confidence=1.0)
            if "sure" in output
            else None
        )

    def terminate(self) -> bool:
        self._alive = False
        return True

    @property
    def is_alive(self) -> bool:  # type: ignore[override]
        return self._alive


@pytest.mark.asyncio
async def test_manager_spawn_and_stream():
    mgr = SupervisorManager(".", supervisor=DummySupervisor())
    res = mgr.spawn("task.txt")
    assert res.success is True
    task = await mgr.stream()
    await asyncio.wait_for(task, timeout=1)
    assert mgr.status()["alive"] in {"True", "False"}


def test_detect_error():
    mgr = SupervisorManager(".", supervisor=DummySupervisor())
    assert mgr.detect_error("ERROR: bad") is True
    assert mgr.detect_error("ok") is False


@pytest.mark.asyncio
async def test_retry_with_backoff_success():
    mgr = SupervisorManager(".", supervisor=DummySupervisor())

    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("boom")
        return 42

    v = await mgr.retry_with_backoff(flaky)
    assert v == 42


@pytest.mark.asyncio
async def test_stop_cleans_up():
    mgr = SupervisorManager(".", supervisor=DummySupervisor())
    mgr.spawn("task.txt")
    await mgr.stop()
    assert mgr.check_health()["process"] == "dead"
