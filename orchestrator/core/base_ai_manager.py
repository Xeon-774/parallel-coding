"""Base AI Manager abstractions.

Defines the abstract base class used by manager implementations. Enforces
typed interfaces, small methods, and docstring documentation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseAIManager(ABC):
    """Abstract base class for AI managers.

    Subclasses implement orchestration logic for supervised agents.
    """

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        """Human - friendly manager name."""

        return self._name

    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        """Apply configuration.

        Args:
            config: Arbitrary configuration mapping.
        """

    @abstractmethod
    async def start(self) -> None:
        """Start manager operations asynchronously."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop manager operations and cleanup resources."""

    @abstractmethod
    def status(self) -> Dict[str, Optional[str]]:
        """Return a small status snapshot.

        Returns:
            Mapping with status details suitable for dashboards.
        """
