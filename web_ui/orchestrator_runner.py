"""
Orchestrator execution management

Handles running the orchestrator and displaying results.
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional

from .config import DashboardConfig
from .exceptions import OrchestratorError
from .constants import Messages, Separators


class OrchestratorRunner:
    """Manages orchestrator execution"""

    def __init__(self, config: Optional[DashboardConfig] = None):
        """
        Initialize the orchestrator runner.

        Args:
            config: Dashboard configuration for display. If None, uses defaults.
        """
        self.config = config or DashboardConfig()
        self.project_root = Path(__file__).parent.parent

    def run(self, user_request: str) -> int:
        """
        Execute the orchestrator with a user request.

        Args:
            user_request: The task description from the user.

        Returns:
            Exit code from the orchestrator process.

        Raises:
            OrchestratorError: If execution fails critically.
        """
        print()
        print(Separators.LINE_70)
        print(f"  {Messages.PREFIX_AI} {Messages.ORCHESTRATOR_TITLE}")
        print(Separators.LINE_70)
        print()
        print(f"Request: {user_request}")
        print()
        print(f"Dashboard: {self.config.dashboard_url}")
        print()
        print(Separators.LINE_70)
        print()

        # Run orchestrator
        try:
            result = subprocess.run(
                [sys.executable, "orchestrator/main.py", user_request],
                cwd=str(self.project_root)
            )
            return result.returncode

        except KeyboardInterrupt:
            print(f"\n\n{Messages.PREFIX_WARNING} {Messages.ERROR_INTERRUPTED}")
            return 1
        except Exception as e:
            raise OrchestratorError(f"Orchestrator execution failed: {e}")

    def show_completion_message(self) -> None:
        """Display completion message and instructions."""
        print()
        print(Separators.LINE_70)
        print(f"  {Messages.PREFIX_OK} {Messages.ORCHESTRATOR_COMPLETED}")
        print(Separators.LINE_70)
        print()
        print(Messages.COMPLETION_MESSAGE.format(url=self.config.dashboard_url))
        print()
