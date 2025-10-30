"""Configuration package for parallel-coding.

This package provides configuration management with auto-detection,
validation, and cross-project compatibility.

Part of Phase 1: Cross-Project Compatibility Initiative
See: ROADMAP_CROSS_PROJECT_COMPATIBILITY.md
"""

# Import main configuration classes
from orchestrator.config.main import (
    OrchestratorConfig,
    TaskConfig,
    DEFAULT_CONFIG,
    DEFAULT_TASK_CONFIG,
)

# Import defaults
from orchestrator.config.defaults import (
    DEFAULT_CODEX_MODEL,
    DEFAULT_CLAUDE_MODEL,
    DEFAULT_MAX_WORKERS,
    DEFAULT_WORKER_TIMEOUT,
    ENV_PREFIX,
)

# Import environment detection
from orchestrator.config.environment import EnvironmentDetector, get_environment_detector

# Import validation
from orchestrator.config.validator import ConfigValidator, ConfigurationError, ValidationResult

__all__ = [
    # Main config classes
    "OrchestratorConfig",
    "TaskConfig",
    "DEFAULT_CONFIG",
    "DEFAULT_TASK_CONFIG",
    # Defaults
    "DEFAULT_CODEX_MODEL",
    "DEFAULT_CLAUDE_MODEL",
    "DEFAULT_MAX_WORKERS",
    "DEFAULT_WORKER_TIMEOUT",
    "ENV_PREFIX",
    # Environment detection
    "EnvironmentDetector",
    "get_environment_detector",
    # Validation
    "ConfigValidator",
    "ConfigurationError",
    "ValidationResult",
]
