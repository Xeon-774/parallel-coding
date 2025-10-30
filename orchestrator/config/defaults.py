"""Default configuration values for cross-project compatibility.

This module provides safe, sensible default values for all configuration
options. These defaults ensure the tool works out-of-the-box while remaining
fully customizable via environment variables or .env files.

Part of Phase 1: Cross-Project Compatibility Initiative
See: ROADMAP_CROSS_PROJECT_COMPATIBILITY.md, DEVELOPMENT_POLICY.md
"""

from pathlib import Path
from typing import Final

# Version
VERSION: Final[str] = "2.0.0"

# Project Structure Defaults
# These are relative to the project root (auto-detected)
DEFAULT_WORKSPACE_DIR: Final[str] = "workspace"
DEFAULT_CONFIG_DIR: Final[str] = "config"
DEFAULT_LOGS_DIR: Final[str] = "logs"
DEFAULT_CACHE_DIR: Final[str] = ".cache/parallel-coding"

# Worker Defaults
DEFAULT_MAX_WORKERS: Final[int] = 4
DEFAULT_WORKER_TIMEOUT: Final[int] = 300  # 5 minutes
DEFAULT_WORKER_TYPE: Final[str] = "codex"

# AI Provider Defaults
DEFAULT_CODEX_MODEL: Final[str] = "gpt-5"
DEFAULT_CLAUDE_MODEL: Final[str] = "claude-sonnet-4.5"
DEFAULT_TEMPERATURE: Final[float] = 0.0
DEFAULT_MAX_TOKENS: Final[int] = 8192

# Codex CLI Flags
CODEX_REQUIRED_FLAGS: Final[str] = (
    "--json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check"
)

# File Encoding
DEFAULT_ENCODING: Final[str] = "utf-8"
DEFAULT_ENCODING_ERRORS: Final[str] = "replace"

# Logging Defaults
DEFAULT_LOG_LEVEL: Final[str] = "INFO"
DEFAULT_LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_ENABLE_DIALOGUE_LOGGING: Final[bool] = True

# Sandbox Defaults
DEFAULT_ENABLE_SANDBOX: Final[bool] = True
DEFAULT_SANDBOX_TIMEOUT: Final[int] = 300

# Dashboard Defaults
DEFAULT_ENABLE_WEB_UI: Final[bool] = True
DEFAULT_DASHBOARD_HOST: Final[str] = "127.0.0.1"
DEFAULT_DASHBOARD_PORT: Final[int] = 8050

# Git Defaults
DEFAULT_AUTO_COMMIT: Final[bool] = False
DEFAULT_AUTO_PUSH: Final[bool] = False

# Window Management Defaults (Legacy)
DEFAULT_AUTO_CLOSE_WINDOWS: Final[bool] = True
DEFAULT_WINDOW_CLOSE_DELAY: Final[int] = 3  # seconds

# Environment Variable Names
ENV_PREFIX: Final[str] = "PARALLEL_CODING_"

# Core Paths
ENV_WORKSPACE_ROOT: Final[str] = f"{ENV_PREFIX}WORKSPACE_ROOT"
ENV_CONFIG_DIR: Final[str] = f"{ENV_PREFIX}CONFIG_DIR"
ENV_LOGS_DIR: Final[str] = f"{ENV_PREFIX}LOGS_DIR"
ENV_CACHE_DIR: Final[str] = f"{ENV_PREFIX}CACHE_DIR"

# Binary Paths (optional - auto-detected if not set)
ENV_CODEX_PATH: Final[str] = f"{ENV_PREFIX}CODEX_PATH"
ENV_CLAUDE_PATH: Final[str] = f"{ENV_PREFIX}CLAUDE_PATH"
ENV_GIT_BASH_PATH: Final[str] = f"{ENV_PREFIX}GIT_BASH_PATH"
ENV_PYTHON_PATH: Final[str] = f"{ENV_PREFIX}PYTHON_PATH"

