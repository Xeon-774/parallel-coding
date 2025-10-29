"""
Professional Structured Logging System (v9.0)

World - class logging infrastructure with:
- Structured JSON logging
- Multiple output handlers
- Log correlation and tracing
- Performance metrics integration
- Contextual logging with decorators
- Log sampling and filtering
- Asynchronous logging support
"""

import json
import logging
import threading
import time
import traceback
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Optional


class LogLevel(str, Enum):
    """Log levels matching Python logging levels"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(str, Enum):
    """Log categories for filtering and routing"""

    SYSTEM = "system"
    WORKER = "worker"
    TASK = "task"
    API = "api"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ORCHESTRATION = "orchestration"
    INTERACTIVE = "interactive"


@dataclass
class LogContext:
    """Context information for log entries"""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    worker_id: Optional[str] = None
    user_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, filtering None values"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class LogEntry:
    """Structured log entry"""

    timestamp: str
    level: LogLevel
    category: LogCategory
    message: str
    logger_name: str
    thread_name: str
    context: Dict[str, Any] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[Dict[str, Any]] = None
    performance: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        """Convert to JSON string"""
        data: Dict[str, Any] = {
            "timestamp": self.timestamp,
            "level": self.level.value,
            "category": self.category.value,
            "message": self.message,
            "logger": self.logger_name,
            "thread": self.thread_name,
        }

        if self.context:
            data["context"] = self.context

        if self.extra:
            data["extra"] = self.extra

        if self.exception:
            data["exception"] = self.exception

        if self.performance:
            data["performance"] = self.performance

        return json.dumps(data, ensure_ascii=False)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""

    def __init__(self, category: LogCategory = LogCategory.SYSTEM):
        super().__init__()
        self.category = category

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        # Extract context from record
        context = getattr(record, "context", {})
        extra = getattr(record, "extra", {})

        # Build log entry
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            level=LogLevel(record.levelname),
            category=getattr(record, "category", self.category),
            message=record.getMessage(),
            logger_name=record.name,
            thread_name=threading.current_thread().name,
            context=context,
            extra=extra,
        )

        # Add exception info if present
        if record.exc_info and record.exc_info[0]:
            entry.exception = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add performance metrics if present
        if hasattr(record, "performance"):
            entry.performance = record.performance

        return entry.to_json()


class ContextFilter(logging.Filter):
    """Filter to add context to log records"""

    def __init__(self, context: LogContext):
        super().__init__()
        self.context = context

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to record"""
        # Merge context into record
        if not hasattr(record, "context"):
            setattr(record, "context", {})

        getattr(record, "context").update(self.context.to_dict())
        return True


