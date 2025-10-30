"""Path resolution utilities for cross-project compatibility.

This module provides dynamic path resolution for project-relative paths,
ensuring the tool works regardless of where it's installed or executed.

Part of Phase 1: Cross-Project Compatibility Initiative
See: ROADMAP_CROSS_PROJECT_COMPATIBILITY.md, DEVELOPMENT_POLICY.md
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

import logging

logger = logging.getLogger(__name__)


class PathResolver:
    """Resolve project-relative paths dynamically."""

    def __init__(self) -> None:
        """Initialize path resolver with caching."""
        self._cache: dict[str, Optional[Path]] = {}

    def get_project_root(self, start_path: Optional[Path] = None) -> Path:
        """Get project root directory.

        Searches upward from start_path to find:
        1. Git repository root (.git directory)
        2. Directory containing parallel-coding tool
        3. Current working directory (fallback)

        Args:
            start_path: Starting path for search (default: current file location)

        Returns:
            Path to project root directory

        Examples:
            >>> resolver = PathResolver()
            >>> root = resolver.get_project_root()
            >>> # In git repo: Path("/home/user/my-project")
            >>> # Otherwise: Path.cwd()
        """
        if "project_root" in self._cache and start_path is None:
            return self._cache["project_root"]

        if start_path is None:
            # Start from this file's location
            start_path = Path(__file__).resolve().parent

        # Check environment variable override
        env_root = os.getenv("PARALLEL_CODING_PROJECT_ROOT")
        if env_root:
            root = Path(env_root).resolve()
            logger.info(f"Using project root from env var: {root}")
            self._cache["project_root"] = root
            return root

        # Try to find git root
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=start_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                git_root = Path(result.stdout.strip()).resolve()
                logger.info(f"Detected git repository root: {git_root}")
                self._cache["project_root"] = git_root
                return git_root
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.debug(f"Git root detection failed: {e}")

        # Search upward for parallel-coding directory (when used as submodule/tool)
        current = start_path.resolve()
        while current != current.parent:
            # Check if this directory contains parallel-coding
            if (current / "orchestrator").exists() and (current / "workspace").exists():
                logger.info(f"Detected parallel-coding installation at: {current}")
                # Go up one more level if we're in the parallel-coding directory itself
                if current.name == "parallel-coding":
                    parent_root = current.parent
                    logger.info(f"Using parent directory as project root: {parent_root}")
                    self._cache["project_root"] = parent_root
                    return parent_root
                self._cache["project_root"] = current
                return current

            # Check for common project markers
            markers = [".git", "pyproject.toml", "setup.py", "package.json", "README.md"]
            if any((current / marker).exists() for marker in markers):
                logger.info(f"Detected project root via markers: {current}")
                self._cache["project_root"] = current
                return current

            current = current.parent

        # Fallback to current working directory
        cwd = Path.cwd().resolve()
        logger.warning(f"Could not detect project root, using cwd: {cwd}")
        self._cache["project_root"] = cwd
        return cwd

    def get_workspace_path(self, create: bool = False) -> Path:
        """Get workspace directory path.

        Args:
            create: If True, create directory if it doesn't exist

        Returns:
            Path to workspace directory

        Examples:
            >>> resolver = PathResolver()
            >>> workspace = resolver.get_workspace_path()
            >>> # Returns: {PROJECT_ROOT}/workspace
        """
        if "workspace_path" in self._cache:
            workspace = self._cache["workspace_path"]
        else:
            # Check environment variable
            env_workspace = os.getenv("PARALLEL_CODING_WORKSPACE_ROOT")
            if env_workspace:
                workspace = Path(env_workspace).resolve()
                logger.info(f"Using workspace from env var: {workspace}")
            else:
                # Default to {PROJECT_ROOT}/workspace
                root = self.get_project_root()
                workspace = root / "workspace"
                logger.debug(f"Using default workspace path: {workspace}")

            self._cache["workspace_path"] = workspace

        if create and not workspace.exists():
            workspace.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created workspace directory: {workspace}")

        return workspace

    def get_config_dir(self, create: bool = False) -> Path:
        """Get configuration directory path.

        Args:
            create: If True, create directory if it doesn't exist

        Returns:
            Path to config directory

        Examples:
            >>> resolver = PathResolver()
            >>> config = resolver.get_config_dir()
            >>> # Returns: {PROJECT_ROOT}/config
        """
        if "config_dir" in self._cache:
            config_dir = self._cache["config_dir"]
        else:
            # Check environment variable
            env_config = os.getenv("PARALLEL_CODING_CONFIG_DIR")
            if env_config:
                config_dir = Path(env_config).resolve()
                logger.info(f"Using config dir from env var: {config_dir}")
            else:
                # Default to {PROJECT_ROOT}/config
                root = self.get_project_root()
                config_dir = root / "config"
                logger.debug(f"Using default config dir: {config_dir}")

            self._cache["config_dir"] = config_dir

        if create and not config_dir.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created config directory: {config_dir}")

        return config_dir

    def get_logs_dir(self, create: bool = False) -> Path:
        """Get logs directory path.

        Args:
            create: If True, create directory if it doesn't exist

        Returns:
            Path to logs directory

        Examples:
            >>> resolver = PathResolver()
            >>> logs = resolver.get_logs_dir()
            >>> # Returns: {PROJECT_ROOT}/logs
        """
        if "logs_dir" in self._cache:
            logs_dir = self._cache["logs_dir"]
        else:
            # Check environment variable
            env_logs = os.getenv("PARALLEL_CODING_LOGS_DIR")
            if env_logs:
                logs_dir = Path(env_logs).resolve()
                logger.info(f"Using logs dir from env var: {logs_dir}")
            else:
                # Default to {PROJECT_ROOT}/logs
                root = self.get_project_root()
                logs_dir = root / "logs"
                logger.debug(f"Using default logs dir: {logs_dir}")

            self._cache["logs_dir"] = logs_dir

        if create and not logs_dir.exists():
            logs_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created logs directory: {logs_dir}")

        return logs_dir

    def get_cache_dir(self, create: bool = True) -> Path:
        """Get cache directory path.

        Args:
            create: If True, create directory if it doesn't exist

        Returns:
            Path to cache directory

        Examples:
            >>> resolver = PathResolver()
            >>> cache = resolver.get_cache_dir()
            >>> # Linux: Path("/home/user/.cache/parallel-coding")
            >>> # Windows: Path("C:/Users/user/AppData/Local/parallel-coding/cache")
        """
        if "cache_dir" in self._cache:
            cache_dir = self._cache["cache_dir"]
        else:
            # Check environment variable
            env_cache = os.getenv("PARALLEL_CODING_CACHE_DIR")
            if env_cache:
                cache_dir = Path(env_cache).resolve()
                logger.info(f"Using cache dir from env var: {cache_dir}")
            else:
                # Use platform-appropriate cache directory
                from orchestrator.config.defaults import get_user_cache_dir

                cache_dir = get_user_cache_dir()
                logger.debug(f"Using platform cache dir: {cache_dir}")

            self._cache["cache_dir"] = cache_dir

        if create and not cache_dir.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created cache directory: {cache_dir}")

        return cache_dir

    def get_parallel_coding_root(self) -> Path:
        """Get parallel-coding tool installation directory.

        Returns:
            Path to parallel-coding installation (where orchestrator/ is located)

        Examples:
            >>> resolver = PathResolver()
            >>> tool_root = resolver.get_parallel_coding_root()
            >>> # Returns: {PROJECT_ROOT}/dev-tools/parallel-coding (if submodule)
            >>> # Or: {PROJECT_ROOT} (if standalone)
        """
        if "tool_root" in self._cache:
            return self._cache["tool_root"]

        # This file is in orchestrator/utils/path_resolver.py
        # So parallel-coding root is 2 levels up
        tool_root = Path(__file__).resolve().parent.parent.parent
        logger.debug(f"Parallel-coding tool root: {tool_root}")
        self._cache["tool_root"] = tool_root
        return tool_root

    def resolve_path(self, path: str | Path, relative_to: Optional[Path] = None) -> Path:
        """Resolve a path, handling both absolute and relative paths.

        Args:
            path: Path to resolve
            relative_to: Base path for relative paths (default: project root)

        Returns:
            Resolved absolute Path

        Examples:
            >>> resolver = PathResolver()
            >>> # Absolute path
            >>> resolver.resolve_path("/tmp/test")
            Path('/tmp/test')
            >>> # Relative path
            >>> resolver.resolve_path("workspace/worker_1")
            Path('/home/user/project/workspace/worker_1')
        """
        path_obj = Path(path)

        # If already absolute, return as-is
        if path_obj.is_absolute():
            return path_obj.resolve()

        # Resolve relative to specified base or project root
        if relative_to is None:
            relative_to = self.get_project_root()

        return (relative_to / path_obj).resolve()

    def to_wsl_path(self, windows_path: Path) -> str:
        """Convert Windows path to WSL path format.

        Args:
            windows_path: Windows path to convert

        Returns:
            WSL-formatted path string

        Examples:
            >>> resolver = PathResolver()
            >>> wsl_path = resolver.to_wsl_path(Path("D:/user/project"))
            '/mnt/d/user/project'
        """
        import platform
        import re

        if platform.system() != "Windows":
            # Not on Windows, return as-is
            return str(windows_path)

        # Convert to string with forward slashes
        path_str = str(windows_path).replace("\\", "/")

        # Convert drive letter (C: -> /mnt/c)
        wsl_path = re.sub(r"^([A-Za-z]):", lambda m: f"/mnt/{m.group(1).lower()}", path_str)

        logger.debug(f"Converted Windows path {windows_path} to WSL path {wsl_path}")
        return wsl_path

    def clear_cache(self) -> None:
        """Clear path resolution cache to force re-detection."""
        self._cache.clear()
        logger.debug("Path resolver cache cleared")


# Global instance for convenience
_resolver: Optional[PathResolver] = None


def get_path_resolver() -> PathResolver:
    """Get global path resolver instance.

    Returns:
        Singleton PathResolver instance

    Examples:
        >>> from orchestrator.utils.path_resolver import get_path_resolver
        >>> resolver = get_path_resolver()
        >>> workspace = resolver.get_workspace_path()
    """
    global _resolver
    if _resolver is None:
        _resolver = PathResolver()
    return _resolver


# Convenience functions for common operations
def get_project_root() -> Path:
    """Get project root directory (convenience function)."""
    return get_path_resolver().get_project_root()


def get_workspace_path(create: bool = False) -> Path:
    """Get workspace directory path (convenience function)."""
    return get_path_resolver().get_workspace_path(create=create)


def get_config_dir(create: bool = False) -> Path:
    """Get config directory path (convenience function)."""
    return get_path_resolver().get_config_dir(create=create)


def get_logs_dir(create: bool = False) -> Path:
    """Get logs directory path (convenience function)."""
    return get_path_resolver().get_logs_dir(create=create)


def get_cache_dir(create: bool = True) -> Path:
    """Get cache directory path (convenience function)."""
    return get_path_resolver().get_cache_dir(create=create)
