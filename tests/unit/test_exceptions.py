"""Unit tests for custom exception classes.

Tests all exception types, context handling, and utility functions.
"""

import time
from typing import Any, Dict

import pytest

from orchestrator.core.exceptions import (  # Base exception; Configuration errors; Worker errors; Interactive errors; Safety errors; API errors; Task errors; Resource errors; Retry errors; Utility functions
    APIError,
    AuthenticationError,
    ConfigurationError,
    ConfirmationParseError,
    DangerousOperationError,
    FileSystemError,
    InsufficientResourcesError,
    InteractiveError,
    InvalidWorkspaceError,
    JobNotFoundError,
    MissingDependencyError,
    OrchestratorException,
    PatternMatchError,
    PseudoTerminalError,
    RateLimitError,
    ResourceError,
    RetryableError,
    SafetyError,
    TaskDecompositionError,
    TaskError,
    TaskExecutionError,
    TaskValidationError,
    UserDeniedError,
    WorkerCommunicationError,
    WorkerCrashError,
    WorkerError,
    WorkerSpawnError,
    WorkerTimeoutError,
    format_exception_chain,
    wrap_exception,
)

# ======================= Base Exception Tests =======================


class TestOrchestratorException:
    """Test OrchestratorException base class."""

    def test_basic_exception_creation(self):
        """Test creating basic exception with message only."""
        exc = OrchestratorException("Test error")
        assert exc.message == "Test error"
        assert exc.context == {}
        assert exc.cause is None
        assert exc.timestamp > 0

    def test_exception_with_context(self):
        """Test exception with context information."""
        context = {"key1": "value1", "key2": 123}
        exc = OrchestratorException("Test error", context=context)
        assert exc.context == context
        assert "key1=value1" in str(exc)
        assert "key2=123" in str(exc)

    def test_exception_with_cause(self):
        """Test exception with cause chain."""
        original = ValueError("Original error")
        exc = OrchestratorException("Wrapper error", cause=original)
        assert exc.cause == original
        assert "Caused by: ValueError: Original error" in str(exc)

    def test_exception_with_all_parameters(self):
        """Test exception with all parameters."""
        original = ValueError("Original")
        context = {"key": "value"}
        exc = OrchestratorException("Message", context=context, cause=original)

        exc_str = str(exc)
        assert "Message" in exc_str
        assert "key=value" in exc_str
        assert "Caused by: ValueError: Original" in exc_str

    def test_exception_string_formatting_without_context(self):
        """Test string formatting with no context or cause."""
        exc = OrchestratorException("Simple error")
        assert str(exc) == "Simple error"


# ======================= Configuration Error Tests =======================


class TestConfigurationErrors:
    """Test configuration - related exception classes."""

    def test_configuration_error(self):
        """Test ConfigurationError creation."""
        exc = ConfigurationError("Invalid config")
        assert exc.message == "Invalid config"
        assert isinstance(exc, OrchestratorException)

    def test_invalid_workspace_error(self):
        """Test InvalidWorkspaceError creation."""
        exc = InvalidWorkspaceError("Workspace not found", context={"path": "/invalid / path"})
        assert exc.message == "Workspace not found"
        assert isinstance(exc, ConfigurationError)
        assert "path=/invalid / path" in str(exc)

    def test_missing_dependency_error(self):
        """Test MissingDependencyError creation."""
        exc = MissingDependencyError("Git not found", context={"dependency": "git"})
        assert exc.message == "Git not found"
        assert isinstance(exc, ConfigurationError)


# ======================= Worker Error Tests =======================


