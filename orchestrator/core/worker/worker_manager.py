"""
Worker Manager (v10.0 - Unified Implementation)

Production-grade worker management with full interactive capabilities.
Uses pexpect/wexpect for robust pseudo-terminal control.

Features:
- Cross-platform support (Windows/Linux/WSL)
- Robust bidirectional communication with Claude CLI workers
- Pattern-based confirmation detection
- AI-powered safety judgment
- Pseudo-terminal control for real terminal environment
- Integrated with recursive orchestration capabilities

This is the unified worker manager consolidating all previous implementations.
"""

import sys
import time
import threading
from typing import Optional, Dict, List, Callable, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

# Cross-platform pexpect import
if sys.platform == "win32":
    import wexpect as expect_module

    PLATFORM = "windows"
else:
    import pexpect as expect_module

    PLATFORM = "unix"

from orchestrator.config import OrchestratorConfig
from orchestrator.interfaces import ILogger
from orchestrator.core.models import TaskResult
from orchestrator.utils.ansi_utils import strip_ansi_codes
from orchestrator.core.common.metrics import MetricsCollector
from orchestrator.core.worker.codex_executor import (
    CodexExecutor,
    CodexExecutionResult,
    create_codex_executor_from_config,
)


# Supervisor-related models for Worker 2 Manager AI Integration
class SupervisorStatus(Enum):
    """Supervisor process status states."""

    SPAWNING = "spawning"
    RUNNING = "running"
    TERMINATED = "terminated"
    ERROR = "error"


@dataclass
class SupervisorStatusInfo:
    """Detailed supervisor status information.

    Attributes:
        supervisor_id: Unique supervisor identifier
        status: Current supervisor status
        alive: Whether supervisor process is alive
        last_error: Last error message (if any)
        uptime_secs: Supervisor uptime in seconds
        output_lines: Number of output lines captured
    """

    supervisor_id: str
    status: SupervisorStatus
    alive: bool
    last_error: Optional[str] = None
    uptime_secs: float = 0.0
    output_lines: int = 0


@dataclass
class SupervisedWorkerResult:
    """Result of spawning a supervised worker.

    Attributes:
        supervisor_id: Unique supervisor identifier
        status: Initial supervisor status
    """

    supervisor_id: str
    status: SupervisorStatus


class OrchestratorTerminalCapture:
    """
    Captures orchestrator decision-making output to orchestrator_terminal.log

    This provides visibility into the orchestrator's reasoning process,
    including worker output analysis, confirmation handling, and responses.
    """

    def __init__(self, workspace_dir: Path, worker_id: str):
        """
        Initialize orchestrator terminal capture

        Args:
            workspace_dir: Worker workspace directory
            worker_id: Worker identifier for log file naming
        """
        self.terminal_file = workspace_dir / "orchestrator_terminal.log"
        self.worker_id = worker_id
        self._init_log_file()

    def _init_log_file(self) -> None:
        """Initialize log file with header"""
        with open(self.terminal_file, "w", encoding="utf-8") as f:
            f.write(f"=== Orchestrator Terminal Output ===\n")
            f.write(f"=== Worker: {self.worker_id} ===\n")
            f.write(f"=== Started: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
            f.flush()

    def log(self, message: str, category: str = "INFO") -> None:
        """
        Append message to terminal log

        Args:
            message: Message to log
            category: Log category (INFO, OUTPUT, SENT, DECISION, etc.)
        """
        # Strip ANSI codes for clean web display (Phase 2.1)
        clean_message = strip_ansi_codes(message)

        timestamp = time.strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{category}] {clean_message}\n"

        # Write to file
        try:
            with open(self.terminal_file, "a", encoding="utf-8") as f:
                f.write(formatted)
                f.flush()  # Force immediate write for real-time streaming
        except Exception as e:
            # Fallback to print if file write fails
            print(f"[ERROR] Failed to write to orchestrator log: {e}")

        # Also print to stdout for console visibility
        print(formatted.rstrip())


from orchestrator.core.common.models import ConfirmationRequest, ConfirmationType
from orchestrator.core.common.ai_safety_judge import SafetyLevel

@dataclass
class WorkerSession:
    """Represents an active worker session"""

    worker_id: str
    task_name: str
    child_process: Any  # pexpect/wexpect spawn object
    started_at: float
    output_lines: List[str] = field(default_factory=list)
    dialogue_transcript: List[Dict[str, Any]] = field(
        default_factory=list
    )  # NEW: Complete dialogue log
    workspace_dir: Optional[Path] = None
    raw_terminal_file: Optional[Path] = None  # NEW: Path to raw terminal output file
    orchestrator_capture: Optional["OrchestratorTerminalCapture"] = (
        None  # NEW: Orchestrator terminal capture
    )
    confirmation_count: int = 0  # NEW Phase 2.2: Count confirmations for metrics
    last_output_time: float = field(default_factory=time.time)  # NEW Phase 2.2: Track output timing


