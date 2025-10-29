"""Claude Code process supervisor.

Spawns and supervises real Claude Code CLI processes with safe input
validation, real - time output streaming, and confirmation prompt detection.
"""

from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field, ValidationError, field_validator

from orchestrator.core.supervisor.io_handler import ProcessIOHandler
from orchestrator.utils.ansi_utils import strip_ansi

DEFAULT_TIMEOUT = 300
GRACEFUL_TERMINATE_SECS = 2.0
POLL_INTERVAL_SECS = 0.05


class SpawnClaudeCodeInput(BaseModel):
    """Validated input for spawning Claude Code.

    Attributes:
        task_file: Relative path to the task file (no traversal allowed).
        workspace_root: Root directory for execution (will be resolved).
        timeout: Max expected run time in seconds.

    Examples:
        >>> SpawnClaudeCodeInput(
        ...     task_file="task_001.txt",
        ...     workspace_root="./workspace",
        ...     timeout=600,
        ... )
    """

    task_file: str = Field(..., min_length=1, max_length=255)
    workspace_root: str = Field(..., min_length=1, max_length=255)
    timeout: int = Field(default=DEFAULT_TIMEOUT, ge=10, le=3600)

    @field_validator("task_file")
    @classmethod
    def _validate_task_file(cls, v: str) -> str:
        if ".." in v or v.startswith("/") or "\\.." in v:
            raise ValueError("Invalid task file path")
        return v

    @field_validator("workspace_root")
    @classmethod
    def _validate_workspace_root(cls, v: str) -> str:
        path = Path(v).expanduser().resolve()
        return str(path)


@dataclass(frozen=True)
class ProcessResult:
    """Outcome of a spawn operation."""

    success: bool
    process_id: Optional[int] = None
    error_message: Optional[str] = None


@dataclass(frozen=True)
class ConfirmationPrompt:
    """Detected confirmation prompt with confidence score."""

    text: str
    pattern: str
    confidence: float


class ClaudeCodeSupervisor:
    """Supervisor for Claude Code CLI processes.

    Provides lifecycle control and output monitoring. Uses `wexpect` on
    Windows and `pexpect` on other platforms.
    """

    def __init__(self, workspace_root: str) -> None:
        self._workspace_root = str(Path(workspace_root).expanduser().resolve())
        self._child: Optional[object] = None
        self._patterns: List[re.Pattern[str]] = self._compile_patterns()

    # Public API
    # -----------
    def spawn_claude_code(self, task_file: str, timeout: int = DEFAULT_TIMEOUT) -> ProcessResult:
        """Spawn a Claude Code CLI process safely.

        Args:
            task_file: Relative path to the task file under the workspace root.
            timeout: Execution timeout in seconds.

        Returns:
            `ProcessResult` indicating success and the PID when successful.
        """

        try:
            payload = SpawnClaudeCodeInput(
                task_file=task_file, workspace_root=self._workspace_root, timeout=timeout
            )
        except ValidationError as exc:  # pragma: no cover - exercised in tests
            return ProcessResult(False, error_message=str(exc))

        try:
            child = self._spawn_child(payload)
            self._child = child
            self._feed_task_file(child, payload)
            return ProcessResult(True, process_id=getattr(child, "pid", None))
        except FileNotFoundError:
            return ProcessResult(False, error_message="Claude Code CLI not found")
        except PermissionError:
            return ProcessResult(False, error_message="Permission denied starting process")
        except Exception as exc:  # noqa: BLE001 - sanitize error
            return ProcessResult(
                False, error_message=f"Failed to start process: {type(exc).__name__}"
            )

    async def monitor_output(self) -> Tuple[ProcessIOHandler, object]:
        """Create an async output stream handler for the child.

        Returns:
            Tuple of `(ProcessIOHandler, child)` to allow external use.
        """

        if self._child is None:
            raise RuntimeError("No process to monitor")
        handler = ProcessIOHandler(self._child)
        return handler, self._child

    def detect_confirmation_prompt(self, output: str) -> Optional[ConfirmationPrompt]:
        """Detect confirmation prompts in output.

        Args:
            output: Text to analyze.

        Returns:
            A `ConfirmationPrompt` when detected, else `None`.
        """

        clean = strip_ansi(output).lower()
        matches = [p for p in self._patterns if p.search(clean)]
        if not matches:
            return None
        confidence = min(1.0, 0.3 + 0.1 * len(matches))
        return ConfirmationPrompt(text=output, pattern=matches[0].pattern, confidence=confidence)

    def terminate(self) -> bool:
        """Terminate the process gracefully, then forcefully if needed.

        Returns:
            True when the process is no longer alive, False otherwise.
        """

        child = self._child
        if child is None:
            return True

        try:
            # Try graceful termination
            if hasattr(child, "terminate"):
                child.terminate()
            deadline = time.monotonic() + GRACEFUL_TERMINATE_SECS
            while time.monotonic() < deadline and self._isalive(child):
                time.sleep(POLL_INTERVAL_SECS)
            # Force kill if still alive
            if self._isalive(child) and hasattr(child, "kill"):
                child.kill(9)
        except Exception:
            pass
        finally:
            dead = not self._isalive(child)
            self._child = None
            return dead

    @property
    def is_alive(self) -> bool:
        """Whether the supervised child is alive."""

        return self._isalive(self._child) if self._child is not None else False

    # Internals
    # ---------
    def _spawn_child(self, payload: SpawnClaudeCodeInput) -> object:
        cmd = "claude"
        args = ["--print"]
        cwd = payload.workspace_root
        if sys.platform.startswith("win"):
            try:
                import wexpect as expect  # type: ignore
            except ImportError as exc:
                raise FileNotFoundError("wexpect not available") from exc
        else:
            try:
                import pexpect as expect  # type: ignore
            except ImportError as exc:
                raise FileNotFoundError("pexpect not available") from exc

        child = expect.spawn(
            cmd,
            args,
            cwd=cwd,
            encoding="utf - 8",
            timeout=payload.timeout,
        )
        return child

    def _feed_task_file(self, child: object, payload: SpawnClaudeCodeInput) -> None:
        # Open and feed the file content to STDIN to avoid shell redirection
        task_path = Path(payload.workspace_root, payload.task_file)
        with task_path.open("r", encoding="utf - 8") as f:
            data = f.read()
        if hasattr(child, "send"):
            child.send(data)
        elif hasattr(child, "sendline"):
            for line in data.splitlines():
                child.sendline(line)

    def _compile_patterns(self) -> List[re.Pattern[str]]:
        # 11 patterns for confirmation prompts
        raw = [
            r"would you like to continue",
            r"proceed\??\s*(?:y / n|yes / no)?",
            r"are you sure",
            r"confirm(?:ation)?",
            r"type 'yes' to continue",
            r"press (?:enter|return) to continue",
            r"accept changes\?",
            r"overwrite .+\?",
            r"install .+\?",
            r"grant (?:access|permission)",
            r"allow .+\?",
        ]
        return [re.compile(p, re.IGNORECASE) for p in raw]

    def _isalive(self, child: Optional[object]) -> bool:
        try:
            return bool(child) and bool(getattr(child, "isalive")())
        except Exception:
            return False
