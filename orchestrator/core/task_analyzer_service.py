"""
Task analysis and splitting service

Provides task decomposition using both AI - driven and basic strategies.
"""

from typing import Any, Dict, List, Optional, Tuple

from orchestrator.config import TaskConfig
from orchestrator.interfaces import ILogger


class TaskAnalyzerService:
    """
    Task analysis and splitting service

    Analyzes user requests and splits them into executable subtasks
    using either advanced AI - driven analysis or basic pattern matching.
    """

    def __init__(
        self, task_config: TaskConfig, logger: ILogger, task_splitter: Optional[Any] = None
    ):
        """
        Initialize task analyzer service

        Args:
            task_config: Task configuration
            logger: Logger instance
            task_splitter: Optional advanced task splitter (AdvancedTaskSplitter)
        """
        self.task_config = task_config
        self.logger = logger
        self.task_splitter = task_splitter

    def analyze_and_split(self, request: str) -> List[Dict[str, Any]]:
        """
        Analyze and split user request into tasks

        Args:
            request: User request string

        Returns:
            List of task dictionaries
        """
        if self.task_splitter:
            return self._advanced_split(request)
        else:
            return self._basic_split(request)

    def _advanced_split(self, request: str) -> List[Dict[str, Any]]:
        """
        Split task using advanced task splitter

        Args:
            request: User request

        Returns:
            List of task dictionaries with analysis data
        """
        assert self.task_splitter is not None, "task_splitter must be initialized"
        subtasks = self.task_splitter.split_task(request)

        tasks = []
        for subtask in subtasks:
            tasks.append(
                {
                    "name": subtask.name,
                    "prompt": subtask.prompt + self.task_config.default_prompt_suffix,
                    "task_id": subtask.task_id,
                    "complexity": subtask.complexity.name,
                    "estimated_time": subtask.estimated_time,
                }
            )

        self.logger.debug(f"Advanced split: {len(tasks)} tasks", tasks=[t["name"] for t in tasks])
        return tasks

    def _basic_split(self, request: str) -> List[Dict[str, Any]]:
        """
        Split task using basic pattern matching

        Fallback method when advanced splitter is not available.

        Args:
            request: User request

        Returns:
            List of task dictionaries
        """
        tasks = []

        # Simple keyword - based splitting
        request_lower = request.lower()

        if "電卓" in request or "calculator" in request_lower:
            tasks.append(
                {
                    "name": "Calculator Application",
                    "prompt": (
                        "Create a simple calculator application in Python. "
                        "Include +, -, *, / operations. "
                        "Write clean, commented code with error handling. "
                        "Output only the Python code."
                    ),
                }
            )
        elif "todo" in request_lower or "タスク" in request:
            tasks.append(
                {
                    "name": "Todo List Application",
                    "prompt": (
                        "Create a simple todo list application in Python. "
                        "Include add, list, and delete functions. "
                        "Write clean, commented code. "
                        "Output only the Python code."
                    ),
                }
            )
        else:
            # Generic task
            tasks.append(
                {"name": "Custom Task", "prompt": request + self.task_config.default_prompt_suffix}
            )

        self.logger.debug(f"Basic split: {len(tasks)} tasks", tasks=[t["name"] for t in tasks])
        return tasks

    def validate_task(self, task: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate a task dictionary

        Args:
            task: Task dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = ["name", "prompt"]

        for field in required_fields:
            if field not in task:
                return False, f"Missing required field: {field}"

        if not isinstance(task["name"], str) or not task["name"].strip():
            return False, "Task name must be a non - empty string"

        if not isinstance(task["prompt"], str) or not task["prompt"].strip():
            return False, "Task prompt must be a non - empty string"

        return True, None
