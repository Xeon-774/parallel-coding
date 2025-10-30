"""
Dashboard process management for Web UI

Handles starting, monitoring, and stopping the dashboard server.
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Optional

from .config import DashboardConfig
from .constants import Messages


class DashboardManager:
    """Manages the web dashboard server process"""

    def __init__(self, config: Optional[DashboardConfig] = None):
        """
        Initialize the dashboard manager.

        Args:
            config: Dashboard configuration. If None, uses defaults.
        """
        self.config = config or DashboardConfig()
        self.process: Optional[subprocess.Popen] = None
        self.project_root = Path(__file__).parent.parent

    def start(self) -> bool:
        """
        Start the dashboard server in the background.

        Returns:
            True if dashboard started successfully, False otherwise.

        Raises:
            DashboardStartupError: If dashboard fails to start.
        """
        print(f"{Messages.PREFIX_WEB} {Messages.DASHBOARD_STARTING}")
        print(f"      URL: {self.config.dashboard_url}")

        # Start dashboard in background
        self.process = subprocess.Popen(
            [
                sys.executable,
                "start_dashboard.py",
                "--host",
                self.config.host,
                "--port",
                str(self.config.port),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(self.project_root),
            text=True,
        )

        # Wait for dashboard to start
        print(f"   {Messages.DASHBOARD_WAITING}", end="", flush=True)

        for i in range(self.config.startup_timeout):
            time.sleep(self.config.health_check_interval)

            # Check if process crashed
            if self.process.poll() is not None:
                print(f" [{Messages.PREFIX_ERROR}]")
                print()
                print(f"   {Messages.DASHBOARD_CRASHED}")
                print()

                # Show error output
                if self.process.stderr:
                    stderr = self.process.stderr.read()
                    if stderr:
                        print("   Error output:")
                        for line in stderr.split("\n")[:10]:
                            if line.strip():
                                print(f"     {line}")
                        print()

                print("   Please check if dependencies are installed:")
                print('     pip install -e ".[web]"')
                print()
                return False

            # Try health check
            try:
                import requests

                response = requests.get(f"{self.config.dashboard_url}/api / status", timeout=1)
                if response.status_code == 200:
                    print(f" [{Messages.PREFIX_OK}]")
                    print(f"      {Messages.DASHBOARD_READY} {self.config.dashboard_url}")
                    return True
            except Exception:

                print(".", end="", flush=True)

        # Timeout
        print(f" [{Messages.PREFIX_ERROR}]")
        print(f"      Warning: {Messages.DASHBOARD_FAILED}")
        return False

    def open_browser(self) -> None:
        """Open the dashboard in the default web browser."""
        if not self.config.auto_open_browser:
            return

        print(f"{Messages.PREFIX_WEB} {Messages.BROWSER_OPENING}")
        try:
            webbrowser.open(self.config.dashboard_url)
            print(f"   {Messages.BROWSER_OPENED}")
        except Exception as e:
            print(f"   {Messages.BROWSER_FAILED}: {e}")
            print(f"   {Messages.BROWSER_MANUAL}: {self.config.dashboard_url}")

    def stop(self) -> None:
        """Stop the dashboard server process."""
        if not self.process:
            return

        print()
        print(f"{Messages.PREFIX_WEB} {Messages.DASHBOARD_STOPPING}")

        try:
            self.process.terminate()
            self.process.wait(timeout=5)
            print(f"   {Messages.DASHBOARD_STOPPED}")
        except subprocess.TimeoutExpired:
            try:
                self.process.kill()
                print(f"   {Messages.DASHBOARD_KILLED}")
            except Exception:

                pass
        except Exception:

            pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup."""
        self.stop()
