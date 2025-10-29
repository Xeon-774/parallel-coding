"""
AI Safety Judge (v8.0)

Orchestrator AI judges the safety of operations requested by worker AIs.
Uses AI reasoning to determine if operations should be approved, denied, or
escalated to the user.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from orchestrator.core.common.models import ConfirmationRequest, ConfirmationType


class SafetyLevel(str, Enum):
    """Safety level assessment"""

    SAFE = "safe"  # Safe to auto - approve
    CAUTION = "caution"  # Proceed with caution
    DANGEROUS = "dangerous"  # Requires user approval
    PROHIBITED = "prohibited"  # Never allow


@dataclass
class SafetyJudgment:
    """Result of safety assessment"""

    level: SafetyLevel
    should_approve: bool
    should_escalate: bool
    reasoning: str
    suggested_modifications: Optional[str] = None


class AISafetyJudge:
    """
    Orchestrator AI component that judges safety of worker AI requests

    This acts as an intelligent gatekeeper that:
    1. Analyzes confirmation requests from worker AIs
    2. Assesses safety based on context and content
    3. Makes approval decisions or escalates to user
    4. Provides reasoning for decisions
    """

    def __init__(self, workspace_root: str):
        """
        Initialize AI safety judge

        Args:
            workspace_root: Root directory of workspace (safe zone)
        """
        self.workspace_root = workspace_root

        # Dangerous patterns
        self.dangerous_patterns = [
            (r"rm\s+-rf\s+/", "Recursive delete of root directory"),
            (r"rm\s+-rf\s+\*", "Recursive delete of all files"),
            (r"format\s+[A - Z]:", "Format disk drive"),
            (r"del\s+/[SF]", "Delete system files"),
            (r"shutdown", "System shutdown"),
            (r"reboot", "System reboot"),
            (r"chmod\s + 777", "Overly permissive file permissions"),
            (r"curl.*\|\s * bash", "Pipe download to bash (security risk)"),
            (r"wget.*\|\s * sh", "Pipe download to shell (security risk)"),
        ]

        # Safe patterns (when in workspace)
        self.safe_patterns = [
            r"\.txt$",  # Text files
            r"\.py$",  # Python files
            r"\.js$",  # JavaScript files
            r"\.json$",  # JSON files
            r"\.md$",  # Markdown files
            r"\.csv$",  # CSV files
            r"requirements\.txt",  # Dependencies
            r"package\.json",  # Node dependencies
        ]

    def judge_confirmation(
        self, confirmation: ConfirmationRequest, context: Optional[Dict[str, Any]] = None
    ) -> SafetyJudgment:
        """
        Judge the safety of a confirmation request

        Args:
            confirmation: The confirmation request to judge
            context: Optional context information (task description, etc.)

        Returns:
            SafetyJudgment with decision and reasoning
        """
        # Route to appropriate judging method based on type
        if confirmation.confirmation_type == ConfirmationType.FILE_WRITE:
            return self._judge_file_write(confirmation, context)

        elif confirmation.confirmation_type == ConfirmationType.FILE_DELETE:
            return self._judge_file_delete(confirmation, context)

        elif confirmation.confirmation_type == ConfirmationType.COMMAND_EXECUTE:
            return self._judge_command_execute(confirmation, context)

        elif confirmation.confirmation_type == ConfirmationType.PACKAGE_INSTALL:
            return self._judge_package_install(confirmation, context)

        else:
            # Unknown type, proceed with caution
            return SafetyJudgment(
                level=SafetyLevel.CAUTION,
                should_approve=True,
                should_escalate=False,
                reasoning="Unknown operation type, proceeding with caution",
            )

    def _judge_file_write(
        self, confirmation: ConfirmationRequest, context: Optional[Dict[str, Any]]
    ) -> SafetyJudgment:
        """Judge file write operation safety"""

        file_path = confirmation.details.get("file", "")

        # Check if in workspace
        if not self._is_in_workspace(file_path):
            return SafetyJudgment(
                level=SafetyLevel.DANGEROUS,
                should_approve=False,
                should_escalate=True,
                reasoning=f"File write outside workspace: {file_path}",
                suggested_modifications=f"Move file to workspace: {self.workspace_root}",
            )

        # Check if safe file type
        if any(re.search(pattern, file_path) for pattern in self.safe_patterns):
            return SafetyJudgment(
                level=SafetyLevel.SAFE,
                should_approve=True,
                should_escalate=False,
                reasoning=f"Safe file write to workspace: {file_path}",
            )

        # Check for system files
        system_patterns = [r"/etc/", r"/sys/", r"/proc/", r"C:\\Windows\\", r"C:\\Program Files"]
        if any(re.search(pattern, file_path, re.IGNORECASE) for pattern in system_patterns):
            return SafetyJudgment(
                level=SafetyLevel.PROHIBITED,
                should_approve=False,
                should_escalate=True,
                reasoning=f"Attempted write to system directory: {file_path}",
            )

        # Unknown file type in workspace, proceed with caution
        return SafetyJudgment(
            level=SafetyLevel.CAUTION,
            should_approve=True,
            should_escalate=False,
            reasoning=f"File write in workspace (unknown type): {file_path}",
        )

    def _judge_file_delete(
        self, confirmation: ConfirmationRequest, context: Optional[Dict[str, Any]]
    ) -> SafetyJudgment:
        """Judge file delete operation safety"""

        file_path = confirmation.details.get("file", "")

        # Deletes should generally be escalated
        if not self._is_in_workspace(file_path):
            return SafetyJudgment(
                level=SafetyLevel.PROHIBITED,
                should_approve=False,
                should_escalate=True,
                reasoning=f"File delete outside workspace: {file_path}",
            )

        # Even in workspace, deletions are risky
        return SafetyJudgment(
            level=SafetyLevel.DANGEROUS,
            should_approve=False,
            should_escalate=True,
            reasoning=f"File deletion requires user approval: {file_path}",
        )

    def _judge_command_execute(
        self, confirmation: ConfirmationRequest, context: Optional[Dict[str, Any]]
    ) -> SafetyJudgment:
        """Judge command execution safety"""

        command = confirmation.details.get("command", "")

        # Check for dangerous patterns
        for pattern, description in self.dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return SafetyJudgment(
                    level=SafetyLevel.PROHIBITED,
                    should_approve=False,
                    should_escalate=True,
                    reasoning=f"Dangerous command detected: {description}\nCommand: {command}",
                )

        # Check for safe commands
        safe_commands = [
            r"^pip install",
            r"^npm install",
            r"^python ",
            r"^node ",
            r"^pytest",
            r"^git ",
            r"^ls ",
            r"^cat ",
            r"^grep ",
            r"^find ",
        ]

        if any(re.search(pattern, command) for pattern in safe_commands):
            return SafetyJudgment(
                level=SafetyLevel.SAFE,
                should_approve=True,
                should_escalate=False,
                reasoning=f"Safe command: {command}",
            )

        # Unknown command, escalate
        return SafetyJudgment(
            level=SafetyLevel.DANGEROUS,
            should_approve=False,
            should_escalate=True,
            reasoning=f"Unknown command requires user approval: {command}",
        )

    def _judge_package_install(
        self, confirmation: ConfirmationRequest, context: Optional[Dict[str, Any]]
    ) -> SafetyJudgment:
        """Judge package installation safety"""

        # Package installs are generally safe
        # Could add checks for known malicious packages

        return SafetyJudgment(
            level=SafetyLevel.SAFE,
            should_approve=True,
            should_escalate=False,
            reasoning="Package installation (approved)",
        )

    def _is_in_workspace(self, path: str) -> bool:
        """Check if path is within workspace"""
        import os

        try:
            # Normalize paths
            workspace = os.path.abspath(self.workspace_root)
            target = os.path.abspath(path)

            # Check if target is under workspace
            return target.startswith(workspace)
        except Exception:
            # If path resolution fails, assume unsafe
            return False

    def explain_decision(self, judgment: SafetyJudgment) -> str:
        """
        Generate human - readable explanation of decision

        Args:
            judgment: Safety judgment to explain

        Returns:
            Human - readable explanation string
        """
        explanation = """
