"""
Custom exceptions for Web UI Dashboard

Provides specific exception types for better error handling
and debugging.
"""


class DashboardError(Exception):
    """Base exception for all dashboard - related errors"""


class DependencyError(DashboardError):
    """Raised when dependency installation or checking fails"""


class DashboardStartupError(DashboardError):
    """Raised when the dashboard fails to start"""


class DashboardTimeoutError(DashboardError):
    """Raised when dashboard startup exceeds timeout"""


class ConfigurationError(DashboardError):
    """Raised when configuration is invalid"""


class OrchestratorError(DashboardError):
    """Raised when orchestrator execution fails"""
