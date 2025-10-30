"""Tests for OPA Policy Engine."""

from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest

from orchestrator.policy.opa_engine import OPAEngine
from orchestrator.policy.policy_schemas import (
    PolicyDecision,
    PolicyRequest,
    PolicyResponse,
)


@pytest.fixture
def opa_engine() -> OPAEngine:
    """Create OPA engine instance for testing."""
    return OPAEngine(
        opa_url="http://localhost:8181",
        policy_dir="policies",
        deny_by_default=True,
        audit_log_path="test_audit.log",
    )


@pytest.fixture
def mock_httpx_client() -> Mock:
    """Create mock httpx client."""
    mock_client = Mock(spec=httpx.Client)
    return mock_client


class TestOPAEngine:
    """Test OPA Engine class."""

    def test_init(self, opa_engine: OPAEngine) -> None:
        """Test OPA engine initialization."""
        assert opa_engine.opa_url == "http://localhost:8181"
        assert opa_engine.policy_dir == Path("policies")
        assert opa_engine.deny_by_default is True
        assert opa_engine.audit_log_path == Path("test_audit.log")

    def test_init_strips_trailing_slash(self) -> None:
        """Test that trailing slash is stripped from OPA URL."""
        engine = OPAEngine(opa_url="http://localhost:8181/")
        assert engine.opa_url == "http://localhost:8181"

    def test_evaluate_policy_allow(self, opa_engine: OPAEngine, mock_httpx_client: Mock) -> None:
        """Test policy evaluation with ALLOW decision."""
        request = PolicyRequest(
            action="execute",
            resource="sandbox",
            context={"risk_level": "LOW"},
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "allow": True,
                "reasons": ["Risk level is LOW"],
            }
        }
        mock_httpx_client.post.return_value = mock_response

        with patch.object(opa_engine, "client", mock_httpx_client):
            result = opa_engine.evaluate_policy(request)

        assert result.allowed is True
        assert result.decision == PolicyDecision.ALLOW
        assert result.policy_path == "ai_investor / sandbox / execute"
        assert "Risk level is LOW" in result.reasons

    def test_evaluate_policy_deny(self, opa_engine: OPAEngine, mock_httpx_client: Mock) -> None:
        """Test policy evaluation with DENY decision."""
        request = PolicyRequest(
            action="execute",
            resource="sandbox",
            context={"risk_level": "HIGH", "approved_by": None},
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "allow": False,
                "reasons": ["HIGH risk execution requires approval"],
            }
        }
        mock_httpx_client.post.return_value = mock_response

        with patch.object(opa_engine, "client", mock_httpx_client):
            result = opa_engine.evaluate_policy(request)

        assert result.allowed is False
        assert result.decision == PolicyDecision.DENY
        assert result.policy_path == "ai_investor / sandbox / execute"
        assert len(result.violations) > 0

    def test_evaluate_policy_not_found_deny_by_default(
        self, opa_engine: OPAEngine, mock_httpx_client: Mock
    ) -> None:
        """Test policy evaluation when policy not found (deny by default)."""
        request = PolicyRequest(
            action="unknown_action",
            resource="unknown_resource",
            context={},
        )

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )
        mock_httpx_client.post.return_value = mock_response

        with patch.object(opa_engine, "client", mock_httpx_client):
            result = opa_engine.evaluate_policy(request)

        assert result.allowed is False
        assert result.decision == PolicyDecision.DENY
        assert "Policy not found" in result.reasons[0]

    def test_evaluate_policy_not_found_allow_by_default(self, mock_httpx_client: Mock) -> None:
        """Test policy evaluation when policy not found (allow by default)."""
        engine = OPAEngine(deny_by_default=False)
        request = PolicyRequest(
            action="unknown_action",
            resource="unknown_resource",
            context={},
        )

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )
        mock_httpx_client.post.return_value = mock_response

        with patch.object(engine, "client", mock_httpx_client):
            result = engine.evaluate_policy(request)

        assert result.allowed is True
        assert result.decision == PolicyDecision.UNKNOWN

    def test_evaluate_policy_error_deny_by_default(
        self, opa_engine: OPAEngine, mock_httpx_client: Mock
    ) -> None:
        """Test policy evaluation when error occurs (deny by default)."""
        request = PolicyRequest(
            action="execute",
            resource="sandbox",
            context={"risk_level": "LOW"},
        )

        mock_httpx_client.post.side_effect = httpx.ConnectError("Connection refused")

        with patch.object(opa_engine, "client", mock_httpx_client):
            result = opa_engine.evaluate_policy(request)

        assert result.allowed is False
        assert result.decision == PolicyDecision.DENY
        assert "evaluation_error" in result.violations

    def test_process_response(self, opa_engine: OPAEngine) -> None:
        """Test processing OPA response."""
        response = PolicyResponse(
            decision=PolicyDecision.ALLOW,
            allowed=True,
            reasons=["Test reason"],
            policy_path="test / policy",
            metadata={"test": "data"},
        )

        result = opa_engine._process_response(response, "test / policy")

        assert result.allowed is True
        assert result.decision == PolicyDecision.ALLOW
        assert result.reasons == ["Test reason"]
        assert result.metadata == {"test": "data"}
        assert len(result.violations) == 0

    def test_process_response_denied(self, opa_engine: OPAEngine) -> None:
        """Test processing denied OPA response."""
        response = PolicyResponse(
            decision=PolicyDecision.DENY,
            allowed=False,
            reasons=["Access denied"],
            policy_path="test / policy",
        )

        result = opa_engine._process_response(response, "test / policy")

        assert result.allowed is False
        assert result.decision == PolicyDecision.DENY
        assert "policy_violation:test / policy" in result.violations

    def test_is_healthy_success(self, opa_engine: OPAEngine, mock_httpx_client: Mock) -> None:
        """Test health check when OPA is healthy."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_httpx_client.get.return_value = mock_response

        with patch.object(opa_engine, "client", mock_httpx_client):
            assert opa_engine.is_healthy() is True

    def test_is_healthy_failure(self, opa_engine: OPAEngine, mock_httpx_client: Mock) -> None:
        """Test health check when OPA is unhealthy."""
        mock_httpx_client.get.side_effect = httpx.ConnectError("Connection refused")

        with patch.object(opa_engine, "client", mock_httpx_client):
            assert opa_engine.is_healthy() is False

    def test_context_manager(self, opa_engine: OPAEngine) -> None:
        """Test OPA engine as context manager."""
        with patch.object(opa_engine, "close") as mock_close:
            with opa_engine as engine:
                assert engine is opa_engine
            mock_close.assert_called_once()

    def test_policy_evaluation_result_bool(self) -> None:
        """Test PolicyEvaluationResult can be used as boolean."""
        from orchestrator.policy.policy_schemas import PolicyEvaluationResult

        allowed_result = PolicyEvaluationResult(
            allowed=True,
            decision=PolicyDecision.ALLOW,
            policy_path="test",
            reasons=[],
            violations=[],
        )
        assert bool(allowed_result) is True

        denied_result = PolicyEvaluationResult(
            allowed=False,
            decision=PolicyDecision.DENY,
            policy_path="test",
            reasons=[],
            violations=[],
        )
        assert bool(denied_result) is False


class TestPolicySchemas:
    """Test policy schema classes."""

    def test_policy_decision_enum(self) -> None:
        """Test PolicyDecision enum values."""
        assert PolicyDecision.ALLOW.value == "allow"
        assert PolicyDecision.DENY.value == "deny"
        assert PolicyDecision.UNKNOWN.value == "unknown"

    def test_policy_request_creation(self) -> None:
        """Test PolicyRequest creation."""
        request = PolicyRequest(
            action="execute",
            resource="sandbox",
            context={"risk_level": "LOW"},
        )

        assert request.action == "execute"
        assert request.resource == "sandbox"
        assert request.context == {"risk_level": "LOW"}
