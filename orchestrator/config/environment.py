"""Environment auto-detection for cross-project compatibility.

This module provides automatic detection of system dependencies, paths, and
configuration values to enable parallel-coding to work across different
projects and environments without manual configuration.

Part of Phase 1: Cross-Project Compatibility Initiative
See: ROADMAP_CROSS_PROJECT_COMPATIBILITY.md
"""

import os
import platform
import subprocess
from pathlib import Path
from typing import Optional

import logging

logger = logging.getLogger(__name__)


class EnvironmentDetector:
    """Auto-detect system configuration and dependencies."""

    def __init__(self) -> None:
        """Initialize environment detector with caching."""
        self._cache: dict[str, Optional[str | Path]] = {}

    def detect_wsl_distribution(self) -> Optional[str]:
        """Auto-detect WSL distribution name.

        Returns:
            WSL distribution name (e.g., "Ubuntu-24.04") or None if not on Windows/WSL

        Examples:
            >>> detector = EnvironmentDetector()
            >>> dist = detector.detect_wsl_distribution()
            >>> # On Windows with WSL: "Ubuntu-24.04"
            >>> # On Linux/macOS: None
        """
        if "wsl_distribution" in self._cache:
            return self._cache["wsl_distribution"]

        # Only applicable on Windows
        if platform.system() != "Windows":
            self._cache["wsl_distribution"] = None
            return None

        try:
            # Run wsl -l -v to list distributions
            result = subprocess.run(
                ["wsl", "-l", "-v"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            if result.returncode != 0:
                logger.debug("WSL not available or not installed")
                self._cache["wsl_distribution"] = None
                return None

            # Parse output to find default distribution
            lines = result.stdout.strip().split("\n")
            for line in lines[1:]:  # Skip header
                # Format: "* Ubuntu-24.04    Running         2"
                parts = line.strip().split()
                if parts and parts[0] == "*":
                    # Default distribution marked with *
                    dist_name = parts[1]
                    logger.info(f"Detected WSL distribution: {dist_name}")
                    self._cache["wsl_distribution"] = dist_name
                    return dist_name

            # If no default found, take first available
            if len(lines) > 1:
                parts = lines[1].strip().split()
                if len(parts) >= 2:
                    dist_name = parts[0] if parts[0] != "*" else parts[1]
                    logger.info(f"Using first WSL distribution: {dist_name}")
                    self._cache["wsl_distribution"] = dist_name
                    return dist_name

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.debug(f"WSL detection failed: {e}")

        self._cache["wsl_distribution"] = None
        return None

    def detect_nvm_path(self) -> Optional[Path]:
        """Auto-detect NVM (Node Version Manager) binary path.

        On Windows, checks WSL for NVM installation first (recommended for Codex).
        On Linux/macOS, checks local filesystem.

        Returns:
            Path to NVM's current Node.js bin directory, or None if not found

        Examples:
            >>> detector = EnvironmentDetector()
            >>> nvm_path = detector.detect_nvm_path()
            >>> # On Linux with NVM: Path("/home/user/.nvm/versions/node/v22.21.0/bin")
            >>> # On Windows with WSL NVM: Path("/home/user/.nvm/versions/node/v22.21.0/bin")
            >>> # Without NVM: None
        """
        if "nvm_path" in self._cache:
            return self._cache["nvm_path"]

        # Check NVM_DIR environment variable
        nvm_dir = os.getenv("NVM_DIR")
        if nvm_dir:
            nvm_bin = Path(nvm_dir) / "current" / "bin"
            if nvm_bin.exists():
                logger.info(f"Detected NVM path from NVM_DIR: {nvm_bin}")
                self._cache["nvm_path"] = nvm_bin
                return nvm_bin

        # On Windows, check WSL first (Codex official recommendation)
        if platform.system() == "Windows":
            wsl_nvm = self._detect_nvm_in_wsl()
            if wsl_nvm:
                logger.info(f"Detected NVM path in WSL: {wsl_nvm}")
                self._cache["nvm_path"] = wsl_nvm
                return wsl_nvm

        # Check common NVM installation paths (local filesystem)
        home = Path.home()
        common_paths = [
            home / ".nvm" / "current" / "bin",
            home / ".nvm" / "versions" / "node" / "current" / "bin",
        ]

        # Also check for specific versions if current symlink doesn't exist
        nvm_versions_dir = home / ".nvm" / "versions" / "node"
        if nvm_versions_dir.exists():
            # Get latest version
            versions = sorted(nvm_versions_dir.iterdir(), reverse=True)
            if versions:
                latest_bin = versions[0] / "bin"
                common_paths.insert(0, latest_bin)

        for path in common_paths:
            if path.exists():
                logger.info(f"Detected NVM path: {path}")
                self._cache["nvm_path"] = path
                return path

        logger.debug("NVM installation not detected")
        self._cache["nvm_path"] = None
        return None

    def _detect_nvm_in_wsl(self) -> Optional[Path]:
        """Detect NVM installation in WSL (Windows only).

        Returns:
            Path to NVM bin directory in WSL format, or None if not found
        """
        import subprocess

        wsl_dist = self.detect_wsl_distribution() or "Ubuntu-24.04"

        # Common NVM paths in WSL
        nvm_check_commands = [
            # Check for latest version in versions directory
            "ls -1d $HOME/.nvm/versions/node/v*/bin 2>/dev/null | sort -V | tail -1",
            # Check for current symlink
            "readlink -f $HOME/.nvm/current/bin 2>/dev/null",
        ]

        for check_cmd in nvm_check_commands:
            try:
                result = subprocess.run(
                    ["wsl", "-d", wsl_dist, "bash", "-c", check_cmd],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                nvm_path = result.stdout.strip()
                if nvm_path and "/bin" in nvm_path:
                    # Verify the path exists in WSL
                    verify_result = subprocess.run(
                        ["wsl", "-d", wsl_dist, "bash", "-c", f"test -d '{nvm_path}' && echo found"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=False,
                    )
                    if verify_result.stdout.strip() == "found":
                        return Path(nvm_path)
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
                logger.debug(f"WSL NVM check failed: {e}")
                continue

        return None

    def detect_git_bash_path(self) -> Optional[Path]:
        """Auto-detect Git Bash executable path (Windows only).

        Returns:
            Path to bash.exe from Git for Windows, or None if not found

        Examples:
            >>> detector = EnvironmentDetector()
            >>> git_bash = detector.detect_git_bash_path()
            >>> # On Windows: Path("C:/Program Files/Git/bin/bash.exe")
            >>> # On Linux/macOS: None
        """
        if "git_bash_path" in self._cache:
            return self._cache["git_bash_path"]

        # Only applicable on Windows
        if platform.system() != "Windows":
            self._cache["git_bash_path"] = None
            return None

        # Check common Git for Windows installation paths
        common_paths = [
            Path("C:/Program Files/Git/bin/bash.exe"),
            Path("C:/Program Files (x86)/Git/bin/bash.exe"),
            Path(os.getenv("ProgramFiles", "C:/Program Files")) / "Git" / "bin" / "bash.exe",
        ]

        for path in common_paths:
            if path.exists():
                logger.info(f"Detected Git Bash: {path}")
                self._cache["git_bash_path"] = path
                return path

        # Try using 'where' command
        try:
            result = subprocess.run(
                ["where", "bash"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                bash_path = Path(result.stdout.strip().split("\n")[0])
                if "Git" in str(bash_path):
                    logger.info(f"Detected Git Bash via 'where': {bash_path}")
                    self._cache["git_bash_path"] = bash_path
                    return bash_path
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.debug(f"Git Bash detection via 'where' failed: {e}")

        logger.debug("Git Bash not detected")
        self._cache["git_bash_path"] = None
        return None

    def detect_python_executable(self) -> Path:
        """Detect current Python executable path.

        Returns:
            Path to Python executable currently running this code

        Examples:
            >>> detector = EnvironmentDetector()
            >>> python_path = detector.detect_python_executable()
            >>> # Path("/usr/bin/python3.11") or similar
        """
        import sys

        return Path(sys.executable)

    def get_platform_info(self) -> dict[str, str]:
        """Get comprehensive platform information.

        Returns:
            Dictionary containing platform details

        Examples:
            >>> detector = EnvironmentDetector()
            >>> info = detector.get_platform_info()
            >>> info["system"]  # "Windows", "Linux", or "Darwin"
            >>> info["machine"]  # "x86_64", "AMD64", etc.
        """
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }

    def is_wsl_environment(self) -> bool:
        """Check if currently running inside WSL (not Windows calling WSL).

        Returns:
            True if running inside WSL, False otherwise

        Examples:
            >>> detector = EnvironmentDetector()
            >>> detector.is_wsl_environment()
            >>> # True if in WSL, False if in Windows or native Linux
        """
        if platform.system() != "Linux":
            return False

        # Check for WSL-specific indicators
        try:
            # WSL has Microsoft in /proc/version
            with open("/proc/version", encoding="utf-8") as f:
                version_info = f.read().lower()
                return "microsoft" in version_info or "wsl" in version_info
        except (FileNotFoundError, Exception):
            return False

    def clear_cache(self) -> None:
        """Clear detection cache to force re-detection."""
        self._cache.clear()
        logger.debug("Environment detection cache cleared")


# Global instance for convenience
_detector: Optional[EnvironmentDetector] = None


def get_environment_detector() -> EnvironmentDetector:
    """Get global environment detector instance.

    Returns:
        Singleton EnvironmentDetector instance

    Examples:
        >>> from orchestrator.config.environment import get_environment_detector
        >>> detector = get_environment_detector()
        >>> wsl_dist = detector.detect_wsl_distribution()
    """
    global _detector
    if _detector is None:
        _detector = EnvironmentDetector()
    return _detector