class StructuredLogger:
    """
    Professional structured logger with advanced features

    Features:
    - JSON structured logging
    - Context injection
    - Performance tracking
    - Multiple output handlers
    - Log sampling
    - Async logging support
    """

    def __init__(
        self,
        name: str,
        level: LogLevel = LogLevel.INFO,
        category: LogCategory = LogCategory.SYSTEM,
        log_dir: Optional[Path] = None,
        enable_console: bool = True,
        enable_file: bool = True,
        context: Optional[LogContext] = None,
    ):
        """
        Initialize structured logger

        Args:
            name: Logger name
            level: Minimum log level
            category: Default log category
            log_dir: Directory for log files
            enable_console: Enable console output
            enable_file: Enable file output
            context: Default log context
        """
        self.name = name
        self.category = category
        self.context = context or LogContext()

        # Create Python logger
        self.logger = logging.getLogger(name)
        # Handle both Enum and str level types
        level_name = level.value if hasattr(level, "value") else level
        self.logger.setLevel(getattr(logging, level_name))
        self.logger.propagate = False

        # Clear existing handlers
        self.logger.handlers.clear()

        # Add context filter
        self.logger.addFilter(ContextFilter(self.context))

        # Create formatter
        formatter = StructuredFormatter(category)

        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # File handler
        if enable_file and log_dir:
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)

            log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.jsonl"
            file_handler = logging.FileHandler(log_file, encoding="utf - 8")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _log(
        self,
        level: LogLevel,
        message: str,
        category: Optional[LogCategory] = None,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
        **kwargs: Any,
    ) -> None:
        """Internal logging method"""
        # Create log record
        record_kwargs: Dict[str, Any] = {
            "extra": {
                "category": category or self.category,
                "extra": extra or {},
                "context": kwargs,
            }
        }

        if exc_info:
            record_kwargs["exc_info"] = True

        # Log at appropriate level
        log_method = getattr(self.logger, level.value.lower())
        log_method(message, **record_kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message"""
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message"""
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message"""
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs: Any) -> None:
        """Log error message"""
        self._log(LogLevel.ERROR, message, exc_info=exc_info, **kwargs)

    def critical(self, message: str, exc_info: bool = False, **kwargs: Any) -> None:
        """Log critical message"""
        self._log(LogLevel.CRITICAL, message, exc_info=exc_info, **kwargs)

    def log_performance(
        self, operation: str, duration: float, success: bool, **kwargs: Any
    ) -> None:
        """Log performance metrics"""
        performance = {
            "operation": operation,
            "duration_ms": round(duration * 1000, 2),
            "success": success,
        }

        message = f"Performance: {operation} {'succeeded' if success else 'failed'} in {duration * 1000:.2f}ms"

        self._log(
            LogLevel.INFO, message, category=LogCategory.PERFORMANCE, extra=performance, **kwargs
        )

    def log_worker_spawn(self, worker_id: str, task_name: str, **kwargs: Any) -> None:
        """Log worker spawn event"""
        self._log(
            LogLevel.INFO,
            f"Worker spawned: {worker_id}",
            category=LogCategory.WORKER,
            extra={"task_name": task_name},
            worker_id=worker_id,
            **kwargs,
        )

    def log_worker_complete(
        self, worker_id: str, success: bool, duration: float, **kwargs: Any
    ) -> None:
        """Log worker completion"""
        self._log(
            LogLevel.INFO,
            f"Worker completed: {worker_id} ({'success' if success else 'failed'})",
            category=LogCategory.WORKER,
            extra={"duration": duration, "success": success},
            worker_id=worker_id,
            **kwargs,
        )

    def log_task_error(self, task_id: str, task_name: str, error: str, **kwargs: Any) -> None:
        """Log task error"""
        self._log(
            LogLevel.ERROR,
            f"Task failed: {task_name} - {error}",
            category=LogCategory.TASK,
            extra={"task_id": task_id, "task_name": task_name, "error": error},
            **kwargs,
        )

    def log_api_request(
        self, method: str, path: str, status_code: int, duration: float, **kwargs: Any
    ) -> None:
        """Log API request"""
        self._log(
            LogLevel.INFO,
            f"API {method} {path} -> {status_code}",
            category=LogCategory.API,
            extra={
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration * 1000, 2),
            },
            **kwargs,
        )

    def log_security_event(
        self, event_type: str, severity: str, details: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Log security event"""
        level = LogLevel.WARNING if severity == "medium" else LogLevel.ERROR

        self._log(
            level,
            f"Security event: {event_type}",
            category=LogCategory.SECURITY,
            extra={"event_type": event_type, "severity": severity, "details": details},
            **kwargs,
        )

    @contextmanager
    def operation(self, operation_name: str, **kwargs: Any) -> Generator[None, None, None]:
        """
        Context manager for logging operations with timing

        Usage:
            with logger.operation("process_data", data_size=1000):
                # do work
                pass
        """
        start_time = time.time()
        success = False

        self.debug(f"Starting operation: {operation_name}", **kwargs)

        try:
            yield
            success = True
        except Exception as e:
            self.error(f"Operation failed: {operation_name}", exc_info=True, error=str(e), **kwargs)
            raise
        finally:
            duration = time.time() - start_time
            self.log_performance(operation_name, duration, success, **kwargs)

    def with_context(self, **context_updates: Any) -> "StructuredLogger":
        """
        Create a new logger with updated context

        Args:
            **context_updates: Context fields to update

        Returns:
            New logger with updated context
        """
        new_context = LogContext(**{**asdict(self.context), **context_updates})

        new_logger = StructuredLogger(name=self.name, category=self.category, context=new_context)

        return new_logger

    def close(self) -> None:
        """
        Close all handlers and release file locks

        This is especially important on Windows to avoid file locking issues.
        Call this method when done with the logger, especially in tests.
        """
        for handler in self.logger.handlers[:]:  # Copy list to avoid modification during iteration
            handler.close()
            self.logger.removeHandler(handler)

    def __enter__(self) -> "StructuredLogger":
        """Support context manager protocol"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Close handlers when exiting context"""
        self.close()


def log_operation(
    logger: StructuredLogger, operation_name: Optional[str] = None, level: LogLevel = LogLevel.INFO
) -> Callable[..., Any]:
    """
    Decorator for logging function operations

    Args:
        logger: Logger instance
        operation_name: Custom operation name (default: function name)
        level: Log level for the operation

    Usage:
        @log_operation(logger, "process_task")
        def process_task(task_id):
            # do work
            pass
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            op_name = operation_name or func.__name__

            with logger.operation(op_name, function=func.__name__):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Global logger registry
_logger_registry: Dict[str, StructuredLogger] = {}


def get_logger(
    name: str,
    log_dir: Optional[Path] = None,
    enable_console: bool = True,
    enable_file: bool = True,
    console_level: LogLevel = LogLevel.INFO,
    file_level: LogLevel = LogLevel.DEBUG,
    category: LogCategory = LogCategory.SYSTEM,
) -> StructuredLogger:
    """
    Get or create a StructuredLogger instance (singleton pattern).

    Args:
        name: Logger name
        log_dir: Directory for log files
        enable_console: Enable console output
        enable_file: Enable file output
        console_level: Console log level
        file_level: File log level
        category: Default log category

    Returns:
        StructuredLogger instance
    """
    if name not in _logger_registry:
        _logger_registry[name] = StructuredLogger(
            name=name,
            level=console_level,
            category=category,
            log_dir=log_dir,
            enable_console=enable_console,
            enable_file=enable_file,
        )
    return _logger_registry[name]


# Example usage and testing
if __name__ == "__main__":
    # Create logger
    logger = StructuredLogger(
        name="orchestrator",
        level=LogLevel.DEBUG,
        category=LogCategory.SYSTEM,
        log_dir=Path("./logs"),
        context=LogContext(session_id="test - session - 123"),
    )

    print("Testing Structured Logger\n")
    print("=" * 70)

    # Test basic logging
    logger.info("Application started", version="9.0", environment="development")
    logger.debug("Debug information", debug_level=5)
    logger.warning("Potential issue detected", issue_type="memory_high")

    # Test worker logging
    logger.log_worker_spawn("worker_1", "Create API", workspace="/workspace / worker_1")

    # Test performance logging
    logger.log_performance("database_query", 0.125, True, query="SELECT * FROM users")

    # Test API logging
    logger.log_api_request("POST", "/api / v1 / jobs", 201, 0.035, user_id="user123")

    # Test security logging
    logger.log_security_event(
        "unauthorized_access_attempt",
        "high",
        {"ip": "192.168.1.100", "endpoint": "/admin"},
        user_id="anonymous",
    )

    # Test operation context manager
    with logger.operation("complex_operation", task_id="task_456"):
        time.sleep(0.1)
        logger.info("Step 1 completed")
        time.sleep(0.05)
        logger.info("Step 2 completed")

    # Test context propagation
    worker_logger = logger.with_context(worker_id="worker_2", task="build_ui")
    worker_logger.info("Worker processing task")

    # Test decorator
    @log_operation(logger, "test_function")
    def test_function(x: int, y: int) -> int:
        return x + y

    result = test_function(5, 3)

    # Test error logging
    try:
        raise ValueError("Test exception for logging")
    except ValueError:
        logger.error("Caught exception", exc_info=True, context="test")

    print("\n" + "=" * 70)
    print("Structured logging tests completed!")
    print("Check ./logs/ directory for JSON log files")
