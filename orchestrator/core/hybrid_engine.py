"""
Hybrid Decision Engine

Combines rule - based safety engine with AI judgment for optimal performance.
Simple cases are handled by fast rules, complex cases go to AI.
"""

import asyncio
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

# Handle imports for both module use and direct execution
try:
    from .cli_orchestrator import CLIOrchestratorAI
except ImportError:
    # Direct execution - add parent to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from orchestrator.core.cli_orchestrator import CLIOrchestratorAI


class ConfirmationType(Enum):
    """Types of confirmation requests"""

    FILE_WRITE = "file_write"
    FILE_READ = "file_read"
    FILE_DELETE = "file_delete"
    PACKAGE_INSTALL = "package_install"
    COMMAND_EXECUTE = "command_execute"
    GENERAL = "general"


@dataclass
class ConfirmationRequest:
    """Worker confirmation request"""

    confirmation_type: ConfirmationType
    message: str
    details: Dict[str, Any]


@dataclass
class RuleResult:
    """Result from rule - based evaluation"""

    is_definitive: bool  # True if rules give clear answer
    action: Optional[str] = None  # "approve" or "deny" if definitive
    reason: str = ""
    duration_ms: float = 0.0


@dataclass
class Decision:
    """Final decision"""

    action: str  # "approve" or "deny"
    reasoning: str
    latency_ms: float = 0.0
    is_fallback: bool = False
    decided_by: str = "unknown"  # "rules", "ai", or "template"


@dataclass
class Template:
    """Template response for errors"""

    action: str
    message: str


class ErrorTemplates:
    """
    Error templates for fallback responses

    Provides safe default responses when AI is unavailable.
    """

    def get_api_error_template(self, request: ConfirmationRequest) -> Template:
        """
        Get template for API errors

        Strategy: Approve safe operations, deny risky ones
        """

        if request.confirmation_type in [ConfirmationType.FILE_WRITE, ConfirmationType.FILE_READ]:
            # File operations in workspace - likely safe
            return Template(
                action="approve",
                message="API error occurred. Workspace file operations are typically safe - proceeding.",
            )

        elif request.confirmation_type == ConfirmationType.FILE_DELETE:
            # Deletion - be cautious
            return Template(
                action="deny", message="API error occurred. For safety, denying file deletion."
            )

        elif request.confirmation_type == ConfirmationType.PACKAGE_INSTALL:
            # Package install - depends on context
            return Template(
                action="approve",
                message="API error occurred. Package installation from requirements.txt is typically safe - proceeding.",
            )

        else:
            # Unknown operation - neutral stance
            return Template(
                action="approve", message="API error occurred. Proceeding with caution."
            )

    def get_timeout_template(self, request: ConfirmationRequest) -> Template:
        """Get template for timeout"""
        # Same logic as API error
        return self.get_api_error_template(request)


