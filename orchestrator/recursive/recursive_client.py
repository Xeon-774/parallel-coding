"""Recursive orchestrator async client with robust error handling.

Implements an async HTTP client using httpx for submitting and tracking
recursive orchestration jobs. Includes:
- Input validation (API key, URL, ranges)
- Retry with exponential backoff and jitter
- Context manager for connection pooling
- Sync wrapper for convenience

No sensitive data (e.g., API keys) are logged or included in exceptions.
"""

from __future__ import annotations

import asyncio
import math
import random
from typing import Any, AsyncGenerator, Dict, Optional

import httpx
from pydantic import BaseModel, Field


class APIError(RuntimeError):
    """Base API error for orchestrator client."""


class ClientValidationError(ValueError):
    """Client - side validation failure."""


class AuthenticationError(APIError):
    """Authentication or authorization error."""


class NetworkError(APIError):
    """Network - related error, e.g., timeouts or connection issues."""


class APIKeyValidator:
    """Validate API keys for recursive calls.

    Security policy:
    - Must be non - empty
    - At least 32 characters
    - Start with "sk - orch-"
    """

    _MIN_LENGTH = 32
    _PREFIX = "sk - orch-"

    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate API key format and strength.

        Args:
            api_key: API key to validate

        Returns:
            True if valid, False otherwise (never returns False, raises).

        Raises:
            ValueError: If API key is invalid
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
        if len(api_key) < APIKeyValidator._MIN_LENGTH:
            raise ValueError(f"API key must be at least {APIKeyValidator._MIN_LENGTH} characters")
        if not api_key.startswith(APIKeyValidator._PREFIX):
            raise ValueError("Invalid API key prefix")
        return True


class OrchestrateRequest(BaseModel):
    """Request to orchestrator API."""

    request: str = Field(..., description="Task description")
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional orchestration configuration"
    )


class JobStatus(BaseModel):
    """Job status response from orchestrator."""

    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: Dict[str, Any]
    results: Optional[Dict[str, Any]] = None


