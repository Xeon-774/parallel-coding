"""
pytest configuration and fixtures

共通のフィクスチャとテスト設定を提供します。
"""

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_workspace():
    """一時ワークスペースフィクスチャ"""
    workspace = Path(tempfile.mkdtemp())
    yield workspace
    shutil.rmtree(workspace, ignore_errors=True)


@pytest.fixture
def mock_config():
    """モック設定フィクスチャ"""
    from orchestrator.config import OrchestratorConfig

    return OrchestratorConfig(
        workspace_root="./test_workspace",
        execution_mode="windows",
        claude_code_git_bash_path=r"C:\opt\Git.Git\usr\bin\bash.exe",
        enable_visible_workers=False,
    )