Safety Assessment:
  Level: {judgment.level.upper()}
  Decision: {'APPROVE' if judgment.should_approve else 'DENY'}
  Escalate: {'YES' if judgment.should_escalate else 'NO'}

Reasoning:
  {judgment.reasoning}
"""

        if judgment.suggested_modifications:
            explanation += """
Suggested Alternative:
  {judgment.suggested_modifications}
"""

        return explanation


# Example usage
if __name__ == "__main__":
    from orchestrator.core.common.models import ConfirmationRequest, ConfirmationType  # noqa: F811

    # Create judge
    judge = AISafetyJudge(workspace_root="./workspace")

    # Test cases
    test_cases = [
        ConfirmationRequest(
            worker_id="worker_1",
            confirmation_type=ConfirmationType.FILE_WRITE,
            message="Write to file 'workspace / output.py'?",
            details={"file": "workspace / output.py"},
        ),
        ConfirmationRequest(
            worker_id="worker_2",
            confirmation_type=ConfirmationType.FILE_DELETE,
            message="Delete file 'important.txt'?",
            details={"file": "/home / user / important.txt"},
        ),
        ConfirmationRequest(
            worker_id="worker_3",
            confirmation_type=ConfirmationType.COMMAND_EXECUTE,
            message="Execute command 'rm -rf /'?",
            details={"command": "rm -rf /"},
        ),
        ConfirmationRequest(
            worker_id="worker_4",
            confirmation_type=ConfirmationType.COMMAND_EXECUTE,
            message="Execute command 'pip install requests'?",
            details={"command": "pip install requests"},
        ),
    ]

    print("AI Safety Judge - Test Cases\n")
    print("=" * 70)

    for i, conf in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Type: {conf.confirmation_type}")
        print(f"  Message: {conf.message}")

        judgment = judge.judge_confirmation(conf)

        print("\n  Judgment:")
        print(f"    Level: {judgment.level}")
        print(f"    Approve: {judgment.should_approve}")
        print(f"    Escalate: {judgment.should_escalate}")
        print(f"    Reasoning: {judgment.reasoning}")

        if judgment.suggested_modifications:
            print(f"    Suggestion: {judgment.suggested_modifications}")

        print("-" * 70)
