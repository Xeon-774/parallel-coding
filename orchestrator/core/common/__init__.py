"""
Common Core Components

Shared components for all AI management modes:
- Worker AI management (parallel coding)
- Supervisor AI management (Claude Code monitoring - Manager AI)
- Future: MT4 bot management, etc.

This module contains:
- AI Safety Judge (intelligent confirmation handling)
- Metrics Collection (performance tracking)
- Common Models (shared data structures)
- Base Manager (common base class for all AI managers)
"""

# Version
__version__ = "1.0.0"

# Export common components
from orchestrator.core.common.models import ConfirmationRequest, ConfirmationType
from orchestrator.core.common.ai_safety_judge import (
    AISafetyJudge,
    SafetyLevel,
    SafetyJudgment,
)
from orchestrator.core.common.metrics import MetricsCollector
from orchestrator.core.common.base_manager import (
    BaseAIManager,
    ManagerType,
    ManagerStatus,
    HealthCheckResult,
    ManagerMetrics,
)

__all__ = [
    "ConfirmationRequest",
    "ConfirmationType",
    "AISafetyJudge",
    "SafetyLevel",
    "SafetyJudgment",
    "MetricsCollector",
    "BaseAIManager",
    "ManagerType",
    "ManagerStatus",
    "HealthCheckResult",
    "ManagerMetrics",
]
