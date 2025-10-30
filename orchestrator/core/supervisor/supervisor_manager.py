"""Supervisor Manager implementation.

Coordinates ClaudeCodeSupervisor and the AISafetyJudge to provide
confirmation handling, retry logic, and health monitoring.
"""

from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from orchestrator.core.ai_safety_judge import AISafetyJudge, Decision
from orchestrator.core.base_ai_manager import BaseAIManager
from orchestrator.core.supervisor.claude_code_supervisor import (
    ClaudeCodeSupervisor,
    ConfirmationPrompt,
    ProcessResult,
)
from orchestrator.core.supervisor.io_handler import ProcessIOHandler

# Strategies


class ApprovalStrategy:
    """Strategy interface for confirmation decisions."""

    def decide(self, prompt: ConfirmationPrompt) -> Decision:
        raise NotImplementedError


class SafeApprovalStrategy(ApprovalStrategy):
    """Auto - approve only highly confident prompts."""

    def __init__(self, threshold: float = 0.8) -> None:
        self._threshold = threshold

    def decide(self, prompt: ConfirmationPrompt) -> Decision:
        return Decision.APPROVE if prompt.confidence >= self._threshold else Decision.ESCALATE


class EscalationStrategy(ApprovalStrategy):
    """Always escalate to human or judge."""

    def decide(self, _prompt: ConfirmationPrompt) -> Decision:
        return Decision.ESCALATE


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 0.3
    max_delay: float = 5.0


class SupervisorManager(BaseAIManager):
    """Manager for Supervisor AI logic.

    Uses dependency injection for the judge and supervisor to ease testing.
    """

    def __init__(
        self,
        workspace_root: str,
        judge: Optional[AISafetyJudge] = None,
        supervisor: Optional[ClaudeCodeSupervisor] = None,
        approval_strategy: Optional[ApprovalStrategy] = None,
    ) -> None:
        super().__init__(name="SupervisorManager")
        self._workspace_root = workspace_root
        self._judge = judge or AISafetyJudge()
        self._supervisor = supervisor or ClaudeCodeSupervisor(workspace_root)
        self._approval = approval_strategy or SafeApprovalStrategy()
        self._retry = RetryConfig()
        self._io: Optional[ProcessIOHandler] = None
        self._last_error: Optional[str] = None

    # BaseAIManager overrides
    def configure(self, config: Dict[str, object]) -> None:
        self._retry = RetryConfig(
            max_retries=int(config.get("max_retries", self._retry.max_retries)),  # type: ignore[call - overload]
            base_delay=float(config.get("base_delay", self._retry.base_delay)),  # type: ignore[arg - type]
            max_delay=float(config.get("max_delay", self._retry.max_delay)),  # type: ignore[arg - type]
        )

    async def start(self) -> None:
        # No - op here; spawning is controlled explicitly via `spawn`.
        return None

    async def stop(self) -> None:
        if self._io is not None:
            await self._io.close()
            self._io = None
        self._supervisor.terminate()

    def status(self) -> Dict[str, Optional[str]]:
        return {
            "alive": str(self._supervisor.is_alive),
            "last_error": self._last_error,
        }

    # Supervisor operations
    def spawn(self, task_file: str, timeout: int = 300) -> ProcessResult:
        result = self._supervisor.spawn_claude_code(task_file=task_file, timeout=timeout)
        if not result.success:
            self._last_error = result.error_message or "spawn failed"
        return result

    async def stream(self) -> asyncio.Task:
        handler, _child = await self._supervisor.monitor_output()
        self._io = handler

        async def _run() -> None:
            assert self._io is not None
            async for line in self._io.read_async():
                await self._handle_line(line)

        return asyncio.create_task(_run())

    async def _handle_line(self, line: str) -> None:
        prompt = self._supervisor.detect_confirmation_prompt(line)
        if not prompt:
            return
        decision = self._approval.decide(prompt)
        if decision is Decision.ESCALATE:
            judgment = self._judge.assess(prompt.text)
            decision = judgment.decision
        # In a real integration we would write back to the process; here we just record
        if decision is Decision.DENY:
            self._last_error = "confirmation denied"

    def detect_error(self, text: str) -> bool:
        lowered = text.lower()
        return any(tag in lowered for tag in ("error:", "traceback", "exception"))

    async def retry_with_backoff(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> object:
        for attempt in range(self._retry.max_retries + 1):
            try:
                return await fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                self._last_error = f"retry {attempt} failed: {type(exc).__name__}"
                if attempt >= self._retry.max_retries:
                    raise
                delay = min(self._retry.max_delay, self._retry.base_delay * math.pow(2, attempt))
                await asyncio.sleep(delay)
        raise RuntimeError("Exhausted all retries")

    def check_health(self) -> Dict[str, str]:
        status = "alive" if self._supervisor.is_alive else "dead"
        return {"process": status}
