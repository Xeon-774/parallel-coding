"""Supervisor core package.

Exports primary classes for external consumers.
"""

from .claude_code_supervisor import (
    ClaudeCodeSupervisor,
    SpawnClaudeCodeInput,
    ProcessResult,
    ConfirmationPrompt,
)
from .supervisor_manager import SupervisorManager
from .io_handler import ProcessIOHandler

__all__ = [
    "ClaudeCodeSupervisor",
    "SupervisorManager",
    "SpawnClaudeCodeInput",
    "ProcessResult",
    "ConfirmationPrompt",
    "ProcessIOHandler",
]