class RecursiveOrchestratorClient:
    """Async client for calling orchestrator API recursively.

    Usage example:
        async with RecursiveOrchestratorClient(
            api_url="http://localhost:8000",
            api_key="sk - orch-" + "x" * 32,
        ) as client:
            job_id = await client.submit_job(
                request="Create authentication module",
                max_workers=3,
                current_depth=1,
            )

            async for status in client.poll_job(job_id):
                if status.status in {"completed", "failed"}:
                    break

            results = await client.get_results(job_id)
    """

    def __init__(
        self, api_url: str, api_key: str, timeout: int = 300, max_retries: int = 3
    ) -> None:
        """Initialize recursive orchestrator client.

        Args:
            api_url: Orchestrator API base URL.
            api_key: API key for authentication.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts for transient errors.

        Raises:
            ClientValidationError: If inputs are invalid.
        """
        if not api_url or not api_url.startswith(("http://", "https://")):
            raise ClientValidationError("Invalid API URL")
        try:
            APIKeyValidator.validate_api_key(api_key)
        except ValueError as e:  # re - wrap with typed error
            raise ClientValidationError(str(e))

        if timeout <= 0:
            raise ClientValidationError("timeout must be positive")
        if max_retries < 0 or max_retries > 10:
            raise ClientValidationError("max_retries must be between 0 and 10")

        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "RecursiveOrchestratorClient":
        """Async context manager entry creating a pooled client instance."""
        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={"X - API - Key": self.api_key},
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit closing the HTTP client."""
        if self.client is not None:
            await self.client.aclose()

    # ------------------------------- Internal -------------------------------
    async def _request_with_retry(
        self, method: str, url: str, *, json: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """Execute an HTTP request with retry and exponential backoff.

        Args:
            method: HTTP method (e.g., "GET", "POST").
            url: Path relative to base_url.
            json: Optional JSON payload.

        Returns:
            httpx.Response on success.

        Raises:
            APIError: When non - retriable or exhausted retries occur.
        """
        assert self.client is not None, "Client context not entered"
        retries = 0
        while True:
            try:
                response = await self.client.request(method, url, json=json)
                if response.status_code == 401:
                    raise AuthenticationError("Unauthorized (401)")
                response.raise_for_status()
                return response
            except httpx.TimeoutException as e:
                if retries >= self.max_retries:
                    raise NetworkError(f"Request timed out after {retries} retries") from e
            except httpx.RequestError as e:
                if retries >= self.max_retries:
                    raise NetworkError(f"Network error after {retries} retries: {e}") from e
            except httpx.HTTPStatusError as e:
                # Non - 2xx response other than 401 already handled above
                # Consider 5xx retriable, 4xx non - retriable
                status = e.response.status_code
                if 500 <= status < 600 and retries < self.max_retries:
                    pass
                else:
                    raise APIError(f"HTTP error {status}: {e.response.text}") from e

            # Backoff before next try
            retries += 1
            await self._sleep_backoff(retries)

    @staticmethod
    async def _sleep_backoff(retries: int) -> None:
        """Sleep with exponential backoff and jitter.

        Args:
            retries: Current retry attempt number (1 - based).

        Notes:
            Uses base 0.2s with exponential factor and random jitter to avoid
            thundering herd effects.
        """
        base = 0.2
        # cap exponential for safety
        delay = min(base * (2 ** (retries - 1)), 5.0)
        jitter = random.uniform(0, 0.1)
        await asyncio.sleep(delay + jitter)

    # ------------------------------ Public API ------------------------------
    async def submit_job(
        self,
        request: str,
        *,
        max_workers: int = 3,
        current_depth: int = 1,
        parent_job_id: Optional[str] = None,
    ) -> str:
        """Submit a new orchestration job.

        Args:
            request: Task description (min 10 chars).
            max_workers: Maximum parallel workers (1..10).
            current_depth: Current recursion depth (0..5).
            parent_job_id: Optional parent job identifier.

        Returns:
            The created job ID.

        Raises:
            ClientValidationError: If inputs are invalid.
            APIError: If the API returns an error.
        """
        if not request or len(request.strip()) < 10:
            raise ClientValidationError("Request must be at least 10 characters")
        if not (1 <= max_workers <= 10):
            raise ClientValidationError("max_workers must be between 1 and 10")
        if not (0 <= current_depth <= 5):
            raise ClientValidationError("current_depth must be between 0 and 5")

        payload = OrchestrateRequest(
            request=request.strip(),
            config={
                "max_workers": max_workers,
                "current_depth": current_depth,
                "parent_job_id": parent_job_id,
                "enable_ai_analysis": True,
            },
        )

        response = await self._request_with_retry(
            "POST", "/api / v1 / orchestrate", json=payload.model_dump()
        )
        data = response.json()
        job_id = data.get("job_id")
        if not isinstance(job_id, str) or not job_id:
            raise APIError("API did not return a valid job_id")
        return job_id

    async def poll_job(
        self, job_id: str, *, poll_interval: int = 5
    ) -> AsyncGenerator[JobStatus, None]:
        """Poll job status until completion.

        Args:
            job_id: Job identifier to poll.
            poll_interval: Seconds to wait between polls.

        Yields:
            JobStatus objects on each poll.

        Raises:
            ClientValidationError: If inputs are invalid.
            APIError: If polling fails fatally.
        """
        if not job_id:
            raise ClientValidationError("job_id cannot be empty")
        if poll_interval <= 0:
            raise ClientValidationError("poll_interval must be positive")

        while True:
            response = await self._request_with_retry("GET", f"/api / v1 / jobs/{job_id}/status")
            status = JobStatus(**response.json())
            yield status
            if status.status in ("completed", "failed"):
                break
            await asyncio.sleep(poll_interval)

    async def get_results(self, job_id: str) -> Dict[str, Any]:
        """Retrieve job results.

        Args:
            job_id: Job identifier whose results should be retrieved.

        Returns:
            Parsed JSON results dictionary.

        Raises:
            ClientValidationError: If job_id is invalid.
            APIError: If the API responds with an error.
        """
        if not job_id:
            raise ClientValidationError("job_id cannot be empty")
        response = await self._request_with_retry("GET", f"/api / v1 / jobs/{job_id}/results")
        data = response.json()
        if not isinstance(data, dict):
            raise APIError("API returned invalid results payload")
        return data


class RecursiveOrchestratorSyncClient:
    """Synchronous wrapper for RecursiveOrchestratorClient.

    This convenience class manages the asyncio loop and delegates to the
    async client while preserving a simple synchronous interface.
    """

    def __init__(self, api_url: str, api_key: str) -> None:
        self._api_url = api_url
        self._api_key = api_key

    def submit_job(self, request: str, **kwargs: Any) -> str:
        """Submit a job synchronously.

        Args:
            request: Task description.
            **kwargs: Additional arguments forwarded to async client.

        Returns:
            Job ID string.
        """

        async def _submit() -> str:
            async with RecursiveOrchestratorClient(self._api_url, self._api_key) as client:
                return await client.submit_job(request, **kwargs)

        return asyncio.run(_submit())

    def wait_for_completion(self, job_id: str, *, poll_interval: int = 5) -> Dict[str, Any]:
        """Wait for a job to complete and return results synchronously.

        Args:
            job_id: Job identifier.
            poll_interval: Seconds between polls.

        Returns:
            Results dictionary from the API.
        """

        async def _wait() -> Dict[str, Any]:
            async with RecursiveOrchestratorClient(self._api_url, self._api_key) as client:
                async for status in client.poll_job(job_id, poll_interval=poll_interval):
                    if status.status in ("completed", "failed"):
                        return await client.get_results(job_id)
            # Should never reach here; loop breaks above
            return {}

        return asyncio.run(_wait())
