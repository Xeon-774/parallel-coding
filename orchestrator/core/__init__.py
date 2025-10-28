"""
Core orchestration modules

This package contains the core components of the orchestrator,
separated by responsibility following the Single Responsibility Principle.

Modules:
- models: Core data models (WorkerInfo, TaskResult)
- worker_manager: Worker process management
- stream_monitor: Real-time stream monitoring
- result_integrator: Result collection and reporting
- task_analyzer_service: Task analysis and splitting
"""

from orchestrator.core.models import WorkerInfo, TaskResult
from orchestrator.core.worker.worker_manager import WorkerManager
from orchestrator.core.stream_monitor import StreamMonitor
from orchestrator.core.result_integrator import ResultIntegrator
from orchestrator.core.task_analyzer_service import TaskAnalyzerService

__all__ = [
    # Models
    "WorkerInfo",
    "TaskResult",
    # Services
    "WorkerManager",
    "StreamMonitor",
    "ResultIntegrator",
    "TaskAnalyzerService",
]
