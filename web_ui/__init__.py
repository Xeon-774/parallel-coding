"""
Web UI Dashboard for Claude Orchestrator

Provides a FastAPI-based web dashboard for monitoring and managing
parallel AI execution.
"""

from .config import DashboardConfig, DependencyConfig
from .dependencies import DependencyManager
from .dashboard_manager import DashboardManager
from .orchestrator_runner import OrchestratorRunner
from .exceptions import (
    DashboardError,
    DependencyError,
    DashboardStartupError,
    DashboardTimeoutError,
    ConfigurationError,
    OrchestratorError,
)
from .constants import Messages, Separators, HelpText

__version__ = "5.0.0"

__all__ = [
    # Configuration
    "DashboardConfig",
    "DependencyConfig",
    # Managers
    "DependencyManager",
    "DashboardManager",
    "OrchestratorRunner",
    # Exceptions
    "DashboardError",
    "DependencyError",
    "DashboardStartupError",
    "DashboardTimeoutError",
    "ConfigurationError",
    "OrchestratorError",
    # Constants
    "Messages",
    "Separators",
    "HelpText",
]