class TestWorkerErrors:
    """Test worker - related exception classes."""

    def test_worker_error(self):
        """Test WorkerError base class."""
        exc = WorkerError("Worker failed")
        assert exc.message == "Worker failed"
        assert isinstance(exc, OrchestratorException)

    def test_worker_spawn_error(self):
        """Test WorkerSpawnError creation."""
        exc = WorkerSpawnError("Failed to spawn worker", context={"worker_id": "w_123"})
        assert exc.message == "Failed to spawn worker"
        assert isinstance(exc, WorkerError)

    def test_worker_timeout_error(self):
        """Test WorkerTimeoutError with timeout and worker_id."""
        exc = WorkerTimeoutError("Worker timed out", worker_id="w_123", timeout=300.0)
        assert exc.message == "Worker timed out"
        assert exc.worker_id == "w_123"
        assert exc.timeout == 300.0
        assert "worker_id=w_123" in str(exc)
        assert "timeout=300.0" in str(exc)

    def test_worker_timeout_error_with_context(self):
        """Test WorkerTimeoutError with additional context."""
        exc = WorkerTimeoutError(
            "Worker timed out", worker_id="w_456", timeout=600.0, context={"task": "Build project"}
        )
        assert exc.context["task"] == "Build project"
        assert exc.context["worker_id"] == "w_456"
        assert exc.context["timeout"] == 600.0

    def test_worker_crash_error(self):
        """Test WorkerCrashError with exit code."""
        exc = WorkerCrashError("Worker crashed", worker_id="w_789", exit_code=1)
        assert exc.message == "Worker crashed"
        assert exc.worker_id == "w_789"
        assert exc.exit_code == 1
        assert "worker_id=w_789" in str(exc)
        assert "exit_code=1" in str(exc)

    def test_worker_crash_error_no_exit_code(self):
        """Test WorkerCrashError with None exit code."""
        exc = WorkerCrashError("Worker crashed", worker_id="w_999", exit_code=None)
        assert exc.exit_code is None
        assert "exit_code=None" in str(exc)

    def test_worker_communication_error(self):
        """Test WorkerCommunicationError creation."""
        exc = WorkerCommunicationError("Failed to communicate", context={"worker_id": "w_123"})
        assert exc.message == "Failed to communicate"
        assert isinstance(exc, WorkerError)


# ======================= Interactive Error Tests =======================


class TestInteractiveErrors:
    """Test interactive mode exception classes."""

    def test_interactive_error(self):
        """Test InteractiveError base class."""
        exc = InteractiveError("Interactive mode failed")
        assert exc.message == "Interactive mode failed"
        assert isinstance(exc, OrchestratorException)

    def test_pseudo_terminal_error(self):
        """Test PseudoTerminalError with platform."""
        exc = PseudoTerminalError("PTY creation failed", platform="windows")
        assert exc.message == "PTY creation failed"
        assert exc.platform == "windows"
        assert "platform=windows" in str(exc)

    def test_pseudo_terminal_error_with_context(self):
        """Test PseudoTerminalError with additional context."""
        exc = PseudoTerminalError("PTY error", platform="linux", context={"error_code": 13})
        assert exc.context["platform"] == "linux"
        assert exc.context["error_code"] == 13

    def test_pattern_match_error(self):
        """Test PatternMatchError with pattern and output."""
        exc = PatternMatchError(
            "Pattern not found", pattern="Expected prompt", output="Actual output here"
        )
        assert exc.message == "Pattern not found"
        assert exc.pattern == "Expected prompt"
        assert exc.output == "Actual output here"
        assert "pattern=Expected prompt" in str(exc)
        assert "output_length=18" in str(exc)  # "Actual output here" is 18 chars

    def test_pattern_match_error_with_long_output(self):
        """Test PatternMatchError stores output length, not full output."""
        long_output = "x" * 1000
        exc = PatternMatchError("Pattern not found", pattern="test", output=long_output)
        assert exc.output == long_output
        assert "output_length=1000" in str(exc)
        # Full output is NOT in the string representation
        assert "x" * 100 not in str(exc)

    def test_confirmation_parse_error(self):
        """Test ConfirmationParseError with raw message."""
        exc = ConfirmationParseError("Failed to parse confirmation", raw_message="Invalid JSON")
        assert exc.message == "Failed to parse confirmation"
        assert exc.raw_message == "Invalid JSON"
        assert "raw_message=Invalid JSON" in str(exc)


# ======================= Safety Error Tests =======================


class TestSafetyErrors:
    """Test safety - related exception classes."""

    def test_safety_error(self):
        """Test SafetyError base class."""
        exc = SafetyError("Safety violation")
        assert exc.message == "Safety violation"
        assert isinstance(exc, OrchestratorException)

    def test_dangerous_operation_error(self):
        """Test DangerousOperationError with operation type and details."""
        exc = DangerousOperationError(
            "Operation blocked", operation_type="FILE_DELETE", details={"file": "/etc / passwd"}
        )
        assert exc.message == "Operation blocked"
        assert exc.operation_type == "FILE_DELETE"
        assert exc.details == {"file": "/etc / passwd"}
        assert "operation_type=FILE_DELETE" in str(exc)

    def test_dangerous_operation_error_with_context(self):
        """Test DangerousOperationError with additional context."""
        exc = DangerousOperationError(
            "Operation blocked",
            operation_type="SYSTEM_MODIFY",
            details={"command": "rm -rf /"},
            context={"worker_id": "w_123"},
        )
        assert exc.context["worker_id"] == "w_123"
        assert exc.context["operation_type"] == "SYSTEM_MODIFY"

    def test_user_denied_error(self):
        """Test UserDeniedError with operation type."""
        exc = UserDeniedError("User denied operation", operation_type="FILE_WRITE")
        assert exc.message == "User denied operation"
        assert exc.operation_type == "FILE_WRITE"
        assert "operation_type=FILE_WRITE" in str(exc)


