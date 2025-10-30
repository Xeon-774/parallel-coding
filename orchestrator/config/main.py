"""Orchestrator configuration with cross-project compatibility.

This module provides the main configuration system for the parallel-coding
tool, integrating auto-detection, validation, and user customization.

Part of Phase 1: Cross-Project Compatibility Initiative
See: ROADMAP_CROSS_PROJECT_COMPATIBILITY.md, DEVELOPMENT_POLICY.md
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from orchestrator.config.defaults import (
    DEFAULT_AUTO_CLOSE_WINDOWS,
    DEFAULT_AUTO_COMMIT,
    DEFAULT_AUTO_PUSH,
    DEFAULT_CLAUDE_MODEL,
    DEFAULT_CODEX_MODEL,
    DEFAULT_DASHBOARD_HOST,
    DEFAULT_DASHBOARD_PORT,
    DEFAULT_ENABLE_DIALOGUE_LOGGING,
    DEFAULT_ENABLE_SANDBOX,
    DEFAULT_ENABLE_WEB_UI,
    DEFAULT_LOG_LEVEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MAX_WORKERS,
    DEFAULT_TEMPERATURE,
    DEFAULT_WINDOW_CLOSE_DELAY,
    DEFAULT_WORKER_TIMEOUT,
    DEFAULT_WORKER_TYPE,
    ENV_AUTO_COMMIT,
    ENV_AUTO_PUSH,
    ENV_CLAUDE_MODEL,
    ENV_CLAUDE_PATH,
    ENV_CODEX_MODEL,
    ENV_CODEX_PATH,
    ENV_DASHBOARD_HOST,
    ENV_DASHBOARD_PORT,
    ENV_ENABLE_DIALOGUE_LOGGING,
    ENV_ENABLE_SANDBOX,
    ENV_ENABLE_WEB_UI,
    ENV_ENVIRONMENT,
    ENV_GIT_BASH_PATH,
    ENV_LOG_LEVEL,
    ENV_MAX_TOKENS,
    ENV_MAX_WORKERS,
    ENV_NVM_PATH,
    ENV_PROJECT_NAME,
    ENV_PYTHON_PATH,
    ENV_TEMPERATURE,
    ENV_WORKER_TIMEOUT,
    ENV_WSL_DISTRIBUTION,
    get_default_environment,
    get_default_project_name,
)
from orchestrator.config.environment import get_environment_detector
from orchestrator.config.validator import ConfigValidator, ValidationResult
from orchestrator.utils.binary_discovery import get_binary_discovery
import logging

logger = logging.getLogger(__name__)
from orchestrator.utils.path_resolver import (
    get_cache_dir,
    get_config_dir,
    get_logs_dir,
    get_project_root,
    get_workspace_path,
)


@dataclass
class OrchestratorConfig:
    """Main orchestrator configuration with auto-detection and validation.

    This configuration class automatically detects system settings, validates
    paths, and provides clear error messages for missing dependencies.

    All paths and environment-specific values are auto-detected or loaded from
    environment variables, ensuring cross-project compatibility.
    """

    # Project metadata
    project_name: str = field(default_factory=get_default_project_name)
    project_root: Path = field(default_factory=get_project_root)
    environment: str = field(default_factory=get_default_environment)

    # Core paths
    workspace_root: Path = field(default_factory=lambda: get_workspace_path(create=True))
    config_dir: Path = field(default_factory=lambda: get_config_dir(create=False))
    logs_dir: Path = field(default_factory=lambda: get_logs_dir(create=True))
    cache_dir: Path = field(default_factory=lambda: get_cache_dir(create=True))

    # Binary paths (auto-detected)
    codex_command_path: Optional[Path] = None
    claude_command_path: Optional[Path] = None
    git_bash_path: Optional[Path] = None
    python_path: Optional[Path] = None

    # WSL configuration (Windows only)
    wsl_distribution: Optional[str] = None
    nvm_path: Optional[Path] = None

    # Worker configuration
    max_workers: int = DEFAULT_MAX_WORKERS
    worker_timeout: int = DEFAULT_WORKER_TIMEOUT
    default_worker_type: str = DEFAULT_WORKER_TYPE

    # AI provider configuration
    codex_model: str = DEFAULT_CODEX_MODEL
    claude_model: str = DEFAULT_CLAUDE_MODEL
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS

    # Feature flags
    enable_sandbox: bool = DEFAULT_ENABLE_SANDBOX
    enable_web_ui: bool = DEFAULT_ENABLE_WEB_UI
    enable_dialogue_logging: bool = DEFAULT_ENABLE_DIALOGUE_LOGGING
    log_level: str = DEFAULT_LOG_LEVEL

    # Dashboard configuration
    dashboard_host: str = DEFAULT_DASHBOARD_HOST
    dashboard_port: int = DEFAULT_DASHBOARD_PORT

    # Git configuration
    auto_commit: bool = DEFAULT_AUTO_COMMIT
    auto_push: bool = DEFAULT_AUTO_PUSH

    # Legacy compatibility settings
    execution_mode: str = "wsl"  # "wsl" or "windows"
    default_timeout: int = 120
    max_retries: int = 2
    poll_interval: int = 2
    enable_visible_workers: bool = False
    auto_close_windows: bool = DEFAULT_AUTO_CLOSE_WINDOWS
    window_close_delay: int = DEFAULT_WINDOW_CLOSE_DELAY
    claude_flags: Optional[List[str]] = None

    def __post_init__(self) -> None:
        """Initialize configuration with auto-detection and validation."""
        # Auto-detect binaries
        self._detect_binaries()

        # Auto-detect WSL configuration (Windows only)
        self._detect_wsl_config()

        # Legacy compatibility: Set claude_flags if None
        if self.claude_flags is None:
            self.claude_flags = ["--print"]

        # Validate configuration
        self._validate_config()

    def _detect_binaries(self) -> None:
        """Auto-detect binary paths if not already set."""
        discovery = get_binary_discovery()

        # Codex CLI (check env var first)
        if self.codex_command_path is None:
            env_codex = os.getenv(ENV_CODEX_PATH)
            if env_codex:
                self.codex_command_path = Path(env_codex)
            else:
                # Auto-detect (non-required for flexibility)
                self.codex_command_path = discovery.find_codex(required=False)

        # Claude CLI
        if self.claude_command_path is None:
            env_claude = os.getenv(ENV_CLAUDE_PATH)
            if env_claude:
                self.claude_command_path = Path(env_claude)
            else:
                self.claude_command_path = discovery.find_claude(required=False)

        # Git Bash (Windows only)
        if self.git_bash_path is None:
            env_git_bash = os.getenv(ENV_GIT_BASH_PATH)
            if env_git_bash:
                self.git_bash_path = Path(env_git_bash)
            else:
                from orchestrator.config.environment import get_environment_detector

                detector = get_environment_detector()
                detected_bash = detector.detect_git_bash_path()
                if detected_bash:
                    self.git_bash_path = detected_bash

        # Python
        if self.python_path is None:
            env_python = os.getenv(ENV_PYTHON_PATH)
            if env_python:
                self.python_path = Path(env_python)
            else:
                self.python_path = discovery.find_python()

    def _detect_wsl_config(self) -> None:
        """Auto-detect WSL configuration (Windows only)."""
        import platform

        detector = get_environment_detector()

        # WSL distribution
        if self.wsl_distribution is None:
            env_wsl_dist = os.getenv(ENV_WSL_DISTRIBUTION)
            if env_wsl_dist:
                self.wsl_distribution = env_wsl_dist
            else:
                detected = detector.detect_wsl_distribution()
                # Use detected value if found, otherwise keep None (will use default in commands)
                self.wsl_distribution = detected if detected else (
                    "Ubuntu-24.04" if platform.system() == "Windows" else None
                )

        # NVM path
        if self.nvm_path is None:
            env_nvm = os.getenv(ENV_NVM_PATH)
            if env_nvm:
                self.nvm_path = Path(env_nvm)
            else:
                # Auto-detect NVM path (can be None if NVM not installed)
                self.nvm_path = detector.detect_nvm_path()

    def _validate_config(self) -> None:
        """Validate configuration and log warnings for issues."""
        validator = ConfigValidator(strict=False)

        # Validate workspace (should exist - we created it in __post_init__)
        result = validator.validate_path_exists(
            self.workspace_root, "Workspace directory", required=True, create=False
        )
        if not result.valid:
            logger.warning(str(result))

        # Validate Codex CLI (optional)
        if self.codex_command_path:
            result = validator.validate_executable(
                self.codex_command_path, "Codex CLI", required=False
            )
            if not result.valid:
                logger.warning(str(result))

        # Validate Claude CLI (optional)
        if self.claude_command_path:
            result = validator.validate_executable(
                self.claude_command_path, "Claude CLI", required=False
            )
            if not result.valid:
                logger.warning(str(result))

    @property
    def codex_command(self) -> str:
        """Get Codex command string for execution."""
        if self.codex_command_path:
            return str(self.codex_command_path)
        return "codex"  # Fallback to PATH

    @property
    def claude_command(self) -> str:
        """Get Claude command string for execution."""
        if self.claude_command_path:
            return str(self.claude_command_path)
        return "claude"  # Fallback to PATH

    @property
    def claude_full_path(self) -> str:
        """Claude CLI full path (legacy compatibility)."""
        return self.claude_command

    @property
    def wsl_workspace_root(self) -> str:
        """Get WSL-formatted workspace path (legacy compatibility)."""
        from orchestrator.utils.path_resolver import get_path_resolver

        resolver = get_path_resolver()
        return resolver.to_wsl_path(self.workspace_root)

    def get_claude_command(
        self, input_file: str, output_file: str, error_file: Optional[str] = None
    ) -> str:
        """Generate Claude execution command based on mode.

        Args:
            input_file: Input file path
            output_file: Output file path
            error_file: Error output file path (optional)

        Returns:
            Command string for Claude execution
        """
        if self.execution_mode == "windows":
            return self.get_claude_command_windows(input_file, output_file, error_file)
        else:
            return self.get_claude_command_wsl(input_file, output_file, error_file)

    def get_claude_command_wsl(
        self, input_file: str, output_file: str, error_file: Optional[str] = None
    ) -> str:
        """Generate WSL-based Claude execution command.

        Args:
            input_file: Input file path
            output_file: Output file path
            error_file: Error output file path (optional)

        Returns:
            WSL command string
        """
        flags_str = " ".join(self.claude_flags or [])

        # Build PATH with NVM if available
        path_export = ""
        if self.nvm_path:
            path_export = f"export PATH='{self.nvm_path}:$PATH' && "

        if error_file:
            # Separate stdout and stderr
            cmd = (
                f"wsl -d {self.wsl_distribution} bash -c "
                f'"{path_export}'
                f"{self.claude_command} {flags_str} < '{input_file}' > '{output_file}' 2> '{error_file}'\""
            )
        else:
            # Merge stderr to stdout
            cmd = (
                f"wsl -d {self.wsl_distribution} bash -c "
                f'"{path_export}'
                f"{self.claude_command} {flags_str} < '{input_file}' > '{output_file}' 2>&1\""
            )

        return cmd

    def get_claude_command_windows(
        self, input_file: str, output_file: str, error_file: Optional[str] = None
    ) -> str:
        """Generate Windows-based Claude execution command.

        Args:
            input_file: Input file path
            output_file: Output file path
            error_file: Error output file path (optional)

        Returns:
            Windows command string
        """
        flags_str = " ".join(self.claude_flags or [])

        # Use git-bash if available
        if self.git_bash_path:
            if error_file:
                cmd = (
                    f'"{self.git_bash_path}" -c '
                    f"\"export CLAUDE_CODE_GIT_BASH_PATH='{self.git_bash_path}' && "
                    f"{self.claude_command} {flags_str} < '{input_file}' > '{output_file}' 2> '{error_file}'\""
                )
            else:
                cmd = (
                    f'"{self.git_bash_path}" -c '
                    f"\"export CLAUDE_CODE_GIT_BASH_PATH='{self.git_bash_path}' && "
                    f"{self.claude_command} {flags_str} < '{input_file}' > '{output_file}' 2>&1\""
                )
        else:
            # Fallback to cmd (may not work)
            if error_file:
                cmd = f'cmd /c "{self.claude_command} {flags_str} < "{input_file}" > "{output_file}" 2> "{error_file}""'
            else:
                cmd = f'cmd /c "{self.claude_command} {flags_str} < "{input_file}" > "{output_file}" 2>&1"'

        return cmd

    @classmethod
    def from_env(cls) -> "OrchestratorConfig":
        """Create configuration from environment variables.

        Returns:
            OrchestratorConfig instance with values from environment
        """
        # Load all environment variables with proper type conversion
        config = cls(
            # Project metadata
            project_name=os.getenv(ENV_PROJECT_NAME, get_default_project_name()),
            environment=os.getenv(ENV_ENVIRONMENT, get_default_environment()),
            # Worker configuration
            max_workers=int(os.getenv(ENV_MAX_WORKERS, str(DEFAULT_MAX_WORKERS))),
            worker_timeout=int(os.getenv(ENV_WORKER_TIMEOUT, str(DEFAULT_WORKER_TIMEOUT))),
            # AI provider configuration
            codex_model=os.getenv(ENV_CODEX_MODEL, DEFAULT_CODEX_MODEL),
            claude_model=os.getenv(ENV_CLAUDE_MODEL, DEFAULT_CLAUDE_MODEL),
            temperature=float(os.getenv(ENV_TEMPERATURE, str(DEFAULT_TEMPERATURE))),
            max_tokens=int(os.getenv(ENV_MAX_TOKENS, str(DEFAULT_MAX_TOKENS))),
            # Feature flags
            enable_sandbox=_parse_bool(os.getenv(ENV_ENABLE_SANDBOX, str(DEFAULT_ENABLE_SANDBOX))),
            enable_web_ui=_parse_bool(os.getenv(ENV_ENABLE_WEB_UI, str(DEFAULT_ENABLE_WEB_UI))),
            enable_dialogue_logging=_parse_bool(
                os.getenv(ENV_ENABLE_DIALOGUE_LOGGING, str(DEFAULT_ENABLE_DIALOGUE_LOGGING))
            ),
            log_level=os.getenv(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL),
            # Dashboard configuration
            dashboard_host=os.getenv(ENV_DASHBOARD_HOST, DEFAULT_DASHBOARD_HOST),
            dashboard_port=int(os.getenv(ENV_DASHBOARD_PORT, str(DEFAULT_DASHBOARD_PORT))),
            # Git configuration
            auto_commit=_parse_bool(os.getenv(ENV_AUTO_COMMIT, str(DEFAULT_AUTO_COMMIT))),
            auto_push=_parse_bool(os.getenv(ENV_AUTO_PUSH, str(DEFAULT_AUTO_PUSH))),
            # Legacy compatibility
            execution_mode=os.getenv("ORCHESTRATOR_MODE", "wsl"),
            default_timeout=int(os.getenv("ORCHESTRATOR_TIMEOUT", "120")),
            max_retries=int(os.getenv("ORCHESTRATOR_MAX_RETRIES", "2")),
            enable_visible_workers=_parse_bool(os.getenv("ORCHESTRATOR_VISIBLE_WORKERS", "false")),
            auto_close_windows=_parse_bool(os.getenv("ORCHESTRATOR_AUTO_CLOSE", "true")),
            window_close_delay=int(os.getenv("ORCHESTRATOR_WINDOW_DELAY", "3")),
        )

        return config


@dataclass
class TaskConfig:
    """Task configuration for code generation prompts."""

    # Default prompt suffix
    default_prompt_suffix: str = (
        "\n\nIMPORTANT: Do NOT create any files. Output ONLY the code to stdout. "
        "Write clean, commented code. No explanations, no file creation, just the code."
    )

    # Task type templates
    code_generation_template: str = (
        "Create {description}. Include proper error handling and documentation."
    )
    refactoring_template: str = (
        "Refactor the following code: {description}. Improve readability and performance."
    )
    testing_template: str = "Create comprehensive unit tests for: {description}."


def _parse_bool(value: str) -> bool:
    """Parse string to boolean.

    Args:
        value: String value to parse

    Returns:
        Boolean value

    Examples:
        >>> _parse_bool("true")
        True
        >>> _parse_bool("false")
        False
        >>> _parse_bool("1")
        True
    """
    return value.lower() in ("true", "yes", "1", "on")


# Default configuration instances
DEFAULT_CONFIG = OrchestratorConfig.from_env()
DEFAULT_TASK_CONFIG = TaskConfig()
