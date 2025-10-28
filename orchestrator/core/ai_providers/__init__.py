"""
AI Providers Module

This module provides interfaces and implementations for various AI providers
used in the parallel coding orchestration system.

Available Providers:
    - CodexCLIProvider: ChatGPT Code Interpreter (via OpenAI Codex CLI)
    - ClaudeAPIProvider: Anthropic Claude API (via native SDK with Tool Use)

Author: Claude (Sonnet 4.5)
Created: 2025-10-27
Version: 2.0.0
"""

from orchestrator.core.ai_providers.codex_cli_provider import (
    CodexCLIProvider,
    CodexProviderConfig,
    CodexExecutionResult as CodexResult,
    CodexError,
)

from orchestrator.core.ai_providers.claude_api_provider import (
    ClaudeAPIProvider,
    ClaudeAPIConfig,
    ClaudeExecutionResult,
    ClaudeAPIError,
    ExecutionStatus,
    FileOperation,
    FileOperationType,
)

__all__ = [
    # Codex CLI Provider
    "CodexCLIProvider",
    "CodexProviderConfig",
    "CodexResult",
    "CodexError",
    # Claude API Provider
    "ClaudeAPIProvider",
    "ClaudeAPIConfig",
    "ClaudeExecutionResult",
    "ClaudeAPIError",
    "ExecutionStatus",
    "FileOperation",
    "FileOperationType",
]
