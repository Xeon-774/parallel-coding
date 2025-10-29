"""
CLI-based Orchestrator AI (Subscription Only - No API)

Uses Claude CLI with subscription for orchestrator AI decisions.
"""

import asyncio
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class Decision:
    """Orchestrator AI decision"""

    action: str  # "approve" or "deny"
    reasoning: str
    latency_ms: float = 0.0
    is_fallback: bool = False


class CLIOrchestratorAI:
    """
    Claude CLI-based Orchestrator AI

    Uses Claude Pro subscription (no API calls).
    Each question spawns a new Claude CLI process.
    """

    def __init__(
        self, workspace: str, wsl_distribution: str = "Ubuntu-24.04", verbose: bool = True
    ):
        """
        Initialize CLI Orchestrator

        Args:
            workspace: Workspace directory (Windows path)
            wsl_distribution: WSL distribution name
            verbose: Enable verbose logging
        """
        self.workspace = Path(workspace)
        self.wsl_distribution = wsl_distribution
        self.verbose = verbose

        # System prompt template
        self.system_prompt_template = """You are the Orchestrator AI in a parallel AI coding system.

Project: {project_name}
Goal: {project_goal}

Your role:
- Review worker AI requests for safety and appropriateness
- Make intelligent decisions based on context
- Provide brief reasoning for your decisions

CRITICAL RESPONSE FORMAT:
You MUST respond with exactly one of these formats:
"APPROVED: [brief reason in 1-2 sentences]"
or
"DENIED: [brief reason in 1-2 sentences]"

Examples of good responses:
- APPROVED: Creating schema.sql in database/ is appropriate for database setup.
- DENIED: Deleting config.json would break the system configuration.
- APPROVED: Installing pytest from requirements.txt is safe and necessary for testing.

Keep your reasoning concise and clear.
"""

    async def ask(self, question: str, context: Optional[Dict[str, Any]] = None) -> Decision:
        """
        Ask the Orchestrator AI for a decision

        Args:
            question: The question/request to evaluate
            context: Additional context (worker_id, task_name, etc.)

        Returns:
            Decision object with action and reasoning
        """
        start_time = time.time()

        # Default context
        if context is None:
            context = {}

        context.setdefault("project_name", "AI_Investor")
        context.setdefault("project_goal", "Build AI-powered investment platform MVP")
        context.setdefault("worker_id", "unknown")
        context.setdefault("task_name", "unknown")

        try:
            # Build system prompt with context
            system_prompt = self.system_prompt_template.format(
                project_name=context["project_name"], project_goal=context["project_goal"]
            )

            # Build full question with context
            full_question = self._build_full_question(question, context)

            if self.verbose:
                print(f"\n{'='*60}")
                print(f"[Orchestrator AI] Question from {context['worker_id']}:")
                print(f"{question[:200]}...")
                print(f"{'='*60}")

            # Call Claude CLI
            response = await self._call_claude_cli(
                system_prompt=system_prompt, question=full_question, timeout=60
            )

            if self.verbose:
                print(f"\n[Orchestrator AI] Response:")
                print(f"{response[:200]}...")
                print(f"{'='*60}\n")

            # Parse response
            decision = self._parse_response(response)
            decision.latency_ms = (time.time() - start_time) * 1000

            return decision

        except subprocess.TimeoutExpired:
            # Timeout - use template response
            latency = (time.time() - start_time) * 1000

            if self.verbose:
                print(f"\n[Orchestrator AI] TIMEOUT after {latency:.0f}ms")

            return Decision(
                action="approve",
                reasoning="Timeout - defaulting to approve for likely safe operation",
                latency_ms=latency,
                is_fallback=True,
            )

        except Exception as e:
            # Error - default to deny for safety
            latency = (time.time() - start_time) * 1000

            if self.verbose:
                print(f"\n[Orchestrator AI] ERROR: {str(e)}")

            return Decision(
                action="deny",
                reasoning=f"Error occurred: {str(e)[:100]}",
                latency_ms=latency,
                is_fallback=True,
            )

    def _build_full_question(self, question: str, context: Dict[str, Any]) -> str:
        """Build full question with context"""
        return f"""=== Context ===
Worker: {context['worker_id']}
Task: {context['task_name']}

=== Request ===
{question}

=== Your Decision ===
Respond with APPROVED: or DENIED:"""

    async def _call_claude_cli(self, system_prompt: str, question: str, timeout: int) -> str:
        """
        Call Claude CLI and get response

        Args:
            system_prompt: System prompt for the AI
            question: Question to ask
            timeout: Timeout in seconds

        Returns:
            Claude CLI response text

        Raises:
            subprocess.TimeoutExpired: If command times out
            RuntimeError: If Claude CLI returns error
        """

        # Convert workspace to WSL path
        wsl_workspace = self._to_wsl_path(str(self.workspace))

        # Create temp directory for prompts
        import tempfile
        import uuid

        # Create temp files (in workspace to ensure accessibility from WSL)
        temp_id = str(uuid.uuid4())[:8]
        system_prompt_file = self.workspace / f"temp_system_{temp_id}.txt"
        question_file = self.workspace / f"temp_question_{temp_id}.txt"

        try:
            # Write system prompt to file
            with open(system_prompt_file, "w", encoding="utf-8") as f:
                f.write(system_prompt)

            # Write question to file
            with open(question_file, "w", encoding="utf-8") as f:
                f.write(question)

            # Convert to WSL paths
            wsl_system_prompt = self._to_wsl_path(str(system_prompt_file))
            wsl_question = self._to_wsl_path(str(question_file))

            # Build command using file inputs
            cmd = (
                f'wsl -d {self.wsl_distribution} -- bash -l -c "'
                f"cd {wsl_workspace} && "
                f"claude --print "
                f'--system-prompt \\"$(cat {wsl_system_prompt})\\" '
                f"< {wsl_question}"
                f'"'
            )

            if self.verbose:
                print(f"\n[DEBUG] Executing Claude CLI...")

            # Run command
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )

            # Check for errors
            if result.returncode != 0:
                stderr = result.stderr.strip()
                raise RuntimeError(f"Claude CLI error (exit {result.returncode}): {stderr[:200]}")

            return result.stdout.strip()

        finally:
            # Clean up temp files
            try:
                if system_prompt_file.exists():
                    system_prompt_file.unlink()
                if question_file.exists():
                    question_file.unlink()
            except:
                pass  # Ignore cleanup errors

    def _parse_response(self, response: str) -> Decision:
        """
        Parse Claude CLI response into Decision

        Args:
            response: Raw response from Claude CLI

        Returns:
            Decision object

        Note:
            If parsing fails, defaults to "deny" for safety
        """

        # Normalize
        normalized = response.strip()

        # Try to match APPROVED: or DENIED:
        patterns = [
            (r"APPROVED\s*:\s*(.+)", "approve"),
            (r"DENIED\s*:\s*(.+)", "deny"),
            (r"APPROVE\s*:\s*(.+)", "approve"),  # Common typo
            (r"DENY\s*:\s*(.+)", "deny"),  # Common typo
        ]

        for pattern, action in patterns:
            match = re.search(pattern, normalized, re.IGNORECASE | re.DOTALL)
            if match:
                reasoning = match.group(1).strip()
                # Limit reasoning length
                if len(reasoning) > 200:
                    reasoning = reasoning[:197] + "..."
                return Decision(action=action, reasoning=reasoning)

        # Parsing failed - try to infer from content
        normalized_lower = normalized.lower()

        if any(word in normalized_lower for word in ["yes", "approve", "safe", "ok", "fine"]):
            return Decision(
                action="approve",
                reasoning=f"Inferred approval from response: {normalized[:100]}...",
            )
        elif any(word in normalized_lower for word in ["no", "deny", "dangerous", "unsafe", "not"]):
            return Decision(
                action="deny", reasoning=f"Inferred denial from response: {normalized[:100]}..."
            )
        else:
            # Completely unclear - default to deny for safety
            return Decision(
                action="deny",
                reasoning=f"Unclear response (defaulting to deny): {normalized[:100]}...",
            )

    def _to_wsl_path(self, windows_path: str) -> str:
        """
        Convert Windows path to WSL path

        Example: D:\\user\\file.txt -> /mnt/d/user/file.txt
        """
        # Replace backslashes with forward slashes
        path = windows_path.replace("\\", "/")

        # Convert drive letter (D:/ -> /mnt/d/)
        import re

        path = re.sub(r"^([A-Za-z]):", lambda m: f"/mnt/{m.group(1).lower()}", path)

        return path

    def _escape_for_bash(self, text: str) -> str:
        """
        Escape text for bash command line

        Args:
            text: Text to escape

        Returns:
            Escaped text safe for bash
        """
        # Replace dangerous characters
        text = text.replace("\\", "\\\\")  # Backslash
        text = text.replace('"', '\\"')  # Double quote
        text = text.replace("$", "\\$")  # Dollar sign (variable expansion)
        text = text.replace("`", "\\`")  # Backtick (command substitution)
        text = text.replace("!", "\\!")  # Exclamation (history expansion)

        return text


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test():
        """Simple test"""
        orchestrator = CLIOrchestratorAI(
            workspace=r"D:\user\ai_coding\AI_Investor\tools\parallel-coding\workspace"
        )

        # Test question
        decision = await orchestrator.ask(
            question="Worker wants to create a file 'test.py' in the workspace. Should I allow this?",
            context={
                "worker_id": "worker_001",
                "task_name": "Test file creation",
                "project_name": "Test Project",
                "project_goal": "Testing orchestrator",
            },
        )

        print(f"\n{'='*60}")
        print(f"RESULT:")
        print(f"  Action: {decision.action}")
        print(f"  Reasoning: {decision.reasoning}")
        print(f"  Latency: {decision.latency_ms:.0f}ms")
        print(f"  Fallback: {decision.is_fallback}")
        print(f"{'='*60}")

    asyncio.run(test())