# ======================= API Error Tests =======================


class TestAPIErrors:
    """Test API - related exception classes."""

    def test_api_error(self):
        """Test APIError base class."""
        exc = APIError("API failed")
        assert exc.message == "API failed"
        assert isinstance(exc, OrchestratorException)

    def test_authentication_error(self):
        """Test AuthenticationError creation."""
        exc = AuthenticationError("Authentication failed", context={"user_id": "user_123"})
        assert exc.message == "Authentication failed"
        assert isinstance(exc, APIError)

    def test_rate_limit_error(self):
        """Test RateLimitError with limit and retry_after."""
        exc = RateLimitError("Rate limit exceeded", limit=100, retry_after=60.0)
        assert exc.message == "Rate limit exceeded"
        assert exc.limit == 100
        assert exc.retry_after == 60.0
        assert "limit=100" in str(exc)
        assert "retry_after=60.0" in str(exc)

    def test_rate_limit_error_no_retry_after(self):
        """Test RateLimitError with None retry_after."""
        exc = RateLimitError("Rate limit exceeded", limit=50, retry_after=None)
        assert exc.retry_after is None

    def test_job_not_found_error(self):
        """Test JobNotFoundError with job_id."""
        exc = JobNotFoundError("Job not found", job_id="job_123")
        assert exc.message == "Job not found"
        assert exc.job_id == "job_123"
        assert "job_id=job_123" in str(exc)


# ======================= Task Error Tests =======================


class TestTaskErrors:
    """Test task - related exception classes."""

    def test_task_error(self):
        """Test TaskError base class."""
        exc = TaskError("Task failed")
        assert exc.message == "Task failed"
        assert isinstance(exc, OrchestratorException)

    def test_task_validation_error(self):
        """Test TaskValidationError creation."""
        exc = TaskValidationError("Invalid task parameters", context={"field": "timeout"})
        assert exc.message == "Invalid task parameters"
        assert isinstance(exc, TaskError)

    def test_task_decomposition_error(self):
        """Test TaskDecompositionError creation."""
        exc = TaskDecompositionError("Failed to split task", context={"task": "Complex operation"})
        assert exc.message == "Failed to split task"
        assert isinstance(exc, TaskError)

    def test_task_execution_error(self):
        """Test TaskExecutionError with task_name and worker_id."""
        exc = TaskExecutionError("Execution failed", task_name="Build project", worker_id="w_123")
        assert exc.message == "Execution failed"
        assert exc.task_name == "Build project"
        assert exc.worker_id == "w_123"
        assert "task_name=Build project" in str(exc)
        assert "worker_id=w_123" in str(exc)

    def test_task_execution_error_no_worker(self):
        """Test TaskExecutionError with None worker_id."""
        exc = TaskExecutionError("Execution failed", task_name="Test task", worker_id=None)
        assert exc.worker_id is None


# ======================= Resource Error Tests =======================


class TestResourceErrors:
    """Test resource - related exception classes."""

    def test_resource_error(self):
        """Test ResourceError base class."""
        exc = ResourceError("Resource unavailable")
        assert exc.message == "Resource unavailable"
        assert isinstance(exc, OrchestratorException)

    def test_insufficient_resources_error(self):
        """Test InsufficientResourcesError with resource details."""
        exc = InsufficientResourcesError(
            "Not enough workers", resource_type="workers", required=5, available=2
        )
        assert exc.message == "Not enough workers"
        assert exc.resource_type == "workers"
        assert exc.required == 5
        assert exc.available == 2
        assert "resource_type=workers" in str(exc)
        assert "required=5" in str(exc)
        assert "available=2" in str(exc)

    def test_insufficient_resources_error_with_context(self):
        """Test InsufficientResourcesError with additional context."""
        exc = InsufficientResourcesError(
            "Memory limit",
            resource_type="memory",
            required="16GB",
            available="8GB",
            context={"node": "node_1"},
        )
        assert exc.context["node"] == "node_1"
        assert exc.context["resource_type"] == "memory"

    def test_file_system_error(self):
        """Test FileSystemError with path and operation."""
        exc = FileSystemError("File not found", path="/tmp / test.txt", operation="read")
        assert exc.message == "File not found"
        assert exc.path == "/tmp / test.txt"
        assert exc.operation == "read"
        assert "path=/tmp / test.txt" in str(exc)
        assert "operation=read" in str(exc)


