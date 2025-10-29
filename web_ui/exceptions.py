"""
Custom exceptions for Web UI Dashboard

Provides specific exception types for better error handling
and debugging.
"""


class DashboardError(Exception):
    """Base exception for all dashboard - related errors"""

    pass


class DependencyError(DashboardError):
    """Raised when dependency installation or checking fails"""

    pass


class DashboardStartupError(DashboardError):
    """Raised when the dashboard fails to start"""

    pass


class DashboardTimeoutError(DashboardError):
    """Raised when dashboard startup exceeds timeout"""

    pass


class ConfigurationError(DashboardError):
    """Raised when configuration is invalid"""

    pass


class OrchestratorError(DashboardError):
    """Raised when orchestrator execution fails"""

    pass