class WorkerManager:
    """
    Unified production-grade worker manager (v10.0).

    This is the consolidated implementation combining all previous worker managers:
    - Basic WorkerManager (process spawning)
    - InteractiveWorkerManager (bidirectional communication)
    - WorkerManager (cross-platform + safety)

    Features:
    - Cross-platform support (Windows/Linux/WSL)
    - Pseudo-terminal control via pexpect/wexpect
    - Pattern-based confirmation detection
    - AI-powered safety judgment
    - User escalation for dangerous operations
    - Recursive orchestration support
    """

    def __init__(
        self,
        config: OrchestratorConfig,
        logger: ILogger,
        user_approval_callback: Optional[Callable[[ConfirmationRequest], bool]] = None,
    ):
        """
        Initialize worker manager

        Args:
            config: Orchestrator configuration
            logger: Logger instance
            user_approval_callback: Optional callback for user approval
        """
        self.config = config
        self.logger = logger
        self.user_approval_callback = user_approval_callback
        self.workers: Dict[str, WorkerSession] = {}
        self.platform = PLATFORM

        # Initialize metrics collector (Phase 2.2)
        self.metrics = MetricsCollector(workspace_root=Path(config.workspace_root))

        # Initialize Codex executor (subprocess-based, NOT pexpect)
        self.codex_executor = create_codex_executor_from_config(config)

        # Confirmation patterns - will be tuned based on actual Claude CLI output
        self.confirmation_patterns = [
            # File operations
            (
                r"(?i)write\s+(?:to\s+)?(?:file\s+)?['\"]([^'\"]+)['\"].*\?",
                ConfirmationType.FILE_WRITE,
            ),
            (r"(?i)create\s+(?:file\s+)?['\"]([^'\"]+)['\"].*\?", ConfirmationType.FILE_WRITE),
            (r"(?i)delete\s+(?:file\s+)?['\"]([^'\"]+)['\"].*\?", ConfirmationType.FILE_DELETE),
            (r"(?i)remove\s+(?:file\s+)?['\"]([^'\"]+)['\"].*\?", ConfirmationType.FILE_DELETE),
            (r"(?i)read\s+(?:file\s+)?['\"]([^'\"]+)['\"].*\?", ConfirmationType.FILE_READ),
            # Command execution
            (
                r"(?i)execute\s+(?:command\s+)?['\"]([^'\"]+)['\"].*\?",
                ConfirmationType.COMMAND_EXECUTE,
            ),
            (r"(?i)run\s+(?:command\s+)?['\"]([^'\"]+)['\"].*\?", ConfirmationType.COMMAND_EXECUTE),
            # Package management
            (
                r"(?i)install\s+(?:package\s+)?['\"]?([^'\"?\s]+)['\"]?.*\?",
                ConfirmationType.PACKAGE_INSTALL,
            ),
            # Generic permission
            (
                r"(?i)(?:do\s+you\s+want\s+to\s+)?(?:proceed|continue).*\?",
                ConfirmationType.PERMISSION_REQUEST,
            ),
            (r"(?i)allow.*\(y/n\)", ConfirmationType.PERMISSION_REQUEST),
            (r"(?i)approve.*\?", ConfirmationType.PERMISSION_REQUEST),
        ]

        self.logger.info(
            f"Enhanced Interactive Worker Manager initialized",
            platform=self.platform,
            expect_module=expect_module.__name__,
        )

    def spawn_worker(
        self, worker_id: str, task: Dict[str, Any], timeout: int = 300, worker_type: str = "claude"
    ) -> Optional[WorkerSession]:
        """
        Spawn worker in interactive mode with pseudo-terminal

        Args:
            worker_id: Unique worker identifier
            task: Task dictionary with 'name' and 'prompt'
            timeout: Default timeout for expect operations
            worker_type: Type of worker ("claude" or "codex")

        Returns:
            WorkerSession if successful, None otherwise
        """
        worker_name = f"worker_{worker_id}"
        worker_dir = Path(self.config.workspace_root) / worker_name
        worker_dir.mkdir(parents=True, exist_ok=True)

        # Create task file
        task_file = worker_dir / "task.txt"
        with open(task_file, "w", encoding="utf-8") as f:
            f.write(task["prompt"])

        # NEW: Create raw terminal output file
        raw_terminal_file = worker_dir / "raw_terminal.log"
        # Clear existing file if any
        with open(raw_terminal_file, "w", encoding="utf-8") as f:
            f.write(f"=== Worker Terminal Output: {worker_name} ===\n")
            f.write(f"=== Task: {task['name']} ===\n")
            f.write(f"=== Started: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")

        print(f"\n[SPAWN-ENHANCED] {worker_name}: {task['name']}")
        print(f"  Platform: {self.platform}")
        print(f"  Workspace: {worker_dir}")

        self.logger.log_worker_spawn(worker_name, task["name"])

        # Build command (WITHOUT --dangerously-skip-permissions for Claude, WITH for Codex)
        cmd = self._build_command(str(task_file), worker_type=worker_type)

        print(f"  Worker Type: {worker_type}")
        print(f"  Command: {cmd}")

        try:
            # Spawn with pexpect/wexpect
            if self.platform == "windows":
                child = expect_module.spawn(cmd, encoding="utf-8", timeout=timeout)
            else:
                child = expect_module.spawn(cmd, encoding="utf-8", timeout=timeout)

            # Create orchestrator terminal capture
            orchestrator_capture = OrchestratorTerminalCapture(
                workspace_dir=worker_dir, worker_id=worker_name
            )

            # Create session
            session = WorkerSession(
                worker_id=worker_name,
                task_name=task["name"],
                child_process=child,
                started_at=time.time(),
                workspace_dir=worker_dir,
                raw_terminal_file=raw_terminal_file,  # NEW
                orchestrator_capture=orchestrator_capture,  # NEW
            )

            self.workers[worker_name] = session

            orchestrator_capture.log("Worker spawned successfully", "OK")

            # Record worker spawn metric (Phase 2.2)
            self.metrics.record_worker_spawned(worker_name)

            return session

        except Exception as e:
            self.logger.error(f"Failed to spawn worker {worker_name}: {str(e)}")
            print(f"  [ERROR] Failed to spawn: {str(e)}\n")
            return None

    def _append_raw_output(self, session: WorkerSession, text: str) -> None:
        """
        Append text to both session.output_lines and raw_terminal.log file

        Args:
            session: Worker session
            text: Text to append
        """
        # Strip ANSI codes for clean web display (Phase 2.1)
        clean_text = strip_ansi_codes(text)

        session.output_lines.append(clean_text)

        # Update last output time for metrics (Phase 2.2)
        session.last_output_time = time.time()

        # Also write to raw terminal log file
        if session.raw_terminal_file:
            try:
                with open(session.raw_terminal_file, "a", encoding="utf-8") as f:
                    f.write(clean_text)
                    if not clean_text.endswith("\n"):
                        f.write("\n")
                    f.flush()  # Force immediate write to disk for real-time streaming
            except Exception as e:
                self.logger.error(f"Failed to write to raw terminal log: {e}")

    def _poll_pending_output(self, session: WorkerSession) -> bool:
        """
        Poll for any pending output from worker process (Phase 2.2 - Continuous Polling).

        This method uses non-blocking reads to capture output that might be generated
        between confirmation requests, eliminating capture gaps.

        Args:
            session: Worker session to poll

        Returns:
            True if output was captured, False otherwise
        """
        try:
            # Try non-blocking read
            # Note: wexpect doesn't support 'timeout' parameter, use size only
            pending = session.child_process.read_nonblocking(
                size=8192  # Read up to 8KB at once
            )

            if pending and pending.strip():
                # Output found - append it
                self._append_raw_output(session, pending)
                return True

        except expect_module.TIMEOUT:
            # No output available - this is normal
            pass
        except expect_module.EOF:
            # Process ended - will be caught by main loop
            pass
        except Exception as e:
            # Unexpected error - log but don't fail
            self.logger.debug(f"Error polling output: {e}")

        return False

    def _convert_to_wsl_path(self, windows_path: str) -> str:
        """
        Convert Windows path to WSL path

        Example: D:\\user\\file.txt -> /mnt/d/user/file.txt
        """
        import re

        # Replace backslashes with forward slashes
        path = windows_path.replace("\\", "/")
        # Convert drive letter (D:/ -> /mnt/d/)
        path = re.sub(r"^([A-Za-z]):", lambda m: f"/mnt/{m.group(1).lower()}", path)
        return path

    def _build_command(self, task_file: str, worker_type: str = "claude") -> str:
        """
        Build command for interactive AI CLI execution (Claude or Codex)

        Args:
            task_file: Path to task file
            worker_type: Type of worker ("claude" or "codex")

        Returns:
            Command string for pexpect/wexpect
        """
        if worker_type == "codex":
            # Codex: Full auto mode with workspace-write sandbox
            # IMPORTANT: --json flag is required for proper non-interactive execution
            codex_flags = "--json --dangerously-bypass-approvals-and-sandbox --model gpt-5"

            if self.config.execution_mode == "wsl":
                # WSL mode - convert Windows path to WSL path
                wsl_task_file = self._convert_to_wsl_path(task_file)
                return (
                    f"wsl -d {self.config.wsl_distribution} bash -c "
                    f"\"export PATH='{self.config.nvm_path}:$PATH' && "
                    f"{self.config.codex_command} exec {codex_flags} < '{wsl_task_file}'\""
                )
            elif self.config.execution_mode == "windows":
                # Windows native mode
                if self.config.git_bash_path:
                    # Use Git Bash on Windows
                    return (
                        f'"{self.config.git_bash_path}" -c '
                        f"\"{self.config.windows_codex_path} exec {codex_flags} < '{task_file}'\""
                    )
                else:
                    # Direct Windows command
                    return f'cmd /c "{self.config.windows_codex_path} exec {codex_flags} < "{task_file}""'
            else:
                # Native Linux/Unix
                return f"{self.config.codex_command} exec {codex_flags} < {task_file}"

        else:
            # Claude: Interactive mode with confirmation support
            # Basic flags only - NO --dangerously-skip-permissions
            flags = ["--print"]
            flags_str = " ".join(flags)

            # Use config.execution_mode instead of self.platform
            if self.config.execution_mode == "wsl":
                # WSL mode - convert Windows path to WSL path
                wsl_task_file = self._convert_to_wsl_path(task_file)
                return (
                    f"wsl -d {self.config.wsl_distribution} bash -c "
                    f"\"export PATH='{self.config.nvm_path}:$PATH' && "
                    f"{self.config.claude_command} {flags_str} < '{wsl_task_file}'\""
                )
            elif self.config.execution_mode == "windows":
                # Windows native mode
                if self.config.git_bash_path:
                    # Use Git Bash on Windows
                    return (
                        f'"{self.config.git_bash_path}" -c '
                        f"\"export CLAUDE_CODE_GIT_BASH_PATH='{self.config.git_bash_path}' && "
                        f"{self.config.windows_claude_path} {flags_str} < '{task_file}'\""
                    )
                else:
                    # Direct Windows command
                    return f'cmd /c "{self.config.windows_claude_path} {flags_str} < "{task_file}""'
            else:
                # Native Linux/Unix
                return f"{self.config.claude_command} {flags_str} < {task_file}"

    def run_interactive_session(self, worker_id: str, max_iterations: int = 100) -> TaskResult:
        """
        Run interactive session for a worker

        Args:
            worker_id: Worker identifier
            max_iterations: Maximum number of interaction rounds

        Returns:
            TaskResult with output and status
        """
        session = self.workers.get(worker_id)
        if not session:
            return TaskResult(
                worker_id=worker_id,
                name="Unknown",
                output="",
                success=False,
                error_message="Worker session not found",
            )

        print(f"\n[INTERACTIVE-SESSION] {worker_id}")
        print(f"  Max iterations: {max_iterations}")
        print(f"  Monitoring for confirmations...\n")

        iteration = 0

        try:
            while iteration < max_iterations:
                iteration += 1

                # Phase 2.2: Poll for any pending output before waiting for patterns
                # This helps capture output that arrives between confirmations
                self._poll_pending_output(session)

                # Build pattern list for expect
                patterns = [p[0] for p in self.confirmation_patterns]
                patterns.append(expect_module.EOF)
                patterns.append(expect_module.TIMEOUT)

                try:
                    # Wait for pattern match
                    # Phase 2.2: Reduced timeout from 30s to 3s for more frequent polling
                    index = session.child_process.expect(patterns, timeout=3)

                    # Capture output before match
                    before_text = session.child_process.before
                    if before_text:
                        self._append_raw_output(session, before_text)  # NEW: Use helper method
                        if session.orchestrator_capture:
                            session.orchestrator_capture.log(before_text.strip(), "OUTPUT")

                        # NEW: Log to dialogue transcript
                        session.dialogue_transcript.append(
                            {
                                "timestamp": time.time(),
                                "direction": "worker→orchestrator",
                                "content": before_text,
                                "type": "output",
                            }
                        )

                    # Check if EOF (completed)
                    if index == len(patterns) - 2:  # EOF
                        if session.orchestrator_capture:
                            session.orchestrator_capture.log("Worker finished (EOF)", "COMPLETE")
                        break

                    # Check if timeout
                    if index == len(patterns) - 1:  # TIMEOUT
                        # Phase 2.2: Poll for pending output on timeout
                        output_found = self._poll_pending_output(session)
                        if not output_found and session.orchestrator_capture:
                            session.orchestrator_capture.log("Polling (no new output)", "POLL")
                        # Continue anyway, might just be processing
                        continue

                    # Confirmation detected
                    confirmation = self._parse_confirmation(worker_id, index, session.child_process)

                    if confirmation:
                        # Phase 2.2: Increment confirmation counter for metrics
                        session.confirmation_count += 1

                        # Phase 2.2: Record confirmation metrics
                        decision_start_time = time.time()

                        # Handle confirmation
                        response = self._handle_confirmation(confirmation)

                        # Phase 2.2: Calculate decision latency and record metric
                        decision_latency_ms = (time.time() - decision_start_time) * 1000
                        self.metrics.record_confirmation(
                            worker_id=worker_id,
                            confirmation_number=session.confirmation_count,
                            orchestrator_latency_ms=decision_latency_ms,
                            response="approved" if response else "skipped",
                        )

                        # Send response
                        if response:
                            session.child_process.sendline(response)
                            if session.orchestrator_capture:
                                session.orchestrator_capture.log(response, "SENT")

                            # NEW: Log orchestrator response to dialogue transcript
                            session.dialogue_transcript.append(
                                {
                                    "timestamp": time.time(),
                                    "direction": "orchestrator→worker",
                                    "content": response,
                                    "type": "response",
                                    "confirmation_type": confirmation.confirmation_type.value,
                                    "confirmation_message": confirmation.message,
                                }
                            )
                        else:
                            if session.orchestrator_capture:
                                session.orchestrator_capture.log("No response sent", "SKIP")

                except expect_module.TIMEOUT:
                    if session.orchestrator_capture:
                        session.orchestrator_capture.log(f"Iteration {iteration}", "TIMEOUT")
                    continue

                except expect_module.EOF:
                    if session.orchestrator_capture:
                        session.orchestrator_capture.log(
                            "Worker finished (EOF exception)", "COMPLETE"
                        )
                    break

            # Capture any remaining output
            try:
                remaining = session.child_process.read()
                if remaining:
                    self._append_raw_output(session, remaining)  # NEW: Use helper method
                    if session.orchestrator_capture:
                        session.orchestrator_capture.log(remaining.strip(), "FINAL-OUTPUT")
            except:
                pass

            # Calculate result
            duration = time.time() - session.started_at
            output = "\n".join(session.output_lines)

            # Check exit status
            session.child_process.close()
            exit_code = session.child_process.exitstatus

            # Determine success: exit code 0 OR (exit code is None but output indicates completion)
            if exit_code == 0:
                success = True
            elif exit_code is not None:
                success = False
            else:
                # Exit code is None - check output for completion indicators
                completion_patterns = [
                    "completed!",
                    "completed",
                    "finished",
                    "done",
                    "success",
                ]
                success = any(pattern.lower() in output.lower() for pattern in completion_patterns)

            result = TaskResult(
                worker_id=worker_id,
                name=session.task_name,
                output=output,
                success=success,
                duration=duration,
                error_message=None if success else f"Exit code: {exit_code}",
            )

            # NEW: Save dialogue transcript to files
            self._save_dialogue_transcript(session)

            # Phase 2.2: Record worker completion metrics
            if success:
                self.metrics.record_worker_completed(worker_id)
            else:
                self.metrics.record_worker_failed(worker_id)

            print(f"\n[RESULT] {worker_id}")
            print(f"  Success: {result.success}")
            print(f"  Duration: {duration:.1f}s")
            print(f"  Output length: {len(output)} chars\n")

            return result

        except Exception as e:
            self.logger.error(f"Error in interactive session for {worker_id}: {str(e)}")

            # Phase 2.2: Record worker failure on exception
            self.metrics.record_worker_failed(worker_id)

            return TaskResult(
                worker_id=worker_id,
                name=session.task_name,
                output="\n".join(session.output_lines),
                success=False,
                duration=time.time() - session.started_at,
                error_message=str(e),
            )

    def _parse_confirmation(
        self, worker_id: str, pattern_index: int, child_process: Any
    ) -> Optional[ConfirmationRequest]:
        """
        Parse confirmation from matched pattern

        Args:
            worker_id: Worker identifier
            pattern_index: Index of matched pattern
            child_process: pexpect/wexpect child process

        Returns:
            ConfirmationRequest if parsed successfully
        """
        if pattern_index >= len(self.confirmation_patterns):
            return None

        pattern, conf_type = self.confirmation_patterns[pattern_index]

        # Get matched text
        matched_text = child_process.after

        # Extract details from regex groups
        match = child_process.match
        details = {}

        if match and match.groups():
            # First group usually contains the target (file, command, etc.)
            target = match.group(1) if len(match.groups()) >= 1 else ""

            if conf_type == ConfirmationType.FILE_WRITE:
                details["file"] = target
            elif conf_type == ConfirmationType.FILE_DELETE:
                details["file"] = target
            elif conf_type == ConfirmationType.FILE_READ:
                details["file"] = target
            elif conf_type == ConfirmationType.COMMAND_EXECUTE:
                details["command"] = target
            elif conf_type == ConfirmationType.PACKAGE_INSTALL:
                details["package"] = target

        confirmation = ConfirmationRequest(
            worker_id=worker_id,
            confirmation_type=conf_type,
            message=matched_text.strip() if matched_text else "",
            details=details,
        )

        print(f"\n  [CONFIRMATION-DETECTED]")
        print(f"    Type: {conf_type}")
        print(f"    Message: {confirmation.message}")
        print(f"    Details: {details}")

        return confirmation

    def _handle_confirmation(self, confirmation: ConfirmationRequest) -> Optional[str]:
        """
        Handle confirmation request with AI safety judgment

        Args:
            confirmation: The confirmation request

        Returns:
            Response string ("yes" or "no") or None
        """
        print(f"  [HANDLING-CONFIRMATION]")

        # Import hybrid engine adapter
        from orchestrator.core.hybrid_integration import AISafetyJudge

        # Create safety judge (now using hybrid engine)
        judge = AISafetyJudge(
            workspace_root=str(self.config.workspace_root),
            wsl_distribution="Ubuntu-24.04",
            verbose=False,  # Set to True for debugging
        )

        # Get judgment
        judgment = judge.judge_confirmation(confirmation)

        print(f"    AI Safety Level: {judgment.level}")
        print(f"    Should Approve: {judgment.should_approve}")
        print(f"    Should Escalate: {judgment.should_escalate}")
        print(f"    Reasoning: {judgment.reasoning}")

        # Auto-approve safe operations
        if judgment.should_approve and not judgment.should_escalate:
            # Enhanced logging with safety level detail
            if judgment.level == SafetyLevel.SAFE:
                print(f"    Decision: AUTO-APPROVE:SAFE")
                print(f"    Details: {judgment.reasoning}")
            else:
                print(f"    Decision: AUTO-APPROVE:{judgment.level.value.upper()}")

            self.logger.info(
                "Auto-approved safe operation",
                worker_id=confirmation.worker_id,
                type=confirmation.confirmation_type,
                level=judgment.level,
            )
            return "yes"

        # Escalate to user if needed
        if judgment.should_escalate:
            # Enhanced logging with safety level detail
            if judgment.level == SafetyLevel.CAUTION:
                print(f"    Decision: ESCALATE:CAUTION")
                print(f"    Details: {judgment.reasoning}")
            elif judgment.level == SafetyLevel.DANGEROUS:
                print(f"    Decision: ESCALATE:DANGEROUS")
                print(f"    Details: {judgment.reasoning}")
                if judgment.suggested_modifications:
                    print(f"    Suggestion: {judgment.suggested_modifications}")
            else:
                print(f"    Decision: ESCALATE:{judgment.level.value.upper()}")

            if self.user_approval_callback:
                approved = self.user_approval_callback(confirmation)
                response = "yes" if approved else "no"

                print(f"    User Response: {response}")

                self.logger.info(
                    "User decision on escalated operation",
                    worker_id=confirmation.worker_id,
                    type=confirmation.confirmation_type,
                    approved=approved,
                    level=judgment.level,
                )

                return response
            else:
                # No callback - deny for safety
                print(f"    Decision: DENY (no user callback)")

                self.logger.warning(
                    "Denied operation - no user callback available",
                    worker_id=confirmation.worker_id,
                    type=confirmation.confirmation_type,
                    level=judgment.level,
                )

                return "no"

        # Prohibited operations
        if judgment.level == SafetyLevel.PROHIBITED:
            print(f"    Decision: DENY:PROHIBITED")
            print(f"    Details: {judgment.reasoning}")

            self.logger.warning(
                "Denied prohibited operation",
                worker_id=confirmation.worker_id,
                type=confirmation.confirmation_type,
                reasoning=judgment.reasoning,
            )

            return "no"

        # Default: deny if unsure
        print(f"    Decision: DENY (default)")

        self.logger.warning(
            "Denied uncertain operation",
            worker_id=confirmation.worker_id,
            type=confirmation.confirmation_type,
        )

        return "no"

    def _save_dialogue_transcript(self, session: WorkerSession) -> None:
        """
        Save complete dialogue transcript to files

        Args:
            session: Worker session with dialogue transcript
        """
        if not session.workspace_dir or not session.dialogue_transcript:
            return

        import json
        from datetime import datetime

        try:
            # Save as JSONL (machine-readable)
            jsonl_file = session.workspace_dir / "dialogue_transcript.jsonl"
            with open(jsonl_file, "w", encoding="utf-8") as f:
                for entry in session.dialogue_transcript:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

            # Save as TXT (human-readable)
            txt_file = session.workspace_dir / "dialogue_transcript.txt"
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write(f"DIALOGUE TRANSCRIPT: {session.worker_id}\n")
                f.write(f"Task: {session.task_name}\n")
                f.write(
                    f"Started: {datetime.fromtimestamp(session.started_at).strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write("=" * 80 + "\n\n")

                for entry in session.dialogue_transcript:
                    timestamp_str = datetime.fromtimestamp(entry["timestamp"]).strftime(
                        "%H:%M:%S.%f"
                    )[:-3]
                    direction = entry["direction"]
                    content = entry["content"]
                    entry_type = entry.get("type", "unknown")

                    f.write(f"[{timestamp_str}] {direction} ({entry_type})\n")

                    # Add confirmation details if present
                    if "confirmation_type" in entry:
                        f.write(f"  Confirmation Type: {entry['confirmation_type']}\n")
                        f.write(
                            f"  Confirmation Message: {entry.get('confirmation_message', 'N/A')}\n"
                        )

                    f.write(f"{'-' * 80}\n")
                    f.write(f"{content}\n")
                    f.write(f"{'=' * 80}\n\n")

            print(f"  [TRANSCRIPT-SAVED] {jsonl_file.name}, {txt_file.name}")

        except Exception as e:
            self.logger.error(
                f"Failed to save dialogue transcript for {session.worker_id}: {str(e)}"
            )
            print(f"  [ERROR] Failed to save transcript: {str(e)}")

    def spawn_codex_worker(
        self, worker_id: str, task: Dict[str, Any], timeout: int = 300
    ) -> Optional[Path]:
        """
        Spawn Codex worker (non-interactive, subprocess-based).

        Unlike spawn_worker(), this does NOT use pexpect. It prepares the workspace
        and task file, but execution happens via run_codex_session().

        Args:
            worker_id: Unique worker identifier
            task: Task dictionary with 'name' and 'prompt'
            timeout: Execution timeout (not used here, passed to run_codex_session)

        Returns:
            Path to worker directory if successful, None otherwise
        """
        worker_name = f"worker_{worker_id}"
        worker_dir = Path(self.config.workspace_root) / worker_name
        worker_dir.mkdir(parents=True, exist_ok=True)

        # Create task file
        task_file = worker_dir / "task.txt"
        try:
            with open(task_file, "w", encoding="utf-8") as f:
                f.write(task["prompt"])

            print(f"\n[SPAWN-CODEX] {worker_name}: {task['name']}")
            print(f"  Workspace: {worker_dir}")
            print(f"  Task file: {task_file}")

            self.logger.log_worker_spawn(worker_name, task["name"])

            # Record worker spawn metric
            self.metrics.record_worker_spawned(worker_name)

            # Store minimal session info (no pexpect process)
            self.workers[worker_name] = WorkerSession(
                worker_id=worker_name,
                task_name=task["name"],
                child_process=None,  # No pexpect process for Codex
                started_at=time.time(),
                workspace_dir=worker_dir,
            )

            return worker_dir

        except Exception as e:
            self.logger.error(f"Failed to spawn Codex worker {worker_name}: {str(e)}")
            print(f"  [ERROR] Failed to spawn: {str(e)}\n")
            return None

    def run_codex_session(
        self, worker_id: str, timeout: int = 300, model: str = "gpt-5"
    ) -> TaskResult:
        """
        Run Codex worker session using subprocess-based executor.

        This method:
        1. Retrieves worker session info
        2. Executes Codex CLI via CodexExecutor (subprocess.Popen)
        3. Parses JSONL events
        4. Tracks file changes
        5. Returns TaskResult

        Args:
            worker_id: Worker identifier (must be spawned first via spawn_codex_worker)
            timeout: Execution timeout in seconds (default: 300)
            model: Model to use (default: gpt-5)

        Returns:
            TaskResult with output, file changes, and status
        """
        session = self.workers.get(worker_id)
        if not session:
            return TaskResult(
                worker_id=worker_id,
                name="Unknown",
                output="",
                success=False,
                error_message="Codex worker session not found",
            )

        print(f"\n[CODEX-SESSION] {worker_id}")
        print(f"  Task: {session.task_name}")
        print(f"  Timeout: {timeout}s")
        print(f"  Model: {model}\n")

        assert session.workspace_dir is not None, "Workspace directory must be set"

        task_file = session.workspace_dir / "task.txt"

        try:
            # Execute via CodexExecutor
            exec_result: CodexExecutionResult = self.codex_executor.execute(
                task_file=task_file, workspace_dir=session.workspace_dir, timeout=timeout, model=model
            )

            # Save execution logs
            self._save_codex_logs(session, exec_result)

            # Convert to TaskResult
            task_result = TaskResult(
                worker_id=worker_id,
                name=session.task_name,
                output=exec_result.stdout,
                success=exec_result.success,
                duration=exec_result.duration_seconds,
                error_message=exec_result.error_message,
            )

            # Record metrics
            if task_result.success:
                self.metrics.record_worker_completed(worker_id)
            else:
                self.metrics.record_worker_failed(worker_id)

            # Print summary
            print(f"\n[CODEX-RESULT] {worker_id}")
            print(f"  Success: {task_result.success}")
            print(f"  Duration: {task_result.duration:.1f}s")
            print(f"  Created files: {exec_result.created_files}")
            print(f"  Events: {len(exec_result.events)}")
            if exec_result.usage:
                print(
                    f"  Tokens: {exec_result.usage.input_tokens} in, {exec_result.usage.output_tokens} out"
                )
            print()

            return task_result

        except Exception as e:
            self.logger.error(f"Error in Codex session for {worker_id}: {str(e)}")

            # Record failure metric
            self.metrics.record_worker_failed(worker_id)

            return TaskResult(
                worker_id=worker_id,
                name=session.task_name,
                output="",
                success=False,
                duration=time.time() - session.started_at,
                error_message=f"Codex execution error: {str(e)}",
            )

    def _save_codex_logs(self, session: WorkerSession, exec_result: CodexExecutionResult) -> None:
        """
        Save Codex execution logs to workspace directory.

        Args:
            session: Worker session
            exec_result: Codex execution result
        """
        if not session.workspace_dir:
            return

        try:
            import json
            from datetime import datetime

            # Save JSONL events
            events_file = session.workspace_dir / "codex_events.jsonl"
            with open(events_file, "w", encoding="utf-8") as f:
                for event in exec_result.events:
                    f.write(json.dumps(event.model_dump(), ensure_ascii=False) + "\n")

            # Save execution summary
            summary_file = session.workspace_dir / "codex_summary.txt"
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write(f"CODEX EXECUTION SUMMARY: {session.worker_id}\n")
                f.write(f"Task: {session.task_name}\n")
                f.write(
                    f"Started: {datetime.fromtimestamp(session.started_at).strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write("=" * 80 + "\n\n")

                f.write(f"Status: {exec_result.status.value}\n")
                f.write(f"Exit Code: {exec_result.exit_code}\n")
                f.write(f"Duration: {exec_result.duration_seconds:.1f}s\n")
                f.write(f"Events: {len(exec_result.events)}\n")
                f.write(f"File Changes: {len(exec_result.file_changes)}\n")

                if exec_result.usage:
                    f.write(f"\nToken Usage:\n")
                    f.write(f"  Input: {exec_result.usage.input_tokens}\n")
                    f.write(f"  Output: {exec_result.usage.output_tokens}\n")

                if exec_result.created_files:
                    f.write(f"\nCreated Files:\n")
                    for file_path in exec_result.created_files:
                        f.write(f"  - {file_path}\n")

                if exec_result.modified_files:
                    f.write(f"\nModified Files:\n")
                    for file_path in exec_result.modified_files:
                        f.write(f"  - {file_path}\n")

                if exec_result.error_message:
                    f.write(f"\nError Message:\n")
                    f.write(f"  {exec_result.error_message}\n")

                f.write("\n" + "=" * 80 + "\n")
                f.write("STDOUT:\n")
                f.write("=" * 80 + "\n")
                f.write(exec_result.stdout)

                if exec_result.stderr:
                    f.write("\n" + "=" * 80 + "\n")
                    f.write("STDERR:\n")
                    f.write("=" * 80 + "\n")
                    f.write(exec_result.stderr)

            print(f"  [LOGS-SAVED] {events_file.name}, {summary_file.name}")

        except Exception as e:
            self.logger.error(f"Failed to save Codex logs for {session.worker_id}: {str(e)}")
            print(f"  [ERROR] Failed to save logs: {str(e)}")

    def run_worker_in_thread(self, worker_id: str) -> Tuple[str, TaskResult]:
        """
        Run a single worker in current thread (helper for parallel execution)

        Args:
            worker_id: Worker identifier

        Returns:
            Tuple of (worker_id, TaskResult)
        """
        try:
            result = self.run_interactive_session(worker_id)
            return (worker_id, result)
        except Exception as e:
            # Create error result
            session = self.workers.get(worker_id)
            error_result = TaskResult(
                worker_id=worker_id,
                name=session.task_name if session else "Unknown",
                output="",
                success=False,
                duration=0.0,
                error_message=f"Thread execution error: {str(e)}",
            )
            return (worker_id, error_result)

    def wait_all(self, max_workers: Optional[int] = None, timeout: int = 1800) -> List[TaskResult]:
        """
        Wait for all workers to complete in PARALLEL using thread pool

        Args:
            max_workers: Maximum number of concurrent workers (default: number of spawned workers)
            timeout: Maximum time to wait for all workers (default: 1800 seconds = 30 minutes)

        Returns:
            List of task results (order matches workers dict order)

        Note: All workers execute in parallel simultaneously. This is the only execution mode.
        """
        worker_ids = list(self.workers.keys())

        if not worker_ids:
            self.logger.info("No workers to execute")
            return []

        # Default max_workers to number of spawned workers
        if max_workers is None:
            max_workers = len(worker_ids)

        self.logger.info(
            f"Starting parallel execution",
            worker_count=len(worker_ids),
            max_workers=max_workers,
            timeout=timeout,
        )

        print(f"\n{'='*80}")
        print(f"PARALLEL EXECUTION: {len(worker_ids)} workers")
        print(f"Max concurrent: {max_workers}")
        print(f"Timeout: {timeout}s")
        print(f"{'='*80}\n")

        results_dict = {}
        start_time = time.time()

        # Execute workers in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all workers
            future_to_worker = {
                executor.submit(self.run_worker_in_thread, worker_id): worker_id
                for worker_id in worker_ids
            }

            # Track progress
            completed_count = 0
            total_count = len(worker_ids)

            # Collect results as they complete
            for future in as_completed(future_to_worker, timeout=timeout):
                worker_id = future_to_worker[future]

                try:
                    result_worker_id, result = future.result()
                    results_dict[result_worker_id] = result

                    completed_count += 1
                    elapsed = time.time() - start_time

                    print(f"\n[PROGRESS] {completed_count}/{total_count} completed")
                    print(f"  Worker: {result_worker_id}")
                    print(f"  Success: {result.success}")
                    print(f"  Duration: {result.duration:.1f}s")
                    print(f"  Elapsed: {elapsed:.1f}s\n")

                    self.logger.info(
                        f"Worker completed",
                        worker_id=result_worker_id,
                        success=result.success,
                        duration=result.duration,
                        progress=f"{completed_count}/{total_count}",
                    )

                except Exception as e:
                    # Handle execution exception
                    error_result = TaskResult(
                        worker_id=worker_id,
                        name="Unknown",
                        output="",
                        success=False,
                        duration=0.0,
                        error_message=f"Future execution error: {str(e)}",
                    )
                    results_dict[worker_id] = error_result

                    completed_count += 1

                    print(f"\n[ERROR] Worker {worker_id} failed: {str(e)}\n")

                    self.logger.error(
                        f"Worker failed",
                        worker_id=worker_id,
                        error=str(e),
                        progress=f"{completed_count}/{total_count}",
                    )

        total_elapsed = time.time() - start_time

        print(f"\n{'='*80}")
        print(f"PARALLEL EXECUTION COMPLETE")
        print(f"{'='*80}")
        print(f"Total workers: {total_count}")
        print(f"Completed: {completed_count}")
        print(f"Total time: {total_elapsed:.1f}s")
        print(f"{'='*80}\n")

        self.logger.info(
            f"Parallel execution complete",
            total_workers=total_count,
            completed=completed_count,
            total_time=total_elapsed,
        )

        # Return results in original worker order
        results = [results_dict.get(worker_id) for worker_id in worker_ids]

        # Filter out None values (shouldn't happen, but just in case)
        results = [r for r in results if r is not None]

        return results

    # Supervisor methods for Worker 2 Manager AI Integration
    async def spawn_supervised_worker(
        self, task_file: str, workspace_root: str, timeout: int = 300
    ) -> SupervisedWorkerResult:
        """Spawn supervised Claude Code worker.

        Creates a new supervised worker process that executes a task file
        within a workspace, with real-time monitoring and control.

        Args:
            task_file: Path to task markdown file
            workspace_root: Workspace root directory
            timeout: Execution timeout in seconds (default: 300)

        Returns:
            SupervisedWorkerResult with supervisor_id and initial status

        Raises:
            ValueError: If task_file or workspace_root is invalid
            RuntimeError: If supervisor spawn fails

        Examples:
            >>> result = await manager.spawn_supervised_worker(
            ...     task_file="tasks/WORKER_2.md",
            ...     workspace_root="workspace/worker_2",
            ...     timeout=600
            ... )
            >>> assert result.status == SupervisorStatus.SPAWNING
        """
        # TODO: Full implementation in future sprint
        # For now, return a stub response to allow API integration testing
        raise NotImplementedError(
            "Supervisor integration pending - scheduled for Week 3. "
            "Current implementation provides API layer only."
        )

    async def get_supervisor_status(self, worker_id: str) -> Optional[SupervisorStatusInfo]:
        """Get supervisor status information.

        Retrieves detailed status for a specific supervisor process.

        Args:
            worker_id: Supervisor identifier

        Returns:
            SupervisorStatusInfo if supervisor exists, None otherwise

        Examples:
            >>> status = await manager.get_supervisor_status("worker_2")
            >>> if status:
            ...     print(f"Status: {status.status}, Alive: {status.alive}")
        """
        # TODO: Full implementation in future sprint
        # For now, return None to indicate supervisor not found
        return None

    async def terminate_supervisor(self, worker_id: str) -> bool:
        """Terminate a running supervisor.

        Gracefully terminates a supervisor process and cleans up resources.

        Args:
            worker_id: Supervisor identifier

        Returns:
            True if termination successful, False if supervisor not found

        Examples:
            >>> terminated = await manager.terminate_supervisor("worker_2")
            >>> assert terminated is True
        """
        # TODO: Full implementation in future sprint
        # For now, return False to indicate supervisor not found
        return False

    async def list_supervisors(self) -> List[SupervisorStatusInfo]:
        """List all active supervisors.

        Returns a list of status information for all running supervisors.

        Returns:
            List of SupervisorStatusInfo objects (empty if none active)

        Examples:
            >>> supervisors = await manager.list_supervisors()
            >>> for sup in supervisors:
            ...     print(f"{sup.supervisor_id}: {sup.status}")
        """
        # TODO: Full implementation in future sprint
        # For now, return empty list
        return []

    async def record_confirmation_response(
        self, worker_id: str, decision: str, reason: str
    ) -> bool:
        """Record a confirmation response for a supervisor.

        Records user decision (APPROVE/DENY/ESCALATE) for a confirmation prompt.

        Args:
            worker_id: Supervisor identifier
            decision: Decision ("APPROVE", "DENY", or "ESCALATE")
            reason: Reason for decision

        Returns:
            True if response recorded, False if supervisor not found

        Raises:
            ValueError: If decision is not one of the allowed values

        Examples:
            >>> recorded = await manager.record_confirmation_response(
            ...     worker_id="worker_2",
            ...     decision="APPROVE",
            ...     reason="Task is safe to execute"
            ... )
            >>> assert recorded is True
        """
        if decision not in ("APPROVE", "DENY", "ESCALATE"):
            raise ValueError(
                f"Invalid decision: {decision}. Must be 'APPROVE', 'DENY', or 'ESCALATE'."
            )

        # TODO: Full implementation in future sprint
        # For now, return False to indicate supervisor not found
        return False

    async def get_output(self, worker_id: str) -> Optional[List[Tuple[float, str]]]:
        """Get buffered output from supervisor.

        Retrieves timestamped output lines from a supervisor's buffer.

        Args:
            worker_id: Supervisor identifier

        Returns:
            List of (timestamp, line) tuples if supervisor exists, None otherwise

        Examples:
            >>> output = await manager.get_output("worker_2")
            >>> if output:
            ...     for timestamp, line in output:
            ...         print(f"[{timestamp}] {line}")
        """
        # TODO: Full implementation in future sprint
        # For now, return None to indicate supervisor not found
        return None


# Example usage
if __name__ == "__main__":
    from orchestrator.config import OrchestratorConfig

    # Simple logger for demo
    class SimpleLogger:
        def log_worker_spawn(self, worker_id: str, task_name: str, **kwargs: Any) -> None:
            print(f"[LOG] Spawned: {worker_id} - {task_name}")

        def log_worker_complete(self, worker_id: str, output_size: int, **kwargs: Any) -> None:
            print(f"[LOG] Completed: {worker_id} - {output_size} bytes")

        def log_task_error(self, task_id: str, task_name: str, error: str, **kwargs: Any) -> None:
            print(f"[LOG] Task Error: {task_id} - {task_name}: {error}")

        def debug(self, message: str, **kwargs: Any) -> None:
            print(f"[DEBUG] {message} | {kwargs}")

        def info(self, message: str, **kwargs: Any) -> None:
            print(f"[INFO] {message} | {kwargs}")

        def warning(self, message: str, **kwargs: Any) -> None:
            print(f"[WARN] {message} | {kwargs}")

        def error(self, message: str, **kwargs: Any) -> None:
            print(f"[ERROR] {message} | {kwargs}")

    def user_approval(confirmation: ConfirmationRequest) -> bool:
        """User approval callback"""
        print(f"\n{'='*60}")
        print(f"USER APPROVAL NEEDED")
        print(f"{'='*60}")
        print(f"Worker: {confirmation.worker_id}")
        print(f"Type: {confirmation.confirmation_type}")
        print(f"Message: {confirmation.message}")
        print(f"Details: {confirmation.details}")

        response = input("\nApprove? (y/n): ").strip().lower()
        return response == "y"

    # Test
    config = OrchestratorConfig.from_env()
    logger = SimpleLogger()

    manager = WorkerManager(config=config, logger=logger, user_approval_callback=user_approval)

    task = {
        "name": "Test Interactive Mode",
        "prompt": "Create a simple Python script that prints 'Hello World' and save it to hello.py",
    }

    session = manager.spawn_worker("test_1", task)

    if session:
        result = manager.run_interactive_session(session.worker_id)

        print(f"\n{'='*60}")
        print(f"FINAL RESULT")
        print(f"{'='*60}")
        print(f"Success: {result.success}")
        print(f"Duration: {result.duration:.1f}s")
        print(f"Output:\n{result.output}")
