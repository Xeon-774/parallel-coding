"""Orchestrator configuration models with recursion support.

This module defines Pydantic models used to configure the orchestrator.
It extends the base configuration to include recursion-related fields
required for hierarchical orchestration.

All fields include validation and sensible defaults to maintain backward
compatibility with existing code that may import these models.
"""

from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel, Field, validator


class OrchestratorConfigRecursion(BaseModel):
    """Recursion configuration for hierarchical orchestration.

    This model controls how deep recursion can go, where recursive API calls
    should be made, and how many workers are permitted at each depth.

    Examples:
        Basic usage with defaults:
            >>> cfg = OrchestratorConfigRecursion()
            >>> cfg.max_recursion_depth
            3
            >>> cfg.current_depth
            0

        Validate URL format:
            >>> OrchestratorConfigRecursion(
            ...     orchestrator_api_url="https://orch.local",
            ... )
            OrchestratorConfigRecursion(max_recursion_depth=3, current_depth=0, orchestrator_api_url='https://orch.local', orchestrator_api_key=None, workers_by_depth={0: 10, 1: 8, 2: 5, 3: 3, 4: 2, 5: 1})
    """

    # Recursion control
    max_recursion_depth: int = Field(
        default=3,
        ge=0,
        le=5,
        description="Maximum recursion depth (0=no recursion, 5=max)",
    )
    current_depth: int = Field(
        default=0,
        ge=0,
        le=5,
        description="Current recursion depth",
    )

    # Orchestrator endpoint (for recursive calls)
    orchestrator_api_url: Optional[str] = Field(
        default=None, description="URL of parent orchestrator API"
    )
    orchestrator_api_key: Optional[str] = Field(
        default=None, description="API key for parent orchestrator"
    )

    # Worker allocation by depth
    workers_by_depth: Dict[int, int] = Field(
        default_factory=lambda: {
            0: 10,  # Root: 10 workers
            1: 8,  # Level 1: 8 workers
            2: 5,  # Level 2: 5 workers
            3: 3,  # Level 3: 3 workers
            4: 2,  # Level 4: 2 workers
            5: 1,  # Level 5: 1 worker
        },
        description="Max workers per depth level",
    )

    @validator("current_depth")
    def validate_current_depth(cls, v: int, values: dict) -> int:
        """Ensure current depth doesn't exceed max depth.

        Args:
            v: The provided current depth.
            values: Other values already parsed on the model.

        Returns:
            The validated current depth.

        Raises:
            ValueError: If current depth exceeds configured maximum.
        """
        max_depth = values.get("max_recursion_depth", 3)
        if v > max_depth:
            raise ValueError(f"Current depth ({v}) exceeds max depth ({max_depth})")
        return v

    @validator("orchestrator_api_url")
    def validate_api_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate API URL format.

        Args:
            v: The API URL to validate.

        Returns:
            The validated URL (or None if not provided).

        Raises:
            ValueError: If the URL does not start with http:// or https://
        """
        if v is not None:
            if not v.startswith(("http://", "https://")):
                raise ValueError("API URL must start with http:// or https://")
        return v


class OrchestratorConfig(BaseModel):
    """Top-level orchestrator configuration.

    Notes:
        This class is provided to keep compatibility with existing imports.
        In existing systems, this may already include many other fields. Here
        we keep it minimal and additive, focusing on recursion configuration.
    """

    # Other existing fields would live here in a real system.
    recursion: OrchestratorConfigRecursion = Field(
        default_factory=OrchestratorConfigRecursion,
        description="Recursion configuration",
    )
