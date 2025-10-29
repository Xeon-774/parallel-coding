"""
Dependency management for Web UI Dashboard

Handles checking and installing required packages.
"""

import subprocess
import sys
from typing import Optional, Tuple

from .config import DependencyConfig
from .constants import Messages, Separators
from .exceptions import DependencyError


class DependencyManager:
    """Manages web UI dependencies"""

    def __init__(self, config: Optional[DependencyConfig] = None):
        """
        Initialize the dependency manager.

        Args:
            config: Dependency configuration. If None, uses default.
        """
        self.config = config or DependencyConfig()

    def check(self) -> bool:
        """
        Check if all required dependencies are installed.

        Returns:
            True if all dependencies are available, False otherwise.
        """
        try:
            import fastapi
            import uvicorn
            import websockets

            return True
        except ImportError:
            return False

    def install(self) -> bool:
        """
        Install all required dependencies.

        Returns:
            True if installation succeeded, False otherwise.

        Raises:
            DependencyError: If installation fails critically.
        """
        print("Installing: fastapi, uvicorn, websockets, aiofiles, requests")
        print()

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install"] + list(self.config.required_packages),
                capture_output=True,
                text=True,
                timeout=self.config.install_timeout,
            )

            if result.returncode == 0:
                print(f"{Messages.PREFIX_OK} {Messages.DEPENDENCY_INSTALL_SUCCESS}")
                print()
                print(Separators.LINE_70)
                print()

                # Verify installation
                if self.check():
                    return True
                else:
                    print(f"{Messages.PREFIX_ERROR} {Messages.ERROR_INSTALL_VERIFY}")
                    print(f"   {Messages.ERROR_RESTART_NEEDED}")
                    return False
            else:
                print(f"{Messages.PREFIX_ERROR} {Messages.DEPENDENCY_INSTALL_FAILED}")
                print()
                print("Error output:")
                print(result.stderr[:500])
                print()
                print(Messages.DEPENDENCY_MANUAL_INSTALL)
                print()
                return False

        except subprocess.TimeoutExpired:
            raise DependencyError(Messages.ERROR_TIMEOUT)
        except Exception as e:
            raise DependencyError(f"Installation error: {e}")

    def check_and_install(self, auto_install: bool = True) -> bool:
        """
        Check dependencies and optionally install if missing.

        Args:
            auto_install: If True, automatically install missing dependencies.

        Returns:
            True if dependencies are available, False otherwise.
        """
        if self.check():
            return True

        # Dependencies are missing
        print()
        print(Separators.LINE_70)
        print(f"  {Messages.PREFIX_WARNING} {Messages.DEPENDENCY_CHECK_FAILED}")
        print(Separators.LINE_70)
        print()

        if auto_install:
            print(f"{Messages.PREFIX_INSTALL} {Messages.DEPENDENCY_INSTALLING}")
            print()
            return self.install()
        else:
            print("The Web Dashboard requires additional packages.")
            print(Messages.DEPENDENCY_MANUAL_INSTALL)
            print()
            print(Separators.LINE_70)
            print()
            return False
