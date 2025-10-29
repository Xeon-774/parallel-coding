"""Supervisor core package.

Exports primary classes for external consumers.
"""

from .claude_code_supervisor import (
    ClaudeCodeSupervisor,
    ConfirmationPrompt,
    ProcessResult,
    SpawnClaudeCodeInput,
)
from .io_handler import ProcessIOHandler
from .supervisor_manager import SupervisorManager

__all__ = [
    "ClaudeCodeSupervisor",
    "SupervisorManager",
    "SpawnClaudeCodeInput",
    "ProcessResult",
    "ConfirmationPrompt",
    "ProcessIOHandler",
]