class SafetyRulesEngine:
    """
    Rule - based safety evaluation engine

    Fast pattern - matching for common cases.
    Returns definitive answer for clear cases, defers to AI for ambiguous ones.
    """

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.resolve()

    def evaluate(self, request: ConfirmationRequest) -> RuleResult:
        """
        Evaluate request using rules

        Returns:
            RuleResult with is_definitive=True if rules can decide
            RuleResult with is_definitive=False if AI judgment needed
        """

        start = time.time()

        # Check safe patterns first (auto - approve)
        safe_result = self._check_safe_patterns(request)
        if safe_result:
            safe_result.duration_ms = (time.time() - start) * 1000
            return safe_result

        # Check dangerous patterns (auto - deny)
        dangerous_result = self._check_dangerous_patterns(request)
        if dangerous_result:
            dangerous_result.duration_ms = (time.time() - start) * 1000
            return dangerous_result

        # Ambiguous - needs AI judgment
        return RuleResult(
            is_definitive=False,
            reason="Requires AI judgment",
            duration_ms=(time.time() - start) * 1000,
        )

    def _check_safe_patterns(self, request: ConfirmationRequest) -> Optional[RuleResult]:
        """Check if request matches safe patterns"""

        # File write in workspace
        if request.confirmation_type == ConfirmationType.FILE_WRITE:
            file_path = request.details.get("file", "")
            if self._is_in_workspace(file_path):
                return RuleResult(
                    is_definitive=True,
                    action="approve",
                    reason="File creation in workspace is safe",
                )

        # File read in workspace
        if request.confirmation_type == ConfirmationType.FILE_READ:
            file_path = request.details.get("file", "")
            if self._is_in_workspace(file_path):
                return RuleResult(
                    is_definitive=True, action="approve", reason="File reading in workspace is safe"
                )

        # Package install from requirements.txt
        if request.confirmation_type == ConfirmationType.PACKAGE_INSTALL:
            package = request.details.get("package", "")
            if self._is_in_requirements(package):
                return RuleResult(
                    is_definitive=True,
                    action="approve",
                    reason="Package is listed in requirements.txt",
                )

        return None

    def _check_dangerous_patterns(self, request: ConfirmationRequest) -> Optional[RuleResult]:
        """Check if request matches dangerous patterns"""

        # Important file deletion
        if request.confirmation_type == ConfirmationType.FILE_DELETE:
            file_path = request.details.get("file", "")
            if self._is_important_file(file_path):
                return RuleResult(
                    is_definitive=True, action="deny", reason="Cannot delete important files"
                )

        # Dangerous commands
        if request.confirmation_type == ConfirmationType.COMMAND_EXECUTE:
            command = request.details.get("command", "")
            if self._is_dangerous_command(command):
                return RuleResult(
                    is_definitive=True, action="deny", reason="Dangerous system command"
                )

        return None

    def _is_in_workspace(self, file_path: str) -> bool:
        """Check if file is in workspace"""
        try:
            path = Path(file_path).resolve()
            # Check if workspace_root is in path's parents OR if they're the same
            return (
                self.workspace_root in path.parents
                or path.parent == self.workspace_root
                or path == self.workspace_root
            )
        except:
            return False

    def _is_in_requirements(self, package: str) -> bool:
        """Check if package is in requirements.txt"""
        requirements_file = self.workspace_root / "requirements.txt"
        if not requirements_file.exists():
            return False

        try:
            with open(requirements_file, "r", encoding="utf - 8") as f:
                packages = [
                    line.split("==")[0].split(">=")[0].split("<=")[0].strip()
                    for line in f
                    if line.strip() and not line.strip().startswith("#")
                ]
                return package.lower() in [p.lower() for p in packages]
        except:
            return False

    def _is_important_file(self, file_path: str) -> bool:
        """Check if file is important"""
        important_patterns = [
            ".git/",
            "config.py",
            "settings.py",
            ".env",
            "requirements.txt",
            "setup.py",
            "pyproject.toml",
        ]
        file_path_lower = file_path.lower()
        return any(pattern in file_path_lower for pattern in important_patterns)

    def _is_dangerous_command(self, command: str) -> bool:
        """Check if command is dangerous"""
        dangerous_commands = ["rm -r", "del /f /s /q", "format", "dd if=", "mkfs", "> /dev / sda"]
        command_lower = command.lower()
        return any(dangerous in command_lower for dangerous in dangerous_commands)


