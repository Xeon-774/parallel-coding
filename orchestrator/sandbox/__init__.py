"""
Hermetic Execution Sandbox

Phase 0 Week 2 - MVP Implementation

Docker-based isolated execution environment with:
- Resource quotas (CPU, memory, processes)
- No network by default
- Read-only root filesystem
- Non-root user execution
- Auto-cleanup
"""

from orchestrator.sandbox.sandbox_config import (
    SandboxConfig,
    ResourceLimits,
    NetworkPolicy,
    DEFAULT_LOW_RISK,
    DEFAULT_MEDIUM_RISK,
    DEFAULT_HIGH_RISK,
)

from orchestrator.sandbox.docker_sandbox import (
    DockerSandbox,
    SandboxExecutionError,
    SandboxTimeoutError,
    execute_in_sandbox,
)

__all__ = [
    # Configuration
    "SandboxConfig",
    "ResourceLimits",
    "NetworkPolicy",
    "DEFAULT_LOW_RISK",
    "DEFAULT_MEDIUM_RISK",
    "DEFAULT_HIGH_RISK",
    # Sandbox
    "DockerSandbox",
    "SandboxExecutionError",
    "SandboxTimeoutError",
    "execute_in_sandbox",
]
