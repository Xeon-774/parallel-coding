"""
Core data models for orchestration

Contains dataclasses and models used across multiple core modules.
"""

import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WorkerInfo:
    """Information about a worker process"""

    worker_id: str
    name: str
    process: "subprocess.Popen[Any]"
    output_file: str
    error_file: str
    task: Dict[str, Any]
    retries: int = 0
    started_at: float = field(default_factory=time.time)
    stdout_lines: List[str] = field(default_factory=list)
    stderr_lines: List[str] = field(default_factory=list)
    monitor_threads: List[threading.Thread] = field(default_factory=list)


@dataclass
class TaskResult:
    """Result of a single task execution"""

    worker_id: str
    name: str
    output: str
    success: bool
    duration: Optional[float] = None
    error_message: Optional[str] = None