# WSL Configuration (optional - auto-detected if not set)
ENV_WSL_DISTRIBUTION: Final[str] = f"{ENV_PREFIX}WSL_DISTRIBUTION"
ENV_NVM_PATH: Final[str] = f"{ENV_PREFIX}NVM_PATH"

# Project Metadata
ENV_PROJECT_NAME: Final[str] = f"{ENV_PREFIX}PROJECT_NAME"
ENV_PROJECT_ROOT: Final[str] = f"{ENV_PREFIX}PROJECT_ROOT"
ENV_ENVIRONMENT: Final[str] = f"{ENV_PREFIX}ENVIRONMENT"

# Worker Configuration
ENV_MAX_WORKERS: Final[str] = f"{ENV_PREFIX}MAX_WORKERS"
ENV_WORKER_TIMEOUT: Final[str] = f"{ENV_PREFIX}WORKER_TIMEOUT"
ENV_DEFAULT_WORKER_TYPE: Final[str] = f"{ENV_PREFIX}DEFAULT_WORKER_TYPE"

# AI Provider Configuration
ENV_CODEX_MODEL: Final[str] = f"{ENV_PREFIX}CODEX_MODEL"
ENV_CLAUDE_MODEL: Final[str] = f"{ENV_PREFIX}CLAUDE_MODEL"
ENV_TEMPERATURE: Final[str] = f"{ENV_PREFIX}TEMPERATURE"
ENV_MAX_TOKENS: Final[str] = f"{ENV_PREFIX}MAX_TOKENS"

# Feature Flags
ENV_ENABLE_SANDBOX: Final[str] = f"{ENV_PREFIX}ENABLE_SANDBOX"
ENV_ENABLE_WEB_UI: Final[str] = f"{ENV_PREFIX}ENABLE_WEB_UI"
ENV_ENABLE_DIALOGUE_LOGGING: Final[str] = f"{ENV_PREFIX}ENABLE_DIALOGUE_LOGGING"
ENV_LOG_LEVEL: Final[str] = f"{ENV_PREFIX}LOG_LEVEL"

# Dashboard Configuration
ENV_DASHBOARD_HOST: Final[str] = f"{ENV_PREFIX}DASHBOARD_HOST"
ENV_DASHBOARD_PORT: Final[str] = f"{ENV_PREFIX}DASHBOARD_PORT"

# Git Configuration
ENV_AUTO_COMMIT: Final[str] = f"{ENV_PREFIX}AUTO_COMMIT"
ENV_AUTO_PUSH: Final[str] = f"{ENV_PREFIX}AUTO_PUSH"


def get_user_cache_dir() -> Path:
    """Get platform-appropriate user cache directory.

    Returns:
        Path to user's cache directory for parallel-coding

    Platform-specific locations:
        - Linux: ~/.cache/parallel-coding
        - macOS: ~/Library/Caches/parallel-coding
        - Windows: %LOCALAPPDATA%/parallel-coding/cache

    Examples:
        >>> cache_dir = get_user_cache_dir()
        >>> # Linux: Path("/home/user/.cache/parallel-coding")
        >>> # Windows: Path("C:/Users/user/AppData/Local/parallel-coding/cache")
    """
    import platform

    system = platform.system()

    if system == "Windows":
        # Use LOCALAPPDATA on Windows
        local_app_data = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return local_app_data / "parallel-coding" / "cache"
    elif system == "Darwin":
        # Use ~/Library/Caches on macOS
        return Path.home() / "Library" / "Caches" / "parallel-coding"
    else:
        # Use XDG_CACHE_HOME or ~/.cache on Linux/Unix
        xdg_cache = os.getenv("XDG_CACHE_HOME", str(Path.home() / ".cache"))
        return Path(xdg_cache) / "parallel-coding"


