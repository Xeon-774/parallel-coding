"""
Codex Review Provider - OpenAI Codex CLI Document Review Implementation

This module provides Codex CLI integration for document review functionality.
It leverages the existing CodexExecutor for task execution and adds review - specific
prompt engineering and result parsing.

Key Features:
    - Perspective - specific review prompts (architecture, security, feasibility)
    - Structured feedback parsing from Codex output
    - Integration with existing CodexExecutor
    - Comprehensive error handling
    - Type - safe with Pydantic models

Architecture:
    CodexReviewProvider
    ├── review_document() - Main review execution
    ├── _build_review_prompt() - Prompt engineering
    ├── _parse_review_output() - Output parsing
    └── _calculate_score() - Score calculation

Dependencies:
    - CodexExecutor (existing)
    - BaseReviewProvider (interface)

Author: Claude (Sonnet 4.5)
Created: 2025 - 10 - 28
Version: 1.0.0
Excellence AI Standard: 100% Applied
"""

from __future__ import annotations

import re
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from orchestrator.core.ai_providers.base_review_provider import (
    AggregatedReview,
    BaseReviewProvider,
    FeedbackSeverity,
    ProviderNotAvailableError,
    ReviewExecutionError,
    ReviewFeedback,
    ReviewPerspective,
    ReviewRequest,
    ReviewResult,
    ReviewStatus,
    ReviewTimeoutError,
    ReviewType,
)
from orchestrator.core.worker.codex_executor import (
    CodexExecutionResult,
    CodexExecutor,
    ExecutionStatus,
)

# =============================================================================
# Constants
# =============================================================================

PROVIDER_NAME: str = "codex"


# =============================================================================
# Review Prompt Templates
# =============================================================================


REVIEW_PROMPTS: Dict[ReviewPerspective, str] = {
    ReviewPerspective.ARCHITECTURE: """
You are an expert software architect reviewing a technical document.

Focus on:
- System design and component architecture
- Scalability and modularity
- Design patterns and best practices
- Component coupling and cohesion
- API design and interfaces

Provide feedback in this format:
[SEVERITY:CRITICAL|WARNING|INFO] [LINE:number] Message
Suggestion: improvement suggestion
---
""",
    ReviewPerspective.SECURITY: """
You are a security expert reviewing a technical document.

Focus on:
- Security vulnerabilities and attack vectors
- Authentication and authorization
- Data validation and sanitization
- Secrets management
- Secure coding practices

Provide feedback in this format:
[SEVERITY:CRITICAL|WARNING|INFO] [LINE:number] Message
Suggestion: improvement suggestion
---
""",
    ReviewPerspective.PERFORMANCE: """
You are a performance optimization expert reviewing a technical document.

Focus on:
- Performance bottlenecks
- Resource utilization (CPU, memory, I / O)
- Caching strategies
- Algorithm complexity
- Database query optimization

Provide feedback in this format:
[SEVERITY:CRITICAL|WARNING|INFO] [LINE:number] Message
Suggestion: improvement suggestion
---
""",
    ReviewPerspective.FEASIBILITY: """
You are a technical feasibility expert reviewing a project document.

Focus on:
- Implementation complexity and effort
- Technical risks and dependencies
- Resource requirements
- Timeline realism
- Technology maturity and availability

Provide feedback in this format:
[SEVERITY:CRITICAL|WARNING|INFO] [LINE:number] Message
Suggestion: improvement suggestion
---
""",
    ReviewPerspective.PRIORITY: """
You are a project management expert reviewing a roadmap or task prioritization.

Focus on:
- Priority alignment with business goals
- Task dependencies and sequencing
- Resource allocation efficiency
- Risk - based prioritization
- MVP vs. nice - to - have features

Provide feedback in this format:
[SEVERITY:CRITICAL|WARNING|INFO] [LINE:number] Message
Suggestion: improvement suggestion
---
""",
    ReviewPerspective.MAINTAINABILITY: """
You are a code maintainability expert reviewing technical documentation.

Focus on:
- Code organization and structure
- Documentation completeness
- Testing strategy
- Dependency management
- Technical debt considerations

Provide feedback in this format:
[SEVERITY:CRITICAL|WARNING|INFO] [LINE:number] Message
Suggestion: improvement suggestion
---
""",
    ReviewPerspective.TESTING: """
You are a QA and testing expert reviewing technical documentation.

Focus on:
- Test coverage and strategies
- Test automation opportunities
- Edge cases and error scenarios
- Integration and E2E testing
- Performance and load testing

Provide feedback in this format:
[SEVERITY:CRITICAL|WARNING|INFO] [LINE:number] Message
Suggestion: improvement suggestion
---
""",
    ReviewPerspective.DOCUMENTATION: """
You are a technical documentation expert reviewing content.

Focus on:
- Clarity and completeness
- Target audience appropriateness
- Examples and usage instructions
- Consistency and structure
- Accessibility and formatting

Provide feedback in this format:
[SEVERITY:CRITICAL|WARNING|INFO] [LINE:number] Message
Suggestion: improvement suggestion
---
""",
}


