"""Policy schemas for OPA/Rego integration."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PolicyDecision(str, Enum):
    """Policy decision results."""

    ALLOW = "allow"
    DENY = "deny"
    UNKNOWN = "unknown"


@dataclass
class PolicyQuery:
    """Policy query request."""

    input: dict[str, Any]
    policy_path: str  # e.g., "ai_investor/sandbox/execute"
    decision: str = "allow"  # default decision field to check


@dataclass
class PolicyRequest:
    """Policy evaluation request."""

    action: str  # e.g., "execute", "file_write", "network_access"
    resource: str  # e.g., "sandbox", "filesystem", "network"
    context: dict[str, Any]  # Additional context (user, risk_level, etc.)


@dataclass
class PolicyResponse:
    """Policy evaluation response."""

    decision: PolicyDecision
    allowed: bool
    reasons: list[str]
    policy_path: str
    metadata: dict[str, Any] | None = None


@dataclass
class PolicyEvaluationResult:
    """Result of policy evaluation."""

    allowed: bool
    decision: PolicyDecision
    policy_path: str
    reasons: list[str]
    violations: list[str]
    metadata: dict[str, Any] | None = None

    def __bool__(self) -> bool:
        """Allow using result as boolean."""
        return self.allowed
