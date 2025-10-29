#!/usr/bin/env python
"""
Claude Orchestrator integrated launcher script

Automatically starts the web dashboard and orchestrator,
and opens the browser.
"""

import argparse
import sys
import time
from pathlib import Path

# Add project root to PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from web_ui import (
    DashboardConfig,
    DashboardManager,
    DependencyConfig,
    DependencyManager,
    HelpText,
    Messages,
    OrchestratorRunner,
    Separators,
)


class IntegratedLauncher:
    """Integrated launcher for dashboard and orchestrator"""

    def __init__(self, dashboard_config: DashboardConfig, dependency_config: DependencyConfig):
        """
        Initialize the integrated launcher.

        Args:
            dashboard_config: Dashboard configuration
            dependency_config: Dependency configuration
        """
        self.dashboard_config = dashboard_config
        self.dependency_config = dependency_config

        # Initialize managers
        self.dependency_manager = DependencyManager(dependency_config)
        self.dashboard_manager = DashboardManager(dashboard_config)
        self.orchestrator_runner = OrchestratorRunner(dashboard_config)

    def run(self, user_request: str) -> int:
        """
        Run the complete orchestration workflow.

        Args:
            user_request: Task description from user

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        # Step 1: Check and install dependencies
        if not self.dependency_manager.check_and_install(
            auto_install=self.dependency_config.auto_install
        ):
            print("Proceeding without Web Dashboard...")
            print()
            return self.orchestrator_runner.run(user_request)

        try:
            # Step 2: Start dashboard
            if not self.dashboard_manager.start():
                print()
                print(f"{Messages.PREFIX_WARNING} {Messages.ORCHESTRATOR_CONTINUING}")
                print()

            # Step 3: Open browser
            time.sleep(2)  # Wait for dashboard to fully initialize
            self.dashboard_manager.open_browser()

            # Step 4: Run orchestrator
            time.sleep(1)  # Brief pause before orchestrator
            return_code = self.orchestrator_runner.run(user_request)

            # Step 5: Show completion message
            self.orchestrator_runner.show_completion_message()

            # Step 6: Wait for user input before cleanup
            try:
                input(Messages.COMPLETION_PROMPT)
            except (KeyboardInterrupt, EOFError):
                pass

            return return_code

        finally:
            # Always cleanup
            self.dashboard_manager.stop()


def main() -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Claude Orchestrator with Web Dashboard - All-in-One Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=HelpText.EPILOG,
    )

    parser.add_argument("request", nargs="?", help="Task description (interactive if omitted)")

    parser.add_argument("--host", default="127.0.0.1", help="Dashboard host (default: 127.0.0.1)")

    parser.add_argument("--port", type=int, default=8000, help="Dashboard port (default: 8000)")

    parser.add_argument(
        "--no-browser", action="store_true", help="Do not automatically open browser"
    )

    parser.add_argument(
        "--no-auto-install",
        action="store_true",
        help="Do not automatically install missing dependencies",
    )

    args = parser.parse_args()

    # Get or prompt for user request
    user_request = args.request
    if not user_request:
        print(Separators.LINE_70)
        print(f"  {Messages.PREFIX_AI} {HelpText.INTERACTIVE_MODE_HEADER}")
        print(Separators.LINE_70)
        print()
        print("Please enter your task request:")
        print("(Examples: 'Create a Todo app', 'Build a calculator', etc.)")
        print()
        try:
            user_request = input("Your request: ").strip()
            if not user_request:
                print(f"{Messages.PREFIX_ERROR} {Messages.ERROR_NO_REQUEST}")
                return 1
        except (KeyboardInterrupt, EOFError):
            print(f"\n{Messages.PREFIX_WARNING} {Messages.ERROR_CANCELLED}")
            return 1

    # Create configurations
    dashboard_config = DashboardConfig(
        host=args.host, port=args.port, auto_open_browser=not args.no_browser
    )
    dependency_config = DependencyConfig(auto_install=not args.no_auto_install)

    # Create and run launcher
    launcher = IntegratedLauncher(dashboard_config, dependency_config)

    try:
        return launcher.run(user_request)
    except KeyboardInterrupt:
        print(f"\n\n{Messages.PREFIX_WARNING} {Messages.ERROR_INTERRUPTED}")
        launcher.dashboard_manager.stop()
        return 1


if __name__ == "__main__":
    sys.exit(main())
