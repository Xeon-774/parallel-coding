"""OPA (Open Policy Agent) Engine for policy evaluation.

This module provides integration with OPA for policy-based decision making.
It supports deny-by-default enforcement and audit logging.
"""

import json
import logging
from pathlib import Path
from typing import Any

import httpx

from .policy_schemas import (
    PolicyDecision,
    PolicyEvaluationResult,
    PolicyQuery,
    PolicyRequest,
    PolicyResponse,
)

logger = logging.getLogger(__name__)


class OPAEngine:
    """OPA Policy Engine for evaluating Rego policies.

    Provides deny-by-default policy enforcement with audit logging.

    Attributes:
        opa_url: URL of OPA server (default: http://localhost:8181)
        policy_dir: Directory containing Rego policy files
        deny_by_default: If True, deny when policy is not found (default: True)
        audit_log_path: Path to audit log file
    """

    def __init__(
        self,
        opa_url: str = "http://localhost:8181",
        policy_dir: str | Path | None = None,
        deny_by_default: bool = True,
        audit_log_path: str | Path | None = None,
    ) -> None:
        """Initialize OPA Engine.

        Args:
            opa_url: URL of OPA server
            policy_dir: Directory containing Rego policies
            deny_by_default: Deny when policy not found
            audit_log_path: Path to audit log file
        """
        self.opa_url = opa_url.rstrip("/")
        self.policy_dir = Path(policy_dir) if policy_dir else Path("policies")
        self.deny_by_default = deny_by_default
        self.audit_log_path = (
            Path(audit_log_path) if audit_log_path else Path("policy_audit.log")
        )
        self.client = httpx.Client(timeout=10.0)

        logger.info(f"OPA Engine initialized: {self.opa_url}")
        logger.info(f"Policy directory: {self.policy_dir}")
        logger.info(f"Deny by default: {self.deny_by_default}")

    def evaluate_policy(
        self, request: PolicyRequest
    ) -> PolicyEvaluationResult:
        """Evaluate policy for given request.

        Args:
            request: Policy evaluation request

        Returns:
            PolicyEvaluationResult with decision and reasons
        """
        # Build policy path
        policy_path = f"ai_investor/{request.resource}/{request.action}"

        # Create policy query
        query = PolicyQuery(
            input={
                "action": request.action,
                "resource": request.resource,
                "context": request.context,
            },
            policy_path=policy_path,
        )

        # Evaluate policy
        try:
            response = self._query_opa(query)
            result = self._process_response(response, policy_path)
        except Exception as e:
            logger.error(f"Policy evaluation failed: {e}")
            if self.deny_by_default:
                result = PolicyEvaluationResult(
                    allowed=False,
                    decision=PolicyDecision.DENY,
                    policy_path=policy_path,
                    reasons=[f"Policy evaluation failed: {e}"],
                    violations=["evaluation_error"],
                )
            else:
                result = PolicyEvaluationResult(
                    allowed=True,
                    decision=PolicyDecision.UNKNOWN,
                    policy_path=policy_path,
                    reasons=[f"Policy evaluation failed (allow by default): {e}"],
                    violations=[],
                )

        # Audit log
        self._audit_log(request, result)

        return result

    def _query_opa(self, query: PolicyQuery) -> PolicyResponse:
        """Query OPA server for policy decision.

        Args:
            query: Policy query

        Returns:
            PolicyResponse with decision
        """
        url = f"{self.opa_url}/v1/data/{query.policy_path.replace('/', '/data/')}"

        try:
            response = self.client.post(
                url,
                json={"input": query.input},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            data = response.json()
            result = data.get("result", {})

            # Extract decision
            decision_value = result.get(query.decision, False)
            if isinstance(decision_value, bool):
                decision = (
                    PolicyDecision.ALLOW if decision_value else PolicyDecision.DENY
                )
            else:
                decision = PolicyDecision.UNKNOWN

            return PolicyResponse(
                decision=decision,
                allowed=decision == PolicyDecision.ALLOW,
                reasons=result.get("reasons", []),
                policy_path=query.policy_path,
                metadata=result.get("metadata"),
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Policy not found: {query.policy_path}")
                if self.deny_by_default:
                    return PolicyResponse(
                        decision=PolicyDecision.DENY,
                        allowed=False,
                        reasons=["Policy not found (deny by default)"],
                        policy_path=query.policy_path,
                    )
                return PolicyResponse(
                    decision=PolicyDecision.UNKNOWN,
                    allowed=True,
                    reasons=["Policy not found (allow by default)"],
                    policy_path=query.policy_path,
                )
            raise

    def _process_response(
        self, response: PolicyResponse, policy_path: str
    ) -> PolicyEvaluationResult:
        """Process OPA response into evaluation result.

        Args:
            response: PolicyResponse from OPA
            policy_path: Policy path that was evaluated

        Returns:
            PolicyEvaluationResult
        """
        violations = []
        if not response.allowed:
            violations.append(f"policy_violation:{policy_path}")

        return PolicyEvaluationResult(
            allowed=response.allowed,
            decision=response.decision,
            policy_path=policy_path,
            reasons=response.reasons,
            violations=violations,
            metadata=response.metadata,
        )

    def _audit_log(
        self, request: PolicyRequest, result: PolicyEvaluationResult
    ) -> None:
        """Write audit log entry.

        Args:
            request: Original policy request
            result: Evaluation result
        """
        audit_entry = {
            "action": request.action,
            "resource": request.resource,
            "context": request.context,
            "decision": result.decision.value,
            "allowed": result.allowed,
            "reasons": result.reasons,
            "violations": result.violations,
            "policy_path": result.policy_path,
        }

        try:
            with open(self.audit_log_path, "a") as f:
                f.write(json.dumps(audit_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def load_policies(self) -> int:
        """Load all Rego policy files from policy directory.

        Returns:
            Number of policies loaded
        """
        if not self.policy_dir.exists():
            logger.warning(f"Policy directory not found: {self.policy_dir}")
            return 0

        policy_files = list(self.policy_dir.glob("**/*.rego"))
        logger.info(f"Found {len(policy_files)} policy files")

        loaded_count = 0
        for policy_file in policy_files:
            try:
                self._load_policy_file(policy_file)
                loaded_count += 1
            except Exception as e:
                logger.error(f"Failed to load policy {policy_file}: {e}")

        logger.info(f"Loaded {loaded_count}/{len(policy_files)} policies")
        return loaded_count

    def _load_policy_file(self, policy_file: Path) -> None:
        """Load a single Rego policy file into OPA.

        Args:
            policy_file: Path to Rego policy file
        """
        # Convert file path to policy path
        relative_path = policy_file.relative_to(self.policy_dir)
        policy_name = str(relative_path.with_suffix("")).replace("\\", "/")

        url = f"{self.opa_url}/v1/policies/{policy_name}"

        with open(policy_file) as f:
            policy_content = f.read()

        response = self.client.put(
            url,
            content=policy_content,
            headers={"Content-Type": "text/plain"},
        )
        response.raise_for_status()

        logger.debug(f"Loaded policy: {policy_name}")

    def is_healthy(self) -> bool:
        """Check if OPA server is healthy.

        Returns:
            True if OPA server is reachable and healthy
        """
        try:
            response = self.client.get(f"{self.opa_url}/health")
            return response.status_code == 200
        except Exception:
            return False

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()

    def __enter__(self) -> "OPAEngine":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