class HybridDecisionEngine:
    """
    Hybrid Decision Engine

    Combines rule - based safety engine with AI judgment for optimal performance.

    Decision Flow:
    1. Rules Engine (fast, ~1ms) - handles clear cases
    2. AI Judgment (smart, ~7s) - handles complex cases
    3. Template Fallback (safe, ~1ms) - handles errors

    Error Handling:
    - API error → Template response (continue if safe)
    - Timeout → Template response (continue if safe)
    - Complete failure → Stop worker
    """

    def __init__(
        self, workspace_root: Path, wsl_distribution: str = "Ubuntu - 24.04", verbose: bool = False
    ):
        """
        Initialize hybrid engine

        Args:
            workspace_root: Root directory of workspace
            wsl_distribution: WSL distribution name for Claude CLI
            verbose: Enable verbose logging
        """
        self.workspace_root = Path(workspace_root)
        self.verbose = verbose

        # Components
        self.rules = SafetyRulesEngine(self.workspace_root)
        self.orchestrator_ai = CLIOrchestratorAI(
            workspace=str(self.workspace_root), wsl_distribution=wsl_distribution, verbose=verbose
        )
        self.templates = ErrorTemplates()

        # Stats
        self.stats = {
            "rules_decisions": 0,
            "ai_decisions": 0,
            "template_fallbacks": 0,
            "total_latency_ms": 0.0,
        }

    async def decide(
        self, worker_id: str, request: ConfirmationRequest, context: Optional[Dict[str, Any]] = None
    ) -> Decision:
        """
        Make a decision on worker request

        Args:
            worker_id: Worker identifier
            request: Confirmation request
            context: Additional context (task_name, project_name, etc.)

        Returns:
            Decision object with action and reasoning

        Raises:
            Exception: If complete failure occurs (worker should stop)
        """

        start_time = time.time()

        if self.verbose:
            print(f"\n[Hybrid Engine] Processing request from {worker_id}")
            print(f"  Type: {request.confirmation_type.value}")
            print(f"  Message: {request.message[:100]}...")

        # Step 1: Try rule - based evaluation (fast)
        rule_result = self.rules.evaluate(request)

        if rule_result.is_definitive:
            # Rules gave clear answer - use it
            latency = (time.time() - start_time) * 1000

            if self.verbose:
                print(f"  ✓ Rules decided: {rule_result.action.upper()}")
                print(f"  Reasoning: {rule_result.reason}")
                print(f"  Latency: {latency:.1f}ms")

            self.stats["rules_decisions"] += 1
            self.stats["total_latency_ms"] += latency

            return Decision(
                action=rule_result.action,
                reasoning=rule_result.reason,
                latency_ms=latency,
                is_fallback=False,
                decided_by="rules",
            )

        # Step 2: Rules inconclusive - ask AI
        if self.verbose:
            print("  → Rules inconclusive, consulting AI...")

        try:
            # Build question for AI
            question = self._build_ai_question(request)

            # Build context
            if context is None:
                context = {}
            context.setdefault("worker_id", worker_id)
            context.setdefault("task_name", "unknown")
            context.setdefault("project_name", "AI_Investor")
            context.setdefault("project_goal", "Build AI - powered investment platform MVP")

            # Ask orchestrator AI
            ai_result = await self.orchestrator_ai.ask(question=question, context=context)

            latency = (time.time() - start_time) * 1000

            if self.verbose:
                print(f"  ✓ AI decided: {ai_result.action.upper()}")
                print(f"  Reasoning: {ai_result.reasoning}")
                print(f"  Latency: {latency:.1f}ms")

            self.stats["ai_decisions"] += 1
            self.stats["total_latency_ms"] += latency

            return Decision(
                action=ai_result.action,
                reasoning=f"AI: {ai_result.reasoning}",
                latency_ms=latency,
                is_fallback=ai_result.is_fallback,
                decided_by="template" if ai_result.is_fallback else "ai",
            )

        except Exception as e:
            # AI failed - use template fallback
            latency = (time.time() - start_time) * 1000

            if self.verbose:
                print(f"  ⚠ AI error: {str(e)[:100]}")
                print("  → Using template fallback")

            # Check if this is a complete failure
            if "completely unresponsive" in str(e).lower():
                # Complete failure - should stop worker
                raise Exception(
                    f"Orchestrator completely unresponsive. Worker {worker_id} should stop."
                )

            # Use template
            template = self.templates.get_api_error_template(request)

            if self.verbose:
                print(f"  ✓ Template: {template.action.upper()}")
                print(f"  Message: {template.message}")
                print(f"  Latency: {latency:.1f}ms")

            self.stats["template_fallbacks"] += 1
            self.stats["total_latency_ms"] += latency

            return Decision(
                action=template.action,
                reasoning=f"Template (error): {template.message}",
                latency_ms=latency,
                is_fallback=True,
                decided_by="template",
            )

    def _build_ai_question(self, request: ConfirmationRequest) -> str:
        """Build question for AI"""

        # Format details nicely
        details_str = "\n".join([f"  - {k}: {v}" for k, v in request.details.items()])

        question = """Request Type: {request.confirmation_type.value}

Message: {request.message}

Details:
{details_str}

Should I approve or deny this request?"""

        return question

    def get_stats(self) -> Dict[str, Any]:
        """Get decision statistics"""
        total_decisions = (
            self.stats["rules_decisions"]
            + self.stats["ai_decisions"]
            + self.stats["template_fallbacks"]
        )

        avg_latency = (
            self.stats["total_latency_ms"] / total_decisions if total_decisions > 0 else 0.0
        )

        return {
            "total_decisions": total_decisions,
            "rules_decisions": self.stats["rules_decisions"],
            "ai_decisions": self.stats["ai_decisions"],
            "template_fallbacks": self.stats["template_fallbacks"],
            "average_latency_ms": avg_latency,
            "rules_percentage": (
                self.stats["rules_decisions"] / total_decisions * 100
                if total_decisions > 0
                else 0.0
            ),
        }


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test():
        """Test hybrid engine"""

        # Create engine
        engine = HybridDecisionEngine(
            workspace_root=Path(r"D:\user\ai_coding\AI_Investor\tools\parallel - coding\workspace"),
            verbose=True,
        )

        print("=" * 70)
        print("HYBRID ENGINE TEST")
        print("=" * 70)

        # Test 1: Safe file creation (should be handled by rules)
        print("\n\nTEST 1: Safe file creation (rules should handle)")
        print("-" * 70)
        request1 = ConfirmationRequest(
            confirmation_type=ConfirmationType.FILE_WRITE,
            message="I want to create a file 'models / user.py' with database model code.",
            details={"file": "workspace / models / user.py"},
        )
        decision1 = await engine.decide("worker_001", request1)
        print(f"\nResult: {decision1.action.upper()}")
        print(f"Decided by: {decision1.decided_by}")
        print(f"Reasoning: {decision1.reasoning}")
        print(f"Latency: {decision1.latency_ms:.1f}ms")

        # Test 2: Complex decision (should go to AI)
        print("\n\nTEST 2: Complex decision (AI should handle)")
        print("-" * 70)
        request2 = ConfirmationRequest(
            confirmation_type=ConfirmationType.GENERAL,
            message="I want to refactor the database connection pooling to use asyncio. This will require modifying several files. Is this a good idea?",
            details={"scope": "multiple files", "complexity": "high"},
        )
        decision2 = await engine.decide("worker_002", request2)
        print(f"\nResult: {decision2.action.upper()}")
        print(f"Decided by: {decision2.decided_by}")
        print(f"Reasoning: {decision2.reasoning}")
        print(f"Latency: {decision2.latency_ms:.1f}ms")

        # Test 3: Dangerous deletion (rules should deny)
        print("\n\nTEST 3: Dangerous deletion (rules should deny)")
        print("-" * 70)
        request3 = ConfirmationRequest(
            confirmation_type=ConfirmationType.FILE_DELETE,
            message="I want to delete config.py",
            details={"file": "config.py"},
        )
        decision3 = await engine.decide("worker_003", request3)
        print(f"\nResult: {decision3.action.upper()}")
        print(f"Decided by: {decision3.decided_by}")
        print(f"Reasoning: {decision3.reasoning}")
        print(f"Latency: {decision3.latency_ms:.1f}ms")

        # Show stats
        print("\n\n" + "=" * 70)
        print("STATISTICS")
        print("=" * 70)
        stats = engine.get_stats()
        print(f"Total decisions: {stats['total_decisions']}")
        print(f"  Rules: {stats['rules_decisions']} ({stats['rules_percentage']:.1f}%)")
        print(f"  AI: {stats['ai_decisions']}")
        print(f"  Template fallbacks: {stats['template_fallbacks']}")
        print(f"Average latency: {stats['average_latency_ms']:.1f}ms")
        print("=" * 70)

    asyncio.run(test())
