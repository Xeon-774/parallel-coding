"""
Text constants for Web UI Dashboard

Centralizes all user - facing text for easier maintenance and i18n support.
All strings are ASCII - safe to avoid Unicode encoding issues on Windows cp932.
"""


class Messages:
    """User - facing messages"""

    # Prefixes (ASCII - safe, no emoji)
    PREFIX_WEB = "[WEB]"
    PREFIX_AI = "[AI]"
    PREFIX_OK = "[OK]"
    PREFIX_ERROR = "[ERROR]"
    PREFIX_INSTALL = "[INSTALL]"
    PREFIX_WARNING = "[!]"

    # Dependency checking
    DEPENDENCY_CHECK_FAILED = "Web UI Dependencies Not Installed"
    DEPENDENCY_INSTALLING = "Attempting to install dependencies automatically..."
    DEPENDENCY_INSTALL_SUCCESS = "Dependencies installed successfully!"
    DEPENDENCY_INSTALL_FAILED = "Installation failed"
    DEPENDENCY_MANUAL_INSTALL = (
        "Please install them with:\n"
        '    pip install -e ".[web]"\n\n'
        "Or install packages individually:\n"
        "    pip install fastapi uvicorn websockets aiofiles requests"
    )

    # Dashboard startup
    DASHBOARD_STARTING = "Starting Web Dashboard..."
    DASHBOARD_WAITING = "Waiting for dashboard to start..."
    DASHBOARD_READY = "Dashboard is ready at"
    DASHBOARD_FAILED = "Dashboard may not have started correctly"
    DASHBOARD_CRASHED = "Dashboard process crashed!"
    DASHBOARD_STOPPING = "Stopping Web Dashboard..."
    DASHBOARD_STOPPED = "Dashboard stopped"
    DASHBOARD_KILLED = "Dashboard killed"

    # Browser
    BROWSER_OPENING = "Opening browser..."
    BROWSER_OPENED = "Browser opened successfully"
    BROWSER_FAILED = "Could not open browser"
    BROWSER_MANUAL = "Please manually open:"

    # Orchestrator
    ORCHESTRATOR_TITLE = "Claude Orchestrator"
    ORCHESTRATOR_COMPLETED = "Orchestrator completed"
    ORCHESTRATOR_CONTINUING = "Dashboard may not be running, but continuing..."

    # Completion
    COMPLETION_MESSAGE = (
        "Dashboard is still running at: {url}\n"
        "You can:\n"
        "  - Review the results in the browser\n"
        "  - Run another task while keeping the dashboard open\n"
        "  - Press Ctrl + C to stop the dashboard and exit"
    )
    COMPLETION_PROMPT = "Press Enter to stop the dashboard and exit..."

    # Errors
    ERROR_NO_REQUEST = "No request provided. Exiting."
    ERROR_CANCELLED = "Cancelled by user"
    ERROR_INTERRUPTED = "Interrupted by user"
    ERROR_TIMEOUT = "Installation timeout (took more than 5 minutes)"
    ERROR_INSTALL_VERIFY = "Installation succeeded but imports still failing"
    ERROR_RESTART_NEEDED = "Please restart the script"


class Separators:
    """Visual separators"""

    LINE_70 = "=" * 70
    LINE_62 = "=" * 62
    LINE_80 = "=" * 80

    @staticmethod
    def box(title: str, width: int = 70) -> str:
        """Create a boxed title"""
        return f"{Separators.LINE_70}\n  {title}\n{Separators.LINE_70}"


class HelpText:
    """Help and usage text"""

    EPILOG = """
Usage examples:
  # Default startup (interactive task input)
  python run_with_dashboard.py

  # Specify task directly
  python run_with_dashboard.py "Create a Todo app"

  # Custom port
  python run_with_dashboard.py --port 3000 "Calculator app"

  # Don't auto - open browser
  python run_with_dashboard.py --no - browser "Password generator"
"""

    INTERACTIVE_MODE_HEADER = (
        "Claude Orchestrator - Interactive Mode\n"
        "\n"
        "Please enter your task request:\n"
        "(Examples: 'Create a Todo app', 'Build a calculator', etc.)"
    )