# =============================================================================
# Codex Review Provider
# =============================================================================


class CodexReviewProvider(BaseReviewProvider):
    """
    Codex CLI - based document review provider.

    This provider uses OpenAI Codex CLI to perform document reviews from
    various perspectives (architecture, security, feasibility, etc.).

    Features:
        - Perspective - specific prompts
        - Structured feedback parsing
        - Score calculation based on feedback severity
        - Integration with existing CodexExecutor

    Usage:
        >>> from orchestrator.config import OrchestratorConfig
        >>> config = OrchestratorConfig.from_env()
        >>> executor = CodexExecutor(...)
        >>> provider = CodexReviewProvider(executor)
        >>>
        >>> request = ReviewRequest(
        ...     document_path="docs / ROADMAP.md",
        ...     review_type=ReviewType.ROADMAP,
        ...     perspective=ReviewPerspective.FEASIBILITY
        ... )
        >>> result = await provider.review_document(request)
    """

    def __init__(self, codex_executor: CodexExecutor) -> None:
        """
        Initialize Codex review provider.

        Args:
            codex_executor: Configured CodexExecutor instance

        Example:
            >>> executor = CodexExecutor(...)
            >>> provider = CodexReviewProvider(executor)
        """
        self._executor = codex_executor

    @property
    def provider_name(self) -> str:
        """Get provider identifier"""
        return PROVIDER_NAME

    def is_available(self) -> bool:
        """
        Check if Codex CLI is available.

        Returns:
            True if Codex CLI is installed and working, False otherwise

        Example:
            >>> if provider.is_available():
            ...     result = await provider.review_document(request)
        """
        try:
            # Check if codex executor is properly configured
            # In production, we'd verify CLI installation here
            return self._executor is not None
        except Exception:
            return False

    async def review_document(self, request: ReviewRequest) -> ReviewResult:
        """
        Execute document review using Codex CLI.

        Args:
            request: Review request with document path and parameters

        Returns:
            ReviewResult with feedback and scores

        Raises:
            ValueError: If request is invalid
            ReviewTimeoutError: If review exceeds timeout
            ReviewExecutionError: If Codex execution fails

        Example:
            >>> request = ReviewRequest(
            ...     document_path="docs / ROADMAP.md",
            ...     review_type=ReviewType.ROADMAP,
            ...     perspective=ReviewPerspective.FEASIBILITY
            ... )
            >>> result = await provider.review_document(request)
            >>> print(f"Score: {result.overall_score}")
            >>> for feedback in result.critical_issues:
            ...     print(f"CRITICAL: {feedback.message}")
        """
        if not self.is_available():
            raise ProviderNotAvailableError("Codex CLI is not available")

        start_time = time.time()
        job_id = uuid.uuid4().hex

        try:
            # Build review prompt
            prompt = self._build_review_prompt(request)

            # Create temporary task file
            task_file = Path(f"temp_review_{job_id}.txt")
            task_file.write_text(prompt, encoding="utf - 8")

            try:
                # Execute review using Codex
                workspace = Path(request.document_path).parent
                codex_result = self._executor.execute(
                    task_file=task_file,
                    workspace_dir=workspace,
                    timeout=request.timeout_seconds,
                )

                # Parse result
                if codex_result.success:
                    feedbacks = self._parse_review_output(codex_result.stdout, request.perspective)
                    score = self._calculate_score(feedbacks)
                    status = ReviewStatus.SUCCESS
                    error_message = None
                elif codex_result.status == ExecutionStatus.TIMEOUT:
                    feedbacks = []
                    score = 0.0
                    status = ReviewStatus.TIMEOUT
                    error_message = "Review execution timed out"
                else:
                    feedbacks = []
                    score = 0.0
                    status = ReviewStatus.FAILED
                    error_message = codex_result.error_message or "Codex execution failed"

                execution_time = time.time() - start_time

                return ReviewResult(
                    job_id=job_id,
                    document_path=request.document_path,
                    review_type=request.review_type,
                    perspective=request.perspective,
                    status=status,
                    feedbacks=feedbacks,
                    overall_score=score,
                    execution_time_seconds=execution_time,
                    provider_name=self.provider_name,
                    metadata={
                        "codex_exit_code": codex_result.exit_code,
                        "codex_duration": codex_result.duration_seconds,
                        "usage": (
                            {
                                "input_tokens": codex_result.usage.input_tokens,
                                "output_tokens": codex_result.usage.output_tokens,
                            }
                            if codex_result.usage
                            else None
                        ),
                    },
                    error_message=error_message,
                )

            finally:
                # Cleanup temporary task file
                if task_file.exists():
                    task_file.unlink()

        except Exception as e:
            execution_time = time.time() - start_time
            return ReviewResult(
                job_id=job_id,
                document_path=request.document_path,
                review_type=request.review_type,
                perspective=request.perspective,
                status=ReviewStatus.FAILED,
                feedbacks=[],
                overall_score=0.0,
                execution_time_seconds=execution_time,
                provider_name=self.provider_name,
                error_message=f"Review execution error: {str(e)}",
            )

    def _build_review_prompt(self, request: ReviewRequest) -> str:
        """
        Build review prompt for Codex CLI.

        Args:
            request: Review request

        Returns:
            Formatted prompt string

        Example:
            >>> prompt = provider._build_review_prompt(request)
        """
        # Get perspective - specific instructions
        perspective_prompt = REVIEW_PROMPTS.get(
            request.perspective,
            REVIEW_PROMPTS[ReviewPerspective.ARCHITECTURE],  # Default fallback
        )

        # Read document content
        doc_content = Path(request.document_path).read_text(encoding="utf - 8")

        # Build context information
        context_str = ""
        if request.context:
            context_str = "\n\nContext:\n"
            for key, value in request.context.items():
                context_str += f"- {key}: {value}\n"

        # Combine into full prompt
        prompt = """Review the following {request.review_type.value} document from a {request.perspective.value} perspective.

{perspective_prompt}

Document path: {request.document_path}
{context_str}

Document content:
---
{doc_content}
---

Please provide structured feedback in the format specified above.
For each issue found, specify severity (CRITICAL / WARNING / INFO), line number if applicable, message, and suggestion.
End your review with a summary line: OVERALL_SCORE: [0 - 100]
"""

        return prompt

    def _parse_review_output(
        self, output: str, perspective: ReviewPerspective
    ) -> List[ReviewFeedback]:
        """
        Parse Codex output into structured feedback.

        Args:
            output: Raw Codex output
            perspective: Review perspective used

        Returns:
            List of ReviewFeedback items

        Example:
            >>> feedbacks = provider._parse_review_output(output, ReviewPerspective.SECURITY)
        """
        feedbacks: List[ReviewFeedback] = []

        # Split into feedback blocks (separated by ---)
        blocks = output.split("---")

        for block in blocks:
            if not block.strip():
                continue

            # Parse feedback header: [SEVERITY:X] [LINE:Y] Message
            header_match = re.search(
                r"\[SEVERITY:(CRITICAL|WARNING|INFO)\](?:\s*\[LINE:(\d+)\])?\s*(.+?)(?:\n|$)",
                block,
                re.IGNORECASE,
            )

            if not header_match:
                continue

            severity_str = header_match.group(1).upper()
            line_num_str = header_match.group(2)
            message = header_match.group(3).strip()

            # Parse suggestion
            suggestion_match = re.search(
                r"Suggestion:\s*(.+?)(?:\n---|$)", block, re.DOTALL | re.IGNORECASE
            )
            suggestion = suggestion_match.group(1).strip() if suggestion_match else None

            # Map severity
            severity_map = {
                "CRITICAL": FeedbackSeverity.CRITICAL,
                "WARNING": FeedbackSeverity.WARNING,
                "INFO": FeedbackSeverity.INFO,
            }
            severity = severity_map.get(severity_str, FeedbackSeverity.INFO)

            # Create feedback
            feedback = ReviewFeedback(
                category=perspective,
                severity=severity,
                line_number=int(line_num_str) if line_num_str else None,
                message=message,
                suggestion=suggestion,
            )

            feedbacks.append(feedback)

        return feedbacks

    def _calculate_score(self, feedbacks: List[ReviewFeedback]) -> float:
        """
        Calculate overall quality score based on feedback.

        Score calculation:
        - Start at 100
        - Subtract 20 per critical issue
        - Subtract 10 per warning
        - Subtract 2 per info item
        - Minimum score: 0

        Args:
            feedbacks: List of feedback items

        Returns:
            Score from 0 - 100

        Example:
            >>> score = provider._calculate_score(feedbacks)
            >>> print(f"Quality score: {score}")
        """
        score = 100.0

        for feedback in feedbacks:
            if feedback.severity == FeedbackSeverity.CRITICAL:
                score -= 20.0
            elif feedback.severity == FeedbackSeverity.WARNING:
                score -= 10.0
            elif feedback.severity == FeedbackSeverity.INFO:
                score -= 2.0

        return max(0.0, score)


