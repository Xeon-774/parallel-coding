"""
Hybrid Engine Integration Layer

Bridges the worker_manager's confirmation system with the hybrid decision engine.
Handles async / sync conversion and data format mapping.
"""

import asyncio
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

# Handle imports for both module use and direct execution
try:
    # Import worker_manager types
    # Import hybrid engine
    from orchestrator.core.hybrid_engine import ConfirmationRequest as HybridConfirmationRequest
    from orchestrator.core.hybrid_engine import ConfirmationType as HybridConfirmationType
    from orchestrator.core.hybrid_engine import (
        HybridDecisionEngine,
    )
    from orchestrator.core.worker.worker_manager import (
        ConfirmationRequest as WorkerConfirmationRequest,
    )
    from orchestrator.core.worker.worker_manager import ConfirmationType as WorkerConfirmationType
except ImportError:
    # Direct execution - add parent to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from orchestrator.core.hybrid_engine import ConfirmationRequest as HybridConfirmationRequest
    from orchestrator.core.hybrid_engine import ConfirmationType as HybridConfirmationType
    from orchestrator.core.hybrid_engine import (
        HybridDecisionEngine,
    )
    from orchestrator.core.worker.worker_manager import (
        ConfirmationRequest as WorkerConfirmationRequest,
    )
    from orchestrator.core.worker.worker_manager import ConfirmationType as WorkerConfirmationType


# Compatibility layer for existing code expecting SafetyJudgment
class SafetyLevel(str, Enum):
    """Safety level assessment (for compatibility)"""

    SAFE = "safe"
    CAUTION = "caution"
    DANGEROUS = "dangerous"
    PROHIBITED = "prohibited"


@dataclass
class SafetyJudgment:
    """
    Result of safety assessment (for compatibility with existing worker_manager)
    """

    level: SafetyLevel
    should_approve: bool
    should_escalate: bool
    reasoning: str
    suggested_modifications: Optional[str] = None


