"""
Claude Orchestrator Python SDK Client

Official Python client library for external AI applications to interact
with Claude Orchestrator API.

Example usage:
    from orchestrator_client import OrchestratorClient

    client = OrchestratorClient(
        api_url="http://localhost:8000",
        api_key="sk-orch-your-key"
    )

    # Synchronous execution
    results = client.orchestrate(
        request="Create a Todo app with FastAPI",
        wait=True
    )

    print(results['results']['summary'])
"""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


class OrchestratorError(Exception):
    """Base exception for orchestrator client errors"""

    pass


class RateLimitError(OrchestratorError):
    """Raised when rate limit is exceeded"""

    def __init__(self, message: str, retry_after: int):
        super().__init__(message)
        self.retry_after = retry_after


class JobNotFoundError(OrchestratorError):
    """Raised when job is not found"""

    pass


class AuthenticationError(OrchestratorError):
    """Raised when authentication fails"""

    pass


@dataclass
class JobProgress:
    """Job progress information"""

    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    running_tasks: int
    pending_tasks: int
    progress_percentage: float


class Job:
    """Represents an orchestration job"""

    def __init__(self, client: "OrchestratorClient", job_id: str):
        self.client = client
        self.job_id = job_id
        self._status_cache: Optional[Dict[str, Any]] = None
        self._results_cache: Optional[Dict[str, Any]] = None

    def status(self, refresh: bool = True) -> Dict[str, Any]:
        """
        Get job status

        Args:
            refresh: Force refresh from server (default True)

        Returns:
            Job status dictionary

        Raises:
            JobNotFoundError: If job doesn't exist
            OrchestratorError: On API errors
        """
        if refresh or self._status_cache is None:
            response = self.client._request("GET", f"/api/v1/jobs/{self.job_id}/status")
            self._status_cache = response
        return self._status_cache

    def results(self, refresh: bool = True) -> Dict[str, Any]:
        """
        Get job results (only available for completed jobs)

        Args:
            refresh: Force refresh from server (default True)

        Returns:
            Job results dictionary

        Raises:
            JobNotFoundError: If job doesn't exist
            OrchestratorError: If job not complete or on API errors
        """
        if refresh or self._results_cache is None:
            response = self.client._request("GET", f"/api/v1/jobs/{self.job_id}/results")
            self._results_cache = response
        return self._results_cache

    def wait_for_completion(
        self,
        poll_interval: int = 5,
        timeout: Optional[int] = None,
        callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Wait for job to complete

        Args:
            poll_interval: Seconds between status checks (default 5)
            timeout: Maximum wait time in seconds (None for no limit)
            callback: Optional callback function called on each status update
                      with signature: callback(status_dict)

        Returns:
            Job results dictionary

        Raises:
            TimeoutError: If timeout is exceeded
            OrchestratorError: On API errors
        """
        start_time = time.time()

        while True:
            status = self.status(refresh=True)

            # Call callback if provided
            if callback:
                callback(status)

            # Check if complete
            job_status = status.get("status", "")
            if job_status in ["completed", "failed", "partial", "canceled"]:
                return self.results()

            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Job did not complete within {timeout} seconds")

            time.sleep(poll_interval)

    def cancel(self) -> bool:
        """
        Cancel job

        Returns:
            True if canceled successfully, False otherwise

        Raises:
            OrchestratorError: On API errors
        """
        try:
            self.client._request("DELETE", f"/api/v1/jobs/{self.job_id}")
            self._status_cache = None  # Invalidate cache
            return True
        except JobNotFoundError:
            return False

    def is_complete(self) -> bool:
        """Check if job is complete"""
        status = self.status()
        return status.get("status") in ["completed", "failed", "partial", "canceled"]

    def is_running(self) -> bool:
        """Check if job is currently running"""
        status = self.status()
        return status.get("status") == "running"

    def is_successful(self) -> bool:
        """Check if job completed successfully"""
        status = self.status()
        return status.get("status") == "completed"

    def get_progress(self) -> JobProgress:
        """Get structured progress information"""
        status = self.status()
        progress_data = status.get("progress", {})
        return JobProgress(**progress_data)


class OrchestratorClient:
    """
    Claude Orchestrator API Client

    Official Python client for interacting with Claude Orchestrator API.
    Enables external AI applications to execute parallel AI coding tasks.
    """

    def __init__(self, api_url: str, api_key: str, timeout: int = 30):
        """
        Initialize client

        Args:
            api_url: Base URL of orchestrator API (e.g., "http://localhost:8000")
            api_key: API authentication key
            timeout: Request timeout in seconds (default 30)
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-API-Key": api_key,
                "Content-Type": "application/json",
                "User-Agent": "orchestrator-client-python/7.0.0",
            }
        )

    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Internal method to make HTTP requests"""
        url = f"{self.api_url}{path}"

        try:
            response = self.session.request(
                method, url, timeout=kwargs.pop("timeout", self.timeout), **kwargs
            )

            # Handle specific status codes
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 404:
                raise JobNotFoundError(response.json().get("error", "Resource not found"))
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise RateLimitError("Rate limit exceeded", retry_after)
            elif response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error", f"HTTP {response.status_code}")
                raise OrchestratorError(error_msg)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            raise OrchestratorError(f"Request failed: {e}")

    def orchestrate(
        self,
        request: str,
        config: Optional[Dict[str, Any]] = None,
        priority: int = 5,
        tags: Optional[List[str]] = None,
        wait: bool = False,
        poll_interval: int = 5,
        timeout: Optional[int] = None,
        progress_callback: Optional[callable] = None,
    ) -> Job | Dict[str, Any]:
        """
        Submit orchestration job

        Args:
            request: Task description (supports markdown)
            config: Optional configuration dictionary with keys:
                    - max_workers (int): Maximum parallel workers (1-10)
                    - default_timeout (int): Timeout per worker in seconds
                    - max_retries (int): Retry attempts (0-5)
                    - enable_ai_analysis (bool): Use AI task decomposition
                    - task_complexity (str): "low", "medium", or "high"
                    - execution_mode (str): "wsl" or "windows"
                    - enable_worktree (bool): Use Git worktree isolation
                    - enable_visible_workers (bool): Show worker windows
                    - enable_realtime_monitoring (bool): Enable monitoring
            priority: Job priority 1-10 (default 5)
            tags: Optional list of tags for categorization
            wait: Block until completion (default False)
            poll_interval: Seconds between checks when waiting (default 5)
            timeout: Maximum wait time when waiting (None for no limit)
            progress_callback: Callback for progress updates when waiting

        Returns:
            Job object if wait=False, results dictionary if wait=True

        Raises:
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            OrchestratorError: On other API errors
        """
        # Build request payload
        payload = {"request": request, "priority": priority}

        if config:
            payload["config"] = config

        if tags:
            payload["tags"] = tags

        # Submit job
        response = self._request("POST", "/api/v1/orchestrate", json=payload)

        job_id = response.get("job_id")
        job = Job(client=self, job_id=job_id)

        # Wait for completion if requested
        if wait:
            return job.wait_for_completion(
                poll_interval=poll_interval, timeout=timeout, callback=progress_callback
            )

        return job

    def get_job(self, job_id: str) -> Job:
        """
        Get job by ID

        Args:
            job_id: Job identifier

        Returns:
            Job object

        Raises:
            JobNotFoundError: If job doesn't exist
        """
        job = Job(client=self, job_id=job_id)
        # Verify job exists by fetching status
        job.status()
        return job

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get system capacity and health

        Returns:
            System status dictionary with keys:
            - status: "healthy", "degraded", or "overloaded"
            - available_capacity: Number of available worker slots
            - active_jobs: Number of currently running jobs
            - queued_jobs: Number of queued jobs
            - total_completed_jobs: Total jobs completed since startup
            - uptime_seconds: Server uptime in seconds
            - version: API version

        Raises:
            OrchestratorError: On API errors
        """
        return self._request("GET", "/api/v1/status")

    def health_check(self) -> bool:
        """
        Check if API is healthy

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = self._request("GET", "/api/v1/health")
            return response.get("status") == "healthy"
        except:
            return False


# Convenience function for quick usage
def orchestrate(
    request: str, api_url: str = "http://localhost:8000", api_key: str = None, **kwargs
) -> Dict[str, Any]:
    """
    Convenience function for quick orchestration

    Args:
        request: Task description
        api_url: API URL (default localhost:8000)
        api_key: API key (defaults to env ORCHESTRATOR_API_KEY)
        **kwargs: Additional arguments passed to OrchestratorClient.orchestrate()

    Returns:
        Results dictionary (always waits for completion)

    Example:
        from orchestrator_client import orchestrate

        results = orchestrate(
            request="Create a Todo API",
            config={"max_workers": 5}
        )
    """
    import os

    if api_key is None:
        api_key = os.getenv("ORCHESTRATOR_API_KEY", "sk-orch-dev-key-12345")

    client = OrchestratorClient(api_url=api_url, api_key=api_key)
    return client.orchestrate(request=request, wait=True, **kwargs)
