"""AI Safety Judge stub.

A minimal, production - safe judge used to decide whether a confirmation
prompt can be auto - approved. Worker 2 may extend or replace strategies.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Decision(Enum):
    """Decision outcomes for confirmation prompts."""

    APPROVE = "approve"
    DENY = "deny"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class Judgment:
    """Judge result with explanation suitable for audit logs."""

    decision: Decision
    reason: str


class AISafetyJudge:
    """Simple safety judge.

    This default implementation is conservative: it denies unknown prompts
    and approves only clearly safe operations. It can be swapped via DI.
    """

    def assess(self, prompt: str, context: Optional[str] = None) -> Judgment:
        """Assess a prompt and return a decision.

        Args:
            prompt: The text of the confirmation prompt.
            context: Optional extra context for the decision.

        Returns:
            A `Judgment` with decision and explanation.
        """

        normalized = prompt.strip().lower()
        if any(k in normalized for k in ("yes / no", "confirm", "proceed?")):
            return Judgment(Decision.ESCALATE, "Requires explicit user confirmation")
        if "print" in normalized and "view" in normalized:
            return Judgment(Decision.APPROVE, "Read - only action deemed safe")
        return Judgment(Decision.DENY, "Unrecognized or potentially unsafe request")
