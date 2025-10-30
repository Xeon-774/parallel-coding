"""Binary discovery utilities for cross-project compatibility.

This module provides automatic discovery of required binaries (codex, claude,
git, etc.) using intelligent search across common installation locations.

Part of Phase 1: Cross-Project Compatibility Initiative
See: ROADMAP_CROSS_PROJECT_COMPATIBILITY.md, DEVELOPMENT_POLICY.md
"""

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from orchestrator.config.defaults import (
    BINARY_CACHE_TTL,
    BINARY_SEARCH_TIMEOUT,
    INSTALLATION_URLS,
    get_npm_global_paths,
)
import logging

logger = logging.getLogger(__name__)


class BinaryNotFoundError(Exception):
    """Raised when a required binary cannot be found."""

    pass


class BinaryDiscovery:
    """Auto-discover system binaries and CLI tools."""

    def __init__(self) -> None:
        """Initialize binary discovery with caching."""
        self._cache: dict[str, Optional[Path]] = {}
        self._cache_timestamps: dict[str, float] = {}

    def _is_cache_valid(self, binary_name: str) -> bool:
        """Check if cached binary path is still valid.

        Args:
            binary_name: Name of binary to check

        Returns:
            True if cache is valid, False otherwise
        """
        import time

        if binary_name not in self._cache:
            return False

        # Check if cache has expired
        cache_time = self._cache_timestamps.get(binary_name, 0)
        if time.time() - cache_time > BINARY_CACHE_TTL:
            return False

        # Check if cached path still exists
        cached_path = self._cache[binary_name]
        if cached_path and not cached_path.exists():
            return False

        return True

    def _update_cache(self, binary_name: str, path: Optional[Path]) -> None:
        """Update cache with discovered binary path.

        Args:
            binary_name: Name of binary
            path: Discovered path or None
        """
        import time

        self._cache[binary_name] = path
        self._cache_timestamps[binary_name] = time.time()

    def find_codex(self, required: bool = False) -> Optional[Path]:
        """Find Codex CLI installation.

        Searches in order:
        1. PARALLEL_CODING_CODEX_PATH environment variable
        2. System PATH
        3. npm global install locations
        4. WSL-mounted Windows npm (if on Windows)

        Args:
            required: If True, raise error if not found

        Returns:
            Path to codex binary or None if not found

        Raises:
            BinaryNotFoundError: If required=True and binary not found

        Examples:
            >>> discovery = BinaryDiscovery()
            >>> codex = discovery.find_codex()
            >>> # Found: Path("/usr/local/bin/codex")
            >>> # Not found: None
        """
        if self._is_cache_valid("codex"):
            return self._cache["codex"]

        # Check environment variable first
        env_path = os.getenv("PARALLEL_CODING_CODEX_PATH")
        if env_path:
            codex_path = Path(env_path)
            if codex_path.exists():
                logger.info(f"Found Codex CLI from env var: {codex_path}")
                self._update_cache("codex", codex_path)
                return codex_path

        # Check system PATH
        codex_which = shutil.which("codex")
        if codex_which:
            codex_path = Path(codex_which)
            logger.info(f"Found Codex CLI in PATH: {codex_path}")
            self._update_cache("codex", codex_path)
            return codex_path

        # Check npm global install locations
        for npm_path in get_npm_global_paths():
            codex_path = npm_path / "codex"
            if platform.system() == "Windows":
                codex_path = npm_path / "codex.cmd"

            if codex_path.exists():
                logger.info(f"Found Codex CLI in npm global: {codex_path}")
                self._update_cache("codex", codex_path)
                return codex_path

        # On Windows, check WSL-mounted paths
        if platform.system() == "Windows":
            wsl_npm_paths = [
                Path("/mnt/c/Users")
                / os.getenv("USERNAME", "user")
                / "AppData"
                / "Roaming"
                / "npm"
                / "codex",
                Path("/mnt/c/Program Files/nodejs/codex"),
            ]
            for wsl_path in wsl_npm_paths:
                # Note: Can't directly check WSL paths from Windows
                # These would be used when building WSL commands
                pass

        if required:
            error_msg = (
                "Codex CLI not found.\n\n"
                "Installation options:\n"
                "  1. Install globally: npm install -g @openai/codex\n"
                "  2. Set environment variable: PARALLEL_CODING_CODEX_PATH=/path/to/codex\n"
                "  3. Add to .env file: PARALLEL_CODING_CODEX_PATH=/path/to/codex\n\n"
                f"For more help, see: {INSTALLATION_URLS.get('codex', 'https://openai.com/codex')}"
            )
            raise BinaryNotFoundError(error_msg)

        logger.debug("Codex CLI not found")
        self._update_cache("codex", None)
        return None

    def find_claude(self, required: bool = False) -> Optional[Path]:
        """Find Claude CLI installation.

        Searches in order:
        1. PARALLEL_CODING_CLAUDE_PATH environment variable
        2. System PATH
        3. pip install locations (~/.local/bin, etc.)

        Args:
            required: If True, raise error if not found

        Returns:
            Path to claude binary or None if not found

        Raises:
            BinaryNotFoundError: If required=True and binary not found

        Examples:
            >>> discovery = BinaryDiscovery()
            >>> claude = discovery.find_claude()
            >>> # Found: Path("/home/user/.local/bin/claude")
            >>> # Not found: None
        """
        if self._is_cache_valid("claude"):
            return self._cache["claude"]

        # Check environment variable first
        env_path = os.getenv("PARALLEL_CODING_CLAUDE_PATH")
        if env_path:
            claude_path = Path(env_path)
            if claude_path.exists():
                logger.info(f"Found Claude CLI from env var: {claude_path}")
                self._update_cache("claude", claude_path)
                return claude_path

        # Check system PATH
        claude_which = shutil.which("claude")
        if claude_which:
            claude_path = Path(claude_which)
            logger.info(f"Found Claude CLI in PATH: {claude_path}")
            self._update_cache("claude", claude_path)
            return claude_path

        # Check common pip install locations
        pip_paths = [
            Path.home() / ".local" / "bin" / "claude",
            Path("/usr/local/bin/claude"),
            Path("/usr/bin/claude"),
        ]

        if platform.system() == "Windows":
            pip_paths.extend(
                [
                    Path.home()
                    / "AppData"
                    / "Local"
                    / "Programs"
                    / "Python"
                    / "Scripts"
                    / "claude.exe",
                    Path.home() / "AppData" / "Roaming" / "Python" / "Scripts" / "claude.exe",
                ]
            )

        for claude_path in pip_paths:
            if claude_path.exists():
                logger.info(f"Found Claude CLI: {claude_path}")
                self._update_cache("claude", claude_path)
                return claude_path

        if required:
            error_msg = (
                "Claude CLI not found.\n\n"
                "Installation options:\n"
                "  1. Install with pip: pip install anthropic-claude-cli\n"
                "  2. Set environment variable: PARALLEL_CODING_CLAUDE_PATH=/path/to/claude\n"
                "  3. Add to .env file: PARALLEL_CODING_CLAUDE_PATH=/path/to/claude\n\n"
                f"For more help, see: {INSTALLATION_URLS.get('claude', 'https://anthropic.com/claude')}"
            )
            raise BinaryNotFoundError(error_msg)

        logger.debug("Claude CLI not found")
        self._update_cache("claude", None)
        return None

    def find_git(self, required: bool = False) -> Optional[Path]:
        """Find Git binary.

        Searches in order:
        1. System PATH
        2. Common installation locations

        Args:
            required: If True, raise error if not found

        Returns:
            Path to git binary or None if not found

        Raises:
            BinaryNotFoundError: If required=True and binary not found

        Examples:
            >>> discovery = BinaryDiscovery()
            >>> git = discovery.find_git()
            >>> # Found: Path("/usr/bin/git")
            >>> # Not found: None
        """
        if self._is_cache_valid("git"):
            return self._cache["git"]

        # Check system PATH
        git_which = shutil.which("git")
        if git_which:
            git_path = Path(git_which)
            logger.info(f"Found Git in PATH: {git_path}")
            self._update_cache("git", git_path)
            return git_path

        # Check common locations
        common_paths = [
            Path("/usr/bin/git"),
            Path("/usr/local/bin/git"),
        ]

        if platform.system() == "Windows":
            common_paths.extend(
                [
                    Path("C:/Program Files/Git/cmd/git.exe"),
                    Path("C:/Program Files (x86)/Git/cmd/git.exe"),
                ]
            )

        for git_path in common_paths:
            if git_path.exists():
                logger.info(f"Found Git: {git_path}")
                self._update_cache("git", git_path)
                return git_path

        if required:
            error_msg = (
                "Git not found.\n\n"
                "Installation options:\n"
                "  1. Install from: https://git-scm.com/downloads\n"
                "  2. Install via package manager:\n"
                "     - Ubuntu/Debian: sudo apt-get install git\n"
                "     - macOS: brew install git\n"
                "     - Windows: Download from git-scm.com\n\n"
                f"For more help, see: {INSTALLATION_URLS.get('git', 'https://git-scm.com')}"
            )
            raise BinaryNotFoundError(error_msg)

        logger.debug("Git not found")
        self._update_cache("git", None)
        return None

    def find_python(self) -> Path:
        """Find Python executable.

        Returns:
            Path to current Python interpreter

        Examples:
            >>> discovery = BinaryDiscovery()
            >>> python = discovery.find_python()
            >>> # Path("/usr/bin/python3.11")
        """
        import sys

        python_path = Path(sys.executable)
        logger.debug(f"Using Python: {python_path}")
        return python_path

    def detect_wsl_distribution(self) -> Optional[str]:
        """Detect WSL distribution name (Windows only).

        Returns:
            WSL distribution name or None if not on Windows/WSL not available

        Examples:
            >>> discovery = BinaryDiscovery()
            >>> wsl_dist = discovery.detect_wsl_distribution()
            >>> # On Windows with WSL: "Ubuntu-24.04"
            >>> # On Linux/macOS: None
        """
        from orchestrator.config.environment import get_environment_detector

        detector = get_environment_detector()
        return detector.detect_wsl_distribution()

    def detect_nvm_path(self) -> Optional[Path]:
        """Detect NVM binary path.

        Returns:
            Path to NVM's current Node.js bin directory, or None if not found

        Examples:
            >>> discovery = BinaryDiscovery()
            >>> nvm_path = discovery.detect_nvm_path()
            >>> # Found: Path("/home/user/.nvm/versions/node/v22.21.0/bin")
            >>> # Not found: None
        """
        from orchestrator.config.environment import get_environment_detector

        detector = get_environment_detector()
        return detector.detect_nvm_path()

    def verify_binary(self, binary_path: Path, binary_name: str) -> bool:
        """Verify that a binary is executable and working.

        Args:
            binary_path: Path to binary
            binary_name: Name of binary (for logging)

        Returns:
            True if binary is executable and responds to --version, False otherwise

        Examples:
            >>> discovery = BinaryDiscovery()
            >>> git_path = Path("/usr/bin/git")
            >>> discovery.verify_binary(git_path, "git")
            True
        """
        if not binary_path.exists():
            logger.warning(f"{binary_name} not found at: {binary_path}")
            return False

        # Check if executable (Unix-like systems)
        if platform.system() != "Windows":
            if not os.access(binary_path, os.X_OK):
                logger.warning(f"{binary_name} is not executable: {binary_path}")
                return False

        # Try to run --version command
        try:
            result = subprocess.run(
                [str(binary_path), "--version"],
                capture_output=True,
                timeout=BINARY_SEARCH_TIMEOUT,
                check=False,
            )
            if result.returncode == 0:
                logger.debug(f"{binary_name} is working: {binary_path}")
                return True
            else:
                logger.warning(f"{binary_name} --version failed: {binary_path}")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.warning(f"{binary_name} verification failed: {e}")
            return False

    def get_binary_info(self, binary_path: Path) -> dict[str, str]:
        """Get version information about a binary.

        Args:
            binary_path: Path to binary

        Returns:
            Dictionary with version info

        Examples:
            >>> discovery = BinaryDiscovery()
            >>> info = discovery.get_binary_info(Path("/usr/bin/git"))
            >>> info["version"]  # "2.34.1"
        """
        try:
            result = subprocess.run(
                [str(binary_path), "--version"],
                capture_output=True,
                text=True,
                timeout=BINARY_SEARCH_TIMEOUT,
                check=False,
            )
            if result.returncode == 0:
                version_output = result.stdout.strip()
                return {
                    "path": str(binary_path),
                    "version": version_output,
                    "exists": True,
                    "executable": True,
                }
        except Exception as e:
            logger.debug(f"Failed to get binary info: {e}")

        return {
            "path": str(binary_path),
            "version": "unknown",
            "exists": binary_path.exists(),
            "executable": False,
        }

    def clear_cache(self) -> None:
        """Clear binary discovery cache to force re-detection."""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.debug("Binary discovery cache cleared")


# Global instance for convenience
_discovery: Optional[BinaryDiscovery] = None


def get_binary_discovery() -> BinaryDiscovery:
    """Get global binary discovery instance.

    Returns:
        Singleton BinaryDiscovery instance

    Examples:
        >>> from orchestrator.utils.binary_discovery import get_binary_discovery
        >>> discovery = get_binary_discovery()
        >>> codex = discovery.find_codex()
    """
    global _discovery
    if _discovery is None:
        _discovery = BinaryDiscovery()
    return _discovery


# Convenience functions for common operations
def find_codex(required: bool = False) -> Optional[Path]:
    """Find Codex CLI (convenience function)."""
    return get_binary_discovery().find_codex(required=required)


def find_claude(required: bool = False) -> Optional[Path]:
    """Find Claude CLI (convenience function)."""
    return get_binary_discovery().find_claude(required=required)


def find_git(required: bool = False) -> Optional[Path]:
    """Find Git binary (convenience function)."""
    return get_binary_discovery().find_git(required=required)
