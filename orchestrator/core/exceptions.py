"""
Custom Exception Classes for Enhanced Error Handling (v8.0)

Provides granular exception types for better error diagnosis and handling.
All exceptions include contextual information for debugging.
"""

from typing import Optional, Dict, Any, Type
import time


class OrchestratorException(Exception):
    """Base exception for all orchestrator errors"""

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize orchestrator exception

        Args:
            message: Human-readable error message
            context: Additional context information
            cause: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.cause = cause
        self.timestamp = time.time()

    def __str__(self) -> str:
        """Format exception with context"""
        parts = [self.message]

        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")

        if self.cause:
            parts.append(f"Caused by: {type(self.cause).__name__}: {str(self.cause)}")

        return " | ".join(parts)


# ============================================================================
# Configuration Errors
# ============================================================================


class ConfigurationError(OrchestratorException):
    """Configuration is invalid or missing"""

    pass


class InvalidWorkspaceError(ConfigurationError):
    """Workspace directory is invalid or inaccessible"""

    pass


class MissingDependencyError(ConfigurationError):
    """Required dependency is not installed or configured"""

    pass


# ============================================================================
# Worker Errors
# ============================================================================


class WorkerError(OrchestratorException):
    """Base exception for worker-related errors"""

    pass


class WorkerSpawnError(WorkerError):
    """Failed to spawn worker process"""

    pass


class WorkerTimeoutError(WorkerError):
    """Worker exceeded timeout limit"""

    def __init__(
        self, message: str, worker_id: str, timeout: float, context: Optional[Dict[str, Any]] = None
    ):
        context = context or {}
        context.update({"worker_id": worker_id, "timeout": timeout})
        super().__init__(message, context=context)
        self.worker_id = worker_id
        self.timeout = timeout


class WorkerCrashError(WorkerError):
    """Worker process crashed unexpectedly"""

    def __init__(
        self,
        message: str,
        worker_id: str,
        exit_code: Optional[int],
        context: Optional[Dict[str, Any]] = None,
    ):
        context = context or {}
        context.update({"worker_id": worker_id, "exit_code": exit_code})
        super().__init__(message, context=context)
        self.worker_id = worker_id
        self.exit_code = exit_code


class WorkerCommunicationError(WorkerError):
    """Failed to communicate with worker"""

    pass


# ============================================================================
# Interactive Mode Errors
# ============================================================================


class InteractiveError(OrchestratorException):
    """Base exception for interactive mode errors"""

    pass


class PseudoTerminalError(InteractiveError):
    """Failed to create or control pseudo-terminal"""

    def __init__(self, message: str, platform: str, context: Optional[Dict[str, Any]] = None):
        context = context or {}
        context.update({"platform": platform})
        super().__init__(message, context=context)
        self.platform = platform


class PatternMatchError(InteractiveError):
    """Failed to match expected pattern in output"""

    def __init__(
        self, message: str, pattern: str, output: str, context: Optional[Dict[str, Any]] = None
    ):
        context = context or {}
        context.update({"pattern": pattern, "output_length": len(output)})
        super().__init__(message, context=context)
        self.pattern = pattern
        self.output = output


class ConfirmationParseError(InteractiveError):
    """Failed to parse confirmation request"""

    def __init__(self, message: str, raw_message: str, context: Optional[Dict[str, Any]] = None):
        context = context or {}
        context.update({"raw_message": raw_message})
        super().__init__(message, context=context)
        self.raw_message = raw_message


# ============================================================================
# Safety Errors
# ============================================================================


class SafetyError(OrchestratorException):
    """Base exception for safety-related errors"""

    pass


class DangerousOperationError(SafetyError):
    """Operation was blocked as dangerous"""

    def __init__(
        self,
        message: str,
        operation_type: str,
        details: Dict[str, str],
        context: Optional[Dict[str, Any]] = None,
    ):
        context = context or {}
        context.update({"operation_type": operation_type, "details": details})
        super().__init__(message, context=context)
        self.operation_type = operation_type
        self.details = details


class UserDeniedError(SafetyError):
    """User denied operation approval"""

    def __init__(self, message: str, operation_type: str, context: Optional[Dict[str, Any]] = None):
        context = context or {}
        context.update({"operation_type": operation_type})
        super().__init__(message, context=context)
        self.operation_type = operation_type


# ============================================================================
# API Errors
# ============================================================================


class APIError(OrchestratorException):
    """Base exception for API-related errors"""

    pass


class AuthenticationError(APIError):
    """API authentication failed"""

    pass


