"""Recursive orchestration package.

Exports the public client interface used by other workers.
"""

from .recursion_validator import RecursionValidationResult, RecursionValidator
from .recursive_client import (
    APIError,
    AuthenticationError,
    ClientValidationError,
    NetworkError,
    RecursiveOrchestratorClient,
    RecursiveOrchestratorSyncClient,
)

__all__ = [
    "RecursiveOrchestratorClient",
    "RecursiveOrchestratorSyncClient",
    "RecursionValidator",
    "RecursionValidationResult",
    "APIError",
    "AuthenticationError",
    "ClientValidationError",
    "NetworkError",
]
