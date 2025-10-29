import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.core.supervisor.claude_code_supervisor import (
    ClaudeCodeSupervisor,
    SpawnClaudeCodeInput,
)


class DummyChild:
    def __init__(self):
        self.pid = 1234
        self._alive = True

    def isalive(self):
        return self._alive

    def terminate(self):
        self._alive = False

    def kill(self, _sig):  # noqa: ARG002
        self._alive = False

    def send(self, _data):  # noqa: ARG002
        return 0

    def sendline(self, _line):  # noqa: ARG002
        return 0


@pytest.fixture()
def workspace(tmp_path):
    p = tmp_path / "ws"
    p.mkdir()
    (p / "task.txt").write_text("do stuff\n", encoding="utf-8")
    return p


def install_expect_module(monkeypatch):
    dummy = SimpleNamespace(spawn=lambda *a, **k: DummyChild())
    if sys.platform.startswith("win"):
        monkeypatch.setitem(sys.modules, "wexpect", dummy)
    else:
        monkeypatch.setitem(sys.modules, "pexpect", dummy)


def test_spawn_success(monkeypatch, workspace):
    install_expect_module(monkeypatch)
    sup = ClaudeCodeSupervisor(str(workspace))
    res = sup.spawn_claude_code("task.txt")
    assert res.success is True
    assert res.process_id == 1234


def test_spawn_validation_error(workspace):
    sup = ClaudeCodeSupervisor(str(workspace))
    res = sup.spawn_claude_code("../../evil")
    assert res.success is False
    assert "Invalid" in (res.error_message or "")


def test_detect_confirmation_patterns(workspace):
    sup = ClaudeCodeSupervisor(str(workspace))
    assert sup.detect_confirmation_prompt("Are you sure?") is not None
    assert sup.detect_confirmation_prompt("Proceed? yes/no") is not None
    assert sup.detect_confirmation_prompt("normal line") is None


def test_terminate(monkeypatch, workspace):
    install_expect_module(monkeypatch)
    sup = ClaudeCodeSupervisor(str(workspace))
    res = sup.spawn_claude_code("task.txt")
    assert res.success
    assert sup.is_alive is True
    assert sup.terminate() is True
    assert sup.is_alive is False