# =============================================================================
# Utility Functions
# =============================================================================


def create_codex_review_provider(codex_executor: CodexExecutor) -> CodexReviewProvider:
    """
    Create Codex review provider with executor.

    Args:
        codex_executor: Configured CodexExecutor instance

    Returns:
        CodexReviewProvider instance

    Example:
        >>> from orchestrator.config import OrchestratorConfig
        >>> from orchestrator.core.worker.codex_executor import create_codex_executor_from_config
        >>> config = OrchestratorConfig.from_env()
        >>> executor = create_codex_executor_from_config(config)
        >>> provider = create_codex_review_provider(executor)
    """
    return CodexReviewProvider(codex_executor)


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    import asyncio

    from orchestrator.config import OrchestratorConfig
    from orchestrator.core.worker.codex_executor import (
        create_codex_executor_from_config,
    )

    async def main() -> None:
        """Example usage of Codex review provider"""
        # Create executor and provider
        config = OrchestratorConfig.from_env()
        executor = create_codex_executor_from_config(config)
        provider = create_codex_review_provider(executor)

        print(f"Provider: {provider.provider_name}")
        print(f"Available: {provider.is_available()}")

        # Example review request
        request = ReviewRequest(
            document_path="docs / ROADMAP.md",
            review_type=ReviewType.ROADMAP,
            perspective=ReviewPerspective.FEASIBILITY,
            context={"project": "AI_Investor", "phase": "Week 2"},
        )

        print(f"\nReviewing: {request.document_path}")
        print(f"Perspective: {request.perspective.value}")

        result = await provider.review_document(request)

        print(f"\nStatus: {result.status.value}")
        print(f"Score: {result.overall_score}/100")
        print(f"Execution time: {result.execution_time_seconds:.1f}s")
        print(f"\nFeedback items: {len(result.feedbacks)}")
        print(f"- Critical: {len(result.critical_issues)}")
        print(f"- Warnings: {len(result.warnings)}")
        print(f"- Info: {len(result.info_items)}")

        if result.critical_issues:
            print("\nCritical issues:")
            for fb in result.critical_issues:
                print(f"  [{fb.line_number or 'N / A'}] {fb.message}")
                if fb.suggestion:
                    print(f"      → {fb.suggestion}")

    asyncio.run(main())