# ======================= Retry Error Tests =======================


class TestRetryableError:
    """Test RetryableError functionality."""

    def test_retryable_error_defaults(self):
        """Test RetryableError with default parameters."""
        exc = RetryableError("Transient error")
        assert exc.message == "Transient error"
        assert exc.max_retries == 3
        assert exc.retry_delay == 1.0
        assert exc.retry_count == 0
        assert exc.can_retry() is True

    def test_retryable_error_custom_parameters(self):
        """Test RetryableError with custom retry parameters."""
        exc = RetryableError("Transient error", max_retries=5, retry_delay=2.5)
        assert exc.max_retries == 5
        assert exc.retry_delay == 2.5

    def test_retryable_error_with_cause(self):
        """Test RetryableError with cause exception."""
        original = ConnectionError("Network timeout")
        exc = RetryableError("Connection failed", cause=original)
        assert exc.cause == original
        assert "Caused by: ConnectionError" in str(exc)

    def test_can_retry_returns_true_before_max(self):
        """Test can_retry returns True before max retries."""
        exc = RetryableError("Error", max_retries=3)
        assert exc.can_retry() is True
        exc.increment_retry()
        assert exc.can_retry() is True
        exc.increment_retry()
        assert exc.can_retry() is True

    def test_can_retry_returns_false_at_max(self):
        """Test can_retry returns False at max retries."""
        exc = RetryableError("Error", max_retries=2)
        exc.increment_retry()
        exc.increment_retry()
        assert exc.retry_count == 2
        assert exc.can_retry() is False

    def test_increment_retry(self):
        """Test increment_retry updates count."""
        exc = RetryableError("Error")
        assert exc.retry_count == 0
        exc.increment_retry()
        assert exc.retry_count == 1
        exc.increment_retry()
        assert exc.retry_count == 2


# ======================= Utility Function Tests =======================


class TestWrapException:
    """Test wrap_exception utility function."""

    def test_wrap_exception_basic(self):
        """Test wrapping exception with new type."""
        original = ValueError("Original error")
        wrapped = wrap_exception(original, ConfigurationError, "Configuration failed")
        assert isinstance(wrapped, ConfigurationError)
        assert wrapped.message == "Configuration failed"
        assert wrapped.cause == original

    def test_wrap_exception_with_context(self):
        """Test wrapping exception with context."""
        original = KeyError("missing_key")
        wrapped = wrap_exception(
            original, TaskValidationError, "Task validation failed", context={"key": "missing_key"}
        )
        assert wrapped.context["key"] == "missing_key"
        assert wrapped.cause == original


class TestFormatExceptionChain:
    """Test format_exception_chain utility function."""

    def test_format_single_exception(self):
        """Test formatting single exception."""
        exc = ValueError("Test error")
        formatted = format_exception_chain(exc)
        assert "ValueError: Test error" in formatted
        assert "Caused by" not in formatted

    def test_format_exception_chain_with_cause(self):
        """Test formatting exception chain with cause."""
        original = ValueError("Original")
        wrapped = OrchestratorException("Wrapped", cause=original)
        formatted = format_exception_chain(wrapped)

        assert "OrchestratorException: Wrapped" in formatted
        assert "Caused by: ValueError: Original" in formatted

    def test_format_exception_chain_multiple_levels(self):
        """Test formatting multi - level exception chain."""
        level1 = ValueError("Level 1")
        level2 = OrchestratorException("Level 2", cause=level1)
        level3 = ConfigurationError("Level 3", cause=level2)

        formatted = format_exception_chain(level3)

        assert "ConfigurationError: Level 3" in formatted
        assert "OrchestratorException: Level 2" in formatted
        assert "ValueError: Level 1" in formatted
        # Count "Caused by:" in the formatted chain (appears multiple times due to nested __str__)
        assert "Caused by:" in formatted

    def test_format_exception_with_builtin_cause(self):
        """Test formatting with __cause__ attribute."""
        try:
            try:
                raise ValueError("Original")
            except ValueError as e:
                raise ConfigurationError("Wrapped") from e
        except ConfigurationError as exc:
            formatted = format_exception_chain(exc)
            assert "ConfigurationError: Wrapped" in formatted
            assert "ValueError: Original" in formatted
