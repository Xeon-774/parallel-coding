"""
Web UI Dashboard for Claude Orchestrator

Provides a FastAPI-based web dashboard for monitoring and managing
parallel AI execution.
"""

from .config import DashboardConfig, DependencyConfig
from .constants import HelpText, Messages, Separators
from .dashboard_manager import DashboardManager
from .dependencies import DependencyManager
from .exceptions import (
    ConfigurationError,
    DashboardError,
    DashboardStartupError,
    DashboardTimeoutError,
    DependencyError,
    OrchestratorError,
)
from .orchestrator_runner import OrchestratorRunner

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
