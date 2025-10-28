"""Unit tests for AI Safety Judge module.

Tests simple safety assessment logic for confirmation prompts.
"""

import pytest

from orchestrator.core.ai_safety_judge import Decision, Judgment, AISafetyJudge


# ======================= Enum Tests =======================


class TestDecisionEnum:
    """Test Decision enum values."""

    def test_decision_enum_values(self):
        """Test Decision enum has expected values."""
        assert Decision.APPROVE.value == "approve"
        assert Decision.DENY.value == "deny"
        assert Decision.ESCALATE.value == "escalate"

    def test_decision_enum_members(self):
        """Test Decision enum has exactly 3 members."""
        assert len(Decision) == 3
        assert set(Decision) == {Decision.APPROVE, Decision.DENY, Decision.ESCALATE}


# ======================= Judgment Tests =======================


class TestJudgment:
    """Test Judgment dataclass."""

    def test_judgment_creation(self):
        """Test creating Judgment with decision and reason."""
        judgment = Judgment(decision=Decision.APPROVE, reason="Safe operation")
        assert judgment.decision == Decision.APPROVE
        assert judgment.reason == "Safe operation"

    def test_judgment_frozen(self):
        """Test that Judgment is immutable (frozen)."""
        judgment = Judgment(decision=Decision.DENY, reason="Unsafe")
        with pytest.raises(AttributeError):
            judgment.decision = Decision.APPROVE

    def test_judgment_equality(self):
        """Test Judgment equality comparison."""
        j1 = Judgment(decision=Decision.APPROVE, reason="Test")
        j2 = Judgment(decision=Decision.APPROVE, reason="Test")
        j3 = Judgment(decision=Decision.DENY, reason="Test")

        assert j1 == j2
        assert j1 != j3


# ======================= AISafetyJudge Tests =======================


class TestAISafetyJudgeEscalation:
    """Test AISafetyJudge ESCALATE decisions."""

    def test_assess_yes_no_prompt_escalates(self):
        """Test that yes/no prompts are escalated."""
        judge = AISafetyJudge()
        judgment = judge.assess("Do you want to continue? yes/no")

        assert judgment.decision == Decision.ESCALATE
        assert "Requires explicit user confirmation" in judgment.reason

    def test_assess_confirm_prompt_escalates(self):
        """Test that confirm prompts are escalated."""
        judge = AISafetyJudge()
        judgment = judge.assess("Please confirm this action")

        assert judgment.decision == Decision.ESCALATE
        assert "Requires explicit user confirmation" in judgment.reason

    def test_assess_proceed_prompt_escalates(self):
        """Test that proceed? prompts are escalated."""
        judge = AISafetyJudge()
        judgment = judge.assess("Proceed?")

        assert judgment.decision == Decision.ESCALATE
        assert "Requires explicit user confirmation" in judgment.reason

    def test_assess_case_insensitive_yes_no(self):
        """Test case insensitivity for yes/no detection."""
        judge = AISafetyJudge()
        judgment = judge.assess("Continue? YES/NO")

        assert judgment.decision == Decision.ESCALATE

    def test_assess_whitespace_handling_for_escalation(self):
        """Test that whitespace is normalized for escalation detection."""
        judge = AISafetyJudge()
        judgment = judge.assess("   confirm this action   ")

        assert judgment.decision == Decision.ESCALATE


class TestAISafetyJudgeApproval:
    """Test AISafetyJudge APPROVE decisions."""

    def test_assess_print_view_approved(self):
        """Test that print and view operations are approved."""
        judge = AISafetyJudge()
        judgment = judge.assess("print this file and view the results")

        assert judgment.decision == Decision.APPROVE
        assert "Read-only action deemed safe" in judgment.reason

    def test_assess_view_print_order_approved(self):
        """Test that view and print in different order is approved."""
        judge = AISafetyJudge()
        judgment = judge.assess("view the output and print it")

        assert judgment.decision == Decision.APPROVE
        assert "Read-only action deemed safe" in judgment.reason

    def test_assess_case_insensitive_print_view(self):
        """Test case insensitivity for print/view detection."""
        judge = AISafetyJudge()
        judgment = judge.assess("PRINT and VIEW this")

        assert judgment.decision == Decision.APPROVE


