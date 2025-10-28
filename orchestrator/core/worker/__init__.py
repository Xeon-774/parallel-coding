"""
Worker AI Management Module

Components specific to parallel Worker AI management:
- WorkerManager: Manages multiple Claude CLI worker instances
- Worker-specific logic and utilities
"""

__version__ = "1.0.0"

from orchestrator.core.worker.worker_manager import WorkerManager

__all__ = ["WorkerManager"]