class HybridEngineAdapter:
    """
    Adapter that makes HybridDecisionEngine compatible with worker_manager.

    Features:
    - Async / sync conversion
    - Data format mapping
    - Compatibility with existing SafetyJudgment interface
    """

    def __init__(
        self, workspace_root: str, wsl_distribution: str = "Ubuntu - 24.04", verbose: bool = False
    ):
        """
        Initialize adapter

        Args:
            workspace_root: Root directory of workspace
            wsl_distribution: WSL distribution name for Claude CLI
            verbose: Enable verbose logging
        """
        self.workspace_root = Path(workspace_root)
        self.verbose = verbose

        # Create hybrid engine
        self.engine = HybridDecisionEngine(
            workspace_root=self.workspace_root, wsl_distribution=wsl_distribution, verbose=verbose
        )

        # Event loop for async operations
        self.loop = None

    def judge_confirmation(
        self, confirmation: WorkerConfirmationRequest, context: Optional[Dict[str, Any]] = None
    ) -> SafetyJudgment:
        """
        Judge confirmation request (synchronous interface for worker_manager)

        Args:
            confirmation: Worker confirmation request
            context: Optional context information

        Returns:
            SafetyJudgment with decision and reasoning
        """
        # Convert to hybrid engine format
        hybrid_request = self._convert_to_hybrid_request(confirmation)

        # Build context
        if context is None:
            context = {}

        # Run async decision in sync context
        decision = self._run_async_decision(
            worker_id=confirmation.worker_id, request=hybrid_request, context=context
        )

        # Convert back to SafetyJudgment
        return self._convert_to_safety_judgment(decision)

    def _convert_to_hybrid_request(
        self, worker_request: WorkerConfirmationRequest
    ) -> HybridConfirmationRequest:
        """Convert worker manager's request to hybrid engine format"""

        # Map confirmation types
        type_mapping = {
            WorkerConfirmationType.FILE_WRITE: HybridConfirmationType.FILE_WRITE,
            WorkerConfirmationType.FILE_READ: HybridConfirmationType.FILE_READ,
            WorkerConfirmationType.FILE_DELETE: HybridConfirmationType.FILE_DELETE,
            WorkerConfirmationType.PACKAGE_INSTALL: HybridConfirmationType.PACKAGE_INSTALL,
            WorkerConfirmationType.COMMAND_EXECUTE: HybridConfirmationType.COMMAND_EXECUTE,
            WorkerConfirmationType.NETWORK_ACCESS: HybridConfirmationType.GENERAL,
            WorkerConfirmationType.PERMISSION_REQUEST: HybridConfirmationType.GENERAL,
            WorkerConfirmationType.UNKNOWN: HybridConfirmationType.GENERAL,
        }

        hybrid_type = type_mapping.get(
            worker_request.confirmation_type, HybridConfirmationType.GENERAL
        )

        return HybridConfirmationRequest(
            confirmation_type=hybrid_type,
            message=worker_request.message,
            details=worker_request.details,
        )

    def _convert_to_safety_judgment(self, decision) -> SafetyJudgment:
        """Convert hybrid engine decision to SafetyJudgment"""

        # Map action to safety judgment
        if decision.action == "approve":
            if decision.decided_by == "rules":
                # Fast rule - based approval
                level = SafetyLevel.SAFE
                should_approve = True
                should_escalate = False
            else:
                # AI approved
                level = SafetyLevel.CAUTION
                should_approve = True
                should_escalate = False
        else:  # deny
            if decision.decided_by == "rules":
                # Fast rule - based denial (dangerous)
                level = SafetyLevel.DANGEROUS
                should_approve = False
                should_escalate = True  # Could escalate to user
            elif decision.is_fallback:
                # Template fallback denial
                level = SafetyLevel.CAUTION
                should_approve = False
                should_escalate = True  # Escalate due to uncertainty
            else:
                # AI denied
                level = SafetyLevel.DANGEROUS
                should_approve = False
                should_escalate = False  # AI already made informed decision

        return SafetyJudgment(
            level=level,
            should_approve=should_approve,
            should_escalate=should_escalate,
            reasoning=decision.reasoning,
            suggested_modifications=None,
        )

    def _run_async_decision(
        self, worker_id: str, request: HybridConfirmationRequest, context: Dict[str, Any]
    ):
        """Run async decision in sync context"""

        # Create or reuse event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run async operation
        return loop.run_until_complete(self.engine.decide(worker_id, request, context))

    def get_stats(self) -> Dict[str, Any]:
        """Get decision statistics from hybrid engine"""
        return self.engine.get_stats()


# For backward compatibility - can be used as drop - in replacement for AISafetyJudge
class AISafetyJudge(HybridEngineAdapter):
    """
    Backward - compatible wrapper for HybridEngineAdapter

    This allows existing code using AISafetyJudge to seamlessly
    use the hybrid engine without code changes.
    """


# Example usage
if __name__ == "__main__":
    import time

    # Create adapter
    adapter = HybridEngineAdapter(
        workspace_root=r"D:\user\ai_coding\AI_Investor\tools\parallel - coding\workspace",
        verbose=True,
    )

    # Create worker confirmation request
    worker_request = WorkerConfirmationRequest(
        worker_id="worker_001",
        confirmation_type=WorkerConfirmationType.FILE_WRITE,
        message="I want to create a file 'models / user.py' with database model code.",
        details={"file": "workspace / models / user.py"},
        timestamp=time.time(),
    )

    # Judge it (synchronous call)
    print("=" * 70)
    print("Testing Hybrid Engine Adapter")
    print("=" * 70)

    judgment = adapter.judge_confirmation(worker_request)

    print("\nResult:")
    print(f"  Level: {judgment.level}")
    print(f"  Should Approve: {judgment.should_approve}")
    print(f"  Should Escalate: {judgment.should_escalate}")
    print(f"  Reasoning: {judgment.reasoning}")
    print("=" * 70)

    # Show stats
    stats = adapter.get_stats()
    print("\nStatistics:")
    print(f"  Total decisions: {stats['total_decisions']}")
    print(f"  Rules: {stats['rules_decisions']}")
    print(f"  AI: {stats['ai_decisions']}")
    print(f"  Template fallbacks: {stats['template_fallbacks']}")
    print("=" * 70)