class RateLimitError(APIError):
    """API rate limit exceeded"""

    def __init__(
        self,
        message: str,
        limit: int,
        retry_after: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        context = context or {}
        context.update({"limit": limit, "retry_after": retry_after})
        super().__init__(message, context=context)
        self.limit = limit
        self.retry_after = retry_after


class JobNotFoundError(APIError):
    """Requested job does not exist"""

    def __init__(self, message: str, job_id: str, context: Optional[Dict[str, Any]] = None):
        context = context or {}
        context.update({"job_id": job_id})
        super().__init__(message, context=context)
        self.job_id = job_id


# ============================================================================
# Task Errors
# ============================================================================


class TaskError(OrchestratorException):
    """Base exception for task-related errors"""

    pass


class TaskValidationError(TaskError):
    """Task parameters are invalid"""

    pass


class TaskDecompositionError(TaskError):
    """Failed to decompose task into subtasks"""

    pass


class TaskExecutionError(TaskError):
    """Task execution failed"""

    def __init__(
        self,
        message: str,
        task_name: str,
        worker_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        context = context or {}
        context.update({"task_name": task_name, "worker_id": worker_id})
        super().__init__(message, context=context)
        self.task_name = task_name
        self.worker_id = worker_id


# ============================================================================
# Resource Errors
# ============================================================================


class ResourceError(OrchestratorException):
    """Base exception for resource-related errors"""

    pass


class InsufficientResourcesError(ResourceError):
    """Not enough resources to complete operation"""

    def __init__(
        self,
        message: str,
        resource_type: str,
        required: Any,
        available: Any,
        context: Optional[Dict[str, Any]] = None,
    ):
        context = context or {}
        context.update(
            {"resource_type": resource_type, "required": required, "available": available}
        )
        super().__init__(message, context=context)
        self.resource_type = resource_type
        self.required = required
        self.available = available


class FileSystemError(ResourceError):
    """File system operation failed"""

    def __init__(
        self, message: str, path: str, operation: str, context: Optional[Dict[str, Any]] = None
    ):
        context = context or {}
        context.update({"path": path, "operation": operation})
        super().__init__(message, context=context)
        self.path = path
        self.operation = operation


# ============================================================================
# Retry Errors
# ============================================================================


class RetryableError(OrchestratorException):
    """
    Retryable error for transient failures

    Indicates that an operation failed but may succeed if retried
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize retryable error

        Args:
            message: Error message
            context: Additional context
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
            cause: Original exception
        """
        super().__init__(message, context=context, cause=cause)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_count = 0

    def can_retry(self) -> bool:
        """Check if retry is possible"""
        return self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """Increment retry counter"""
        self.retry_count += 1


# ============================================================================
# Legacy Aliases (for backward compatibility)
# ============================================================================

# Deprecated - use OrchestratorException instead
OrchestratorError = OrchestratorException

# Deprecated - use TaskDecompositionError instead
TaskSplitError = TaskDecompositionError

# Deprecated - use TaskValidationError instead
ValidationError = TaskValidationError

# Deprecated - use InvalidWorkspaceError instead
WorkspaceError = InvalidWorkspaceError

# Deprecated - use MissingDependencyError instead
GitBashError = MissingDependencyError

# Deprecated - use WorkerTimeoutError instead
TimeoutError = WorkerTimeoutError

# Deprecated - use FileSystemError instead
OutputError = FileSystemError

# Deprecated v4.2 exceptions (no longer used)
WindowManagerError = ResourceError
ScreenshotError = ResourceError


# ============================================================================
# Utility Functions
# ============================================================================


def wrap_exception(
    original: Exception,
    new_type: Type[OrchestratorException],
    message: str,
    context: Optional[Dict[str, Any]] = None,
) -> OrchestratorException:
    """
    Wrap an exception with additional context

    Args:
        original: Original exception
        new_type: New exception type
        message: New message
        context: Additional context

    Returns:
        New exception with wrapped original
    """
    return new_type(message, context=context, cause=original)


def format_exception_chain(exc: Exception) -> str:
    """
    Format exception chain for logging

    Args:
        exc: Exception to format

    Returns:
        Formatted string with full exception chain
    """
    lines = []
    current: Optional[BaseException] = exc

    while current is not None:
        lines.append(f"{type(current).__name__}: {str(current)}")

        if isinstance(current, OrchestratorException) and current.cause:
            current = current.cause
        elif current.__cause__:
            current = current.__cause__
        else:
            break

    return "\n  Caused by: ".join(lines)


# ============================================================================
# Exception Testing
# ============================================================================

if __name__ == "__main__":
    # Test exception creation and formatting

    print("Testing Custom Exceptions\n")
    print("=" * 70)

    # Test 1: Basic exception
    try:
        raise WorkerTimeoutError(
            "Worker exceeded timeout",
            worker_id="worker_1",
            timeout=300.0,
            context={"task_name": "Create API"},
        )
    except WorkerTimeoutError as e:
        print("\nTest 1: WorkerTimeoutError")
        print(f"  {e}")
        print(f"  Worker ID: {e.worker_id}")
        print(f"  Timeout: {e.timeout}")

    # Test 2: Wrapped exception
    try:
        try:
            raise ValueError("Invalid input")
        except ValueError as original:
            raise wrap_exception(
                original,
                ConfigurationError,
                "Configuration validation failed",
                context={"config_key": "max_workers"},
            )
    except ConfigurationError as e:
        print("\nTest 2: Wrapped Exception")
        print(f"  {e}")
        print(f"  Chain: {format_exception_chain(e)}")

    # Test 3: Dangerous operation
    try:
        raise DangerousOperationError(
            "Operation blocked by safety judge",
            operation_type="FILE_DELETE",
            details={"file": "/etc/passwd"},
            context={"worker_id": "worker_2"},
        )
    except DangerousOperationError as e:
        print("\nTest 3: DangerousOperationError")
        print(f"  {e}")
        print(f"  Operation: {e.operation_type}")
        print(f"  Details: {e.details}")

    print("\n" + "=" * 70)
    print("All exception tests completed successfully!")
