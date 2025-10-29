"""Adaptive Standard Embedding for Codex prompts.

This module provides intelligent embedding of Excellence AI Standard
and Token Efficiency Standard into Codex prompts based on task type
and violation history.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List


class EmbeddingLevel(str, Enum):
    """Standard embedding level for Codex prompts."""

    REFERENCE = "reference"  # ~10 tokens: "Excellence AI Standard: enforced"
    SUMMARY = "summary"  # ~200 tokens: Critical rules only
    FULL = "full"  # ~800 tokens: Complete standard


@dataclass
class ViolationHistory:
    """Track Excellence AI Standard violations by type."""

    todo_comments: int = 0
    any_types: int = 0
    insecure_hashing: int = 0  # bcrypt, MD5, SHA1
    sql_injection_risk: int = 0
    long_functions: int = 0  # >50 lines
    missing_docstrings: int = 0
    missing_type_hints: int = 0
    low_test_coverage: int = 0  # <90%

    def total_violations(self) -> int:
        """Calculate total violation count."""
        return (
            self.todo_comments
            + self.any_types
            + self.insecure_hashing
            + self.sql_injection_risk
            + self.long_functions
            + self.missing_docstrings
            + self.missing_type_hints
            + self.low_test_coverage
        )

    def has_frequent_violations(self, threshold: int = 3) -> bool:
        """Check if violations exceed threshold."""
        return self.total_violations() >= threshold


class AdaptiveStandardEmbedding:
    """Adaptively embed standards in Codex prompts based on context.

    Optimizes token usage by selecting appropriate embedding level:
    - REFERENCE: Security - free utility functions (10 tokens)
    - SUMMARY: Standard business logic (200 tokens)
    - FULL: Security - critical or violation - prone (800 tokens)

    Example:
        >>> adapter = AdaptiveStandardEmbedding()
        >>> prompt = adapter.generate_prompt_with_standard(
        ...     task_spec="Create email_validator.py",
        ...     task_type="utility"
        ... )
        >>> # Uses REFERENCE level (10 tokens)
    """

    def __init__(
        self,
        standard_dir: Path | None = None,
        violation_history: ViolationHistory | None = None,
    ):
        """Initialize adapter with standards directory.

        Args:
            standard_dir: Path to excellence_ai_standard directory
            violation_history: Previous violation history
        """
        self.standard_dir = standard_dir or Path("excellence_ai_standard")
        self.violation_history = violation_history or ViolationHistory()

        # Security - critical task types requiring FULL embedding
        self.security_critical_types = {
            "auth",
            "authentication",
            "authorization",
            "crypto",
            "encryption",
            "password",
            "security",
            "jwt",
            "oauth",
        }

    def determine_embedding_level(self, task_type: str) -> EmbeddingLevel:
        """Determine appropriate embedding level for task.

        Strategy:
        1. Security - critical → FULL (800 tokens)
        2. Frequent violations → SUMMARY (200 tokens)
        3. Clean history → REFERENCE (10 tokens)

        Args:
            task_type: Type of task (e.g., 'auth', 'utility')

        Returns:
            Appropriate embedding level
        """
        # Security - critical always gets full standard
        if any(critical in task_type.lower() for critical in self.security_critical_types):
            return EmbeddingLevel.FULL

        # Violation - prone gets summary
        if self.violation_history.has_frequent_violations():
            return EmbeddingLevel.SUMMARY

        # Clean history gets reference only
        return EmbeddingLevel.REFERENCE

    def load_summary(self) -> str:
        """Load Excellence AI Standard summary (800 tokens)."""
        summary_path = self.standard_dir / "summaries" / "excellence_ai_standard_summary.md"

        if not summary_path.exists():
            raise FileNotFoundError(f"Standard summary not found: {summary_path}")

        return summary_path.read_text(encoding="utf - 8")

    def extract_critical_rules(self, full_summary: str) -> str:
        """Extract critical rules from full summary (800 → 200 tokens).

        Extracts:
        - Absolute prohibitions
        - Security standards
        - Type safety requirements
        - Function complexity limits

        Args:
            full_summary: Full standard summary (800 tokens)

        Returns:
            Critical rules only (200 tokens)
        """
        critical_sections = [
            "## Absolute Prohibitions",
            "## Security Standards",
            "## Type Safety",
            "## Function Complexity",
        ]

        extracted_lines: List[str] = []

        for line in full_summary.splitlines():
            # Include section headers and bullet points
            if any(section in line for section in critical_sections):
                extracted_lines.append(line)
            elif line.strip().startswith(("-", "✅", "❌")):
                extracted_lines.append(line)

        return "\n".join(extracted_lines)

    def generate_standard_section(self, level: EmbeddingLevel) -> str:
        """Generate standard section for prompt based on level.

        Args:
            level: Embedding level to use

        Returns:
            Formatted standard section for Codex prompt
        """
        if level == EmbeddingLevel.REFERENCE:
            return (
                "## Excellence AI Standard\n"
                "Standard: enforced\n"
                "Full reference: excellence_ai_standard / summaries/"
                "excellence_ai_standard_summary.md"
            )

        elif level == EmbeddingLevel.SUMMARY:
            full_summary = self.load_summary()
            critical_rules = self.extract_critical_rules(full_summary)

            return (
                "## Excellence AI Standard (CRITICAL RULES)\n"
                f"{critical_rules}\n\n"
                "Full standard: excellence_ai_standard / summaries/"
                "excellence_ai_standard_summary.md"
            )

        else:  # FULL
            full_summary = self.load_summary()

            return (
                "## Excellence AI Standard (FULL COMPLIANCE REQUIRED)\n"
                f"{full_summary}\n\n"
                "CRITICAL: 100% compliance mandatory for this file."
            )

    def generate_prompt_with_standard(
        self,
        task_spec: str,
        task_type: str,
    ) -> str:
        """Generate Codex prompt with adaptively embedded standard.

        Args:
            task_spec: Task specification (file, class, methods)
            task_type: Type of task for level determination

        Returns:
            Complete Codex prompt with embedded standard

        Example:
            >>> adapter = AdaptiveStandardEmbedding()
            >>> prompt = adapter.generate_prompt_with_standard(
            ...     task_spec="Create email_validator.py\\n...",
            ...     task_type="utility"
            ... )
            >>> print(len(prompt))  # ~510 tokens (task + reference)
        """
        level = self.determine_embedding_level(task_type)
        standard_section = self.generate_standard_section(level)

        return f"{task_spec}\n\n{standard_section}"

    def record_violations(self, violations: List[str]) -> None:
        """Record violations for adaptive learning.

        Args:
            violations: List of violation types detected
        """
        for violation in violations:
            violation_lower = violation.lower()

            if "todo" in violation_lower or "fixme" in violation_lower:
                self.violation_history.todo_comments += 1
            elif "any" in violation_lower:
                self.violation_history.any_types += 1
            elif "bcrypt" in violation_lower or "md5" in violation_lower:
                self.violation_history.insecure_hashing += 1
            elif "sql" in violation_lower:
                self.violation_history.sql_injection_risk += 1
            elif "50 lines" in violation_lower:
                self.violation_history.long_functions += 1
            elif "docstring" in violation_lower:
                self.violation_history.missing_docstrings += 1
            elif "type hint" in violation_lower:
                self.violation_history.missing_type_hints += 1
            elif "coverage" in violation_lower:
                self.violation_history.low_test_coverage += 1

    def get_token_estimate(self, level: EmbeddingLevel) -> int:
        """Estimate token count for embedding level.

        Args:
            level: Embedding level

        Returns:
            Estimated token count
        """
        token_estimates = {
            EmbeddingLevel.REFERENCE: 10,
            EmbeddingLevel.SUMMARY: 200,
            EmbeddingLevel.FULL: 800,
        }

        return token_estimates[level]


__all__ = [
    "AdaptiveStandardEmbedding",
    "EmbeddingLevel",
    "ViolationHistory",
]