class TestAISafetyJudgeDenial:
    """Test AISafetyJudge DENY decisions."""

    def test_assess_unrecognized_prompt_denied(self):
        """Test that unrecognized prompts are denied."""
        judge = AISafetyJudge()
        judgment = judge.assess("delete all files")

        assert judgment.decision == Decision.DENY
        assert "Unrecognized or potentially unsafe request" in judgment.reason

    def test_assess_empty_prompt_denied(self):
        """Test that empty prompts are denied."""
        judge = AISafetyJudge()
        judgment = judge.assess("")

        assert judgment.decision == Decision.DENY

    def test_assess_whitespace_only_denied(self):
        """Test that whitespace-only prompts are denied."""
        judge = AISafetyJudge()
        judgment = judge.assess("   ")

        assert judgment.decision == Decision.DENY

    def test_assess_print_without_view_denied(self):
        """Test that print alone (without view) is denied."""
        judge = AISafetyJudge()
        judgment = judge.assess("print this file")

        assert judgment.decision == Decision.DENY

    def test_assess_view_without_print_denied(self):
        """Test that view alone (without print) is denied."""
        judge = AISafetyJudge()
        judgment = judge.assess("view this file")

        assert judgment.decision == Decision.DENY

    def test_assess_dangerous_operation_denied(self):
        """Test that dangerous operations are denied."""
        judge = AISafetyJudge()
        judgment = judge.assess("format disk")

        assert judgment.decision == Decision.DENY


class TestAISafetyJudgeWithContext:
    """Test AISafetyJudge with optional context parameter."""

    def test_assess_with_context_parameter(self):
        """Test that context parameter is accepted."""
        judge = AISafetyJudge()
        judgment = judge.assess(
            "unrecognized prompt",
            context="worker_id=w123, task=test"
        )

        # Context doesn't affect decision in simple judge
        assert judgment.decision == Decision.DENY

    def test_assess_with_none_context(self):
        """Test assess with explicit None context."""
        judge = AISafetyJudge()
        judgment = judge.assess("print and view", context=None)

        assert judgment.decision == Decision.APPROVE

    def test_assess_without_context_parameter(self):
        """Test assess without context parameter (default None)."""
        judge = AISafetyJudge()
        judgment = judge.assess("confirm action")

        assert judgment.decision == Decision.ESCALATE


class TestAISafetyJudgeEdgeCases:
    """Test AISafetyJudge edge cases."""

    def test_assess_partial_keyword_match(self):
        """Test that partial matches don't trigger false positives."""
        judge = AISafetyJudge()

        # "confirmed" contains "confirm" but in different context
        judgment = judge.assess("Task confirmed as completed")
        assert judgment.decision == Decision.ESCALATE  # Still matches "confirm"

    def test_assess_multiple_keywords(self):
        """Test prompt with multiple matching keywords."""
        judge = AISafetyJudge()

        # Both "print/view" (approve) and "confirm" (escalate)
        # Escalate wins because it's checked first
        judgment = judge.assess("confirm to print and view")
        assert judgment.decision == Decision.ESCALATE

    def test_assess_special_characters(self):
        """Test prompts with special characters."""
        judge = AISafetyJudge()
        judgment = judge.assess("!@#$%^&*()_+{}|:<>?")

        assert judgment.decision == Decision.DENY

    def test_assess_unicode_characters(self):
        """Test prompts with unicode characters."""
        judge = AISafetyJudge()
        judgment = judge.assess("確認してください (confirm please)")

        # Contains "confirm" after normalization
        assert judgment.decision == Decision.ESCALATE

    def test_assess_newlines_and_tabs(self):
        """Test prompts with newlines and tabs."""
        judge = AISafetyJudge()
        judgment = judge.assess("\n\tprint\nand\tview\n")

        # Should match print and view after strip/lower
        assert judgment.decision == Decision.APPROVE
