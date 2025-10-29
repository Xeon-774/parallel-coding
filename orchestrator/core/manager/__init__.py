"""
AI Manager Module

This module provides manager implementations for coordinating multiple AI providers
in the parallel coding orchestration system.

Available Managers:
    - ClaudeCodexManager: Hybrid manager using Claude for orchestration and Codex for execution

Author: Claude (Sonnet 4.5)
Created: 2025-10-27
Version: 1.0.0
"""

from orchestrator.core.manager.claude_codex_manager import (
    ClaudeCodexManager,
    CodexTask,
    TaskComplexity,
    TaskResult,
)

__all__ = [
    "ClaudeCodexManager",
    "CodexTask",
    "TaskResult",
    "TaskComplexity",
]