def get_user_config_dir() -> Path:
    """Get platform-appropriate user configuration directory.

    Returns:
        Path to user's config directory for parallel-coding

    Platform-specific locations:
        - Linux: ~/.config/parallel-coding
        - macOS: ~/Library/Application Support/parallel-coding
        - Windows: %APPDATA%/parallel-coding

    Examples:
        >>> config_dir = get_user_config_dir()
        >>> # Linux: Path("/home/user/.config/parallel-coding")
        >>> # Windows: Path("C:/Users/user/AppData/Roaming/parallel-coding")
    """
    import platform

    system = platform.system()

    if system == "Windows":
        # Use APPDATA on Windows
        app_data = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        return app_data / "parallel-coding"
    elif system == "Darwin":
        # Use ~/Library/Application Support on macOS
        return Path.home() / "Library" / "Application Support" / "parallel-coding"
    else:
        # Use XDG_CONFIG_HOME or ~/.config on Linux/Unix
        xdg_config = os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        return Path(xdg_config) / "parallel-coding"


# Import os for environment variable access
import os


def get_default_project_name() -> str:
    """Get default project name from current directory.

    Returns:
        Name of current directory (used as project name)

    Examples:
        >>> # In directory /home/user/my-awesome-project
        >>> get_default_project_name()
        'my-awesome-project'
    """
    return Path.cwd().name


def get_default_environment() -> str:
    """Get default environment name.

    Returns:
        Environment name (development, staging, production)

    Examples:
        >>> get_default_environment()
        'development'
    """
    return os.getenv("ENV", os.getenv("ENVIRONMENT", "development"))


# Binary Discovery Defaults
BINARY_SEARCH_TIMEOUT: Final[int] = 5  # seconds
BINARY_CACHE_TTL: Final[int] = 3600  # 1 hour


def get_npm_global_paths() -> list[Path]:
    """Get common npm global installation paths for current platform.

    Returns:
        List of paths where npm global binaries might be installed

    Examples:
        >>> paths = get_npm_global_paths()
        >>> # Windows: [Path("C:/Users/user/AppData/Roaming/npm"), ...]
        >>> # Linux: [Path("/usr/local/bin"), Path("~/.npm-global/bin"), ...]
    """
    import platform

    system = platform.system()
    paths: list[Path] = []

    if system == "Windows":
        # Windows npm global paths
        paths.extend(
            [
                Path.home() / "AppData" / "Roaming" / "npm",
                Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "npm",
            ]
        )
    else:
        # Linux/macOS npm global paths
        paths.extend(
            [
                Path("/usr/local/bin"),
                Path.home() / ".npm-global" / "bin",
                Path.home() / ".npm" / "bin",
                Path("/usr/bin"),
            ]
        )

        # Add NVM paths if available
        nvm_dir = os.getenv("NVM_DIR")
        if nvm_dir:
            paths.extend(
                [
                    Path(nvm_dir) / "current" / "bin",
                    Path(nvm_dir) / "versions" / "node" / "current" / "bin",
                ]
            )

    return paths


# Installation URLs (for error messages)
INSTALLATION_URLS: Final[dict[str, str]] = {
    "codex": "https://openai.com/codex",
    "claude": "https://anthropic.com/claude",
    "git": "https://git-scm.com/downloads",
    "wsl": "https://docs.microsoft.com/en-us/windows/wsl/install",
    "nvm": "https://github.com/nvm-sh/nvm",
}

# Documentation URLs
DOCS_BASE_URL: Final[str] = "https://github.com/yourusername/parallel-coding"
DOCS_INSTALLATION: Final[str] = f"{DOCS_BASE_URL}/blob/main/INSTALLATION.md"
DOCS_CONFIGURATION: Final[str] = f"{DOCS_BASE_URL}/blob/main/CONFIGURATION.md"
DOCS_TROUBLESHOOTING: Final[str] = f"{DOCS_BASE_URL}/blob/main/TROUBLESHOOTING.md"
