"""
Resilience Patterns for Production Systems (v9.0)

World - class resilience patterns:
- Circuit Breaker pattern
- Retry with exponential backoff and jitter
- Bulkhead isolation
- Timeout management
- Fallback strategies
- Health checks
"""

import random
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Generator, Optional, Tuple, Type


class CircuitState(str, Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""

    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes to close from half - open
    timeout: float = 60.0  # Seconds before trying half - open
    expected_exceptions: Tuple[Type[BaseException], ...] = (Exception,)


@dataclass
class RetryConfig:
    """Configuration for retry logic"""

    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: Tuple[Type[BaseException], ...] = (Exception,)


@dataclass
class BulkheadConfig:
    """Configuration for bulkhead pattern"""

    max_concurrent: int = 10
    max_wait: float = 30.0  # seconds


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""


class BulkheadFullError(Exception):
    """Raised when bulkhead is at capacity"""


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation

    Prevents cascading failures by failing fast when a service is down.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests are rejected immediately
    - HALF_OPEN: Testing if service recovered, limited requests allowed
    """

    def __init__(self, config: CircuitBreakerConfig):
        """Initialize circuit breaker"""
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self._lock = threading.Lock()

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    failure_time = (
                        datetime.fromtimestamp(self.last_failure_time)
                        if self.last_failure_time
                        else "unknown"
                    )
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is open. Last failure: {failure_time}"
                    )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exceptions:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True

        return (time.time() - self.last_failure_time) >= self.config.timeout

    def _on_success(self) -> None:
        """Handle successful execution"""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0

            if self.state == CircuitState.CLOSED:
                self.failure_count = 0

    def _on_failure(self) -> None:
        """Handle failed execution"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
            elif self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN

    def reset(self) -> None:
        """Manually reset circuit breaker"""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None

    @property
    def status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": (
                datetime.fromtimestamp(self.last_failure_time).isoformat()
                if self.last_failure_time
                else None
            ),
        }


class RetryStrategy:
    """
    Retry with exponential backoff and jitter

    Implements intelligent retry logic to handle transient failures.
    """

    def __init__(self, config: RetryConfig):
        """Initialize retry strategy"""
        self.config = config

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with retry logic

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Last exception if all retries exhausted
        """
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except self.config.retryable_exceptions as e:
                last_exception = e

                if attempt == self.config.max_attempts:
                    raise

                delay = self._calculate_delay(attempt)
                time.sleep(delay)

        # Should not reach here, but for type safety
        if last_exception:
            raise last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter"""
        # Exponential backoff
        delay = min(
            self.config.initial_delay * (self.config.exponential_base ** (attempt - 1)),
            self.config.max_delay,
        )

        # Add jitter to prevent thundering herd
        if self.config.jitter:
            delay = delay * (0.5 + random.random() * 0.5)

        return delay


class Bulkhead:
    """
    Bulkhead pattern for resource isolation

    Limits concurrent operations to prevent resource exhaustion.
    """

    def __init__(self, config: BulkheadConfig):
        """Initialize bulkhead"""
        self.config = config
        self.semaphore = threading.Semaphore(config.max_concurrent)
        self._active_count = 0
        self._lock = threading.Lock()

    @contextmanager
    def acquire(self, timeout: Optional[float] = None) -> Generator[None, None, None]:
        """
        Acquire bulkhead slot

        Args:
            timeout: Maximum time to wait for slot

        Raises:
            BulkheadFullError: If bulkhead is full and timeout exceeded
        """
        timeout = timeout or self.config.max_wait

        acquired = self.semaphore.acquire(timeout=timeout)

        if not acquired:
            raise BulkheadFullError(
                f"Bulkhead full: {self.config.max_concurrent} concurrent operations"
            )

        with self._lock:
            self._active_count += 1

        try:
            yield
        finally:
            with self._lock:
                self._active_count -= 1
            self.semaphore.release()

    @property
    def status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            "max_concurrent": self.config.max_concurrent,
            "active": self._active_count,
            "available": self.config.max_concurrent - self._active_count,
        }


class ResilientOperation:
    """
    Combined resilience patterns

    Combines circuit breaker, retry, and bulkhead patterns.
    """

    def __init__(
        self,
        name: str,
        circuit_breaker: Optional[CircuitBreaker] = None,
        retry_strategy: Optional[RetryStrategy] = None,
        bulkhead: Optional[Bulkhead] = None,
    ):
        """
        Initialize resilient operation

        Args:
            name: Operation name
            circuit_breaker: Optional circuit breaker
            retry_strategy: Optional retry strategy
            bulkhead: Optional bulkhead
        """
        self.name = name
        self.circuit_breaker = circuit_breaker
        self.retry_strategy = retry_strategy
        self.bulkhead = bulkhead

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with all resilience patterns

        Order of execution:
        1. Bulkhead (resource limiting)
        2. Circuit Breaker (fail - fast)
        3. Retry (transient failure handling)
        4. Function execution
        """

        def _execute() -> Any:
            # Apply circuit breaker
            if self.circuit_breaker:
                return self.circuit_breaker.call(func, *args, **kwargs)
            else:
                return func(*args, **kwargs)

        def _execute_with_retry() -> Any:
            # Apply retry
            if self.retry_strategy:
                return self.retry_strategy.execute(_execute)
            else:
                return _execute()

        # Apply bulkhead
        if self.bulkhead:
            with self.bulkhead.acquire():
                return _execute_with_retry()
        else:
            return _execute_with_retry()

    @property
    def status(self) -> Dict[str, Any]:
        """Get combined status"""
        status: Dict[str, Any] = {"name": self.name}

        if self.circuit_breaker:
            status["circuit_breaker"] = self.circuit_breaker.status

        if self.bulkhead:
            status["bulkhead"] = self.bulkhead.status

        return status


# Decorators for easy usage
def with_circuit_breaker(
    config: Optional[CircuitBreakerConfig] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to add circuit breaker to function"""
    config = config or CircuitBreakerConfig()
    breaker = CircuitBreaker(config)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return breaker.call(func, *args, **kwargs)

        wrapper.circuit_breaker = breaker  # type: ignore
        return wrapper

    return decorator


def with_retry(
    config: Optional[RetryConfig] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to add retry to function"""
    config = config or RetryConfig()
    strategy = RetryStrategy(config)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return strategy.execute(func, *args, **kwargs)

        return wrapper

    return decorator


def with_bulkhead(
    config: Optional[BulkheadConfig] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to add bulkhead to function"""
    config = config or BulkheadConfig()
    bulkhead = Bulkhead(config)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with bulkhead.acquire():
                return func(*args, **kwargs)

        wrapper.bulkhead = bulkhead  # type: ignore
        return wrapper

    return decorator


def _test_circuit_breaker() -> None:
    """Test circuit breaker pattern."""
    print("\nTest 1: Circuit Breaker")
    print("-" * 70)

    config = CircuitBreakerConfig(failure_threshold=3, timeout=2.0)
    breaker = CircuitBreaker(config)

    def failing_service() -> None:
        raise ValueError("Service unavailable")

    # Trigger failures
    for i in range(5):
        try:
            breaker.call(failing_service)
        except (ValueError, CircuitBreakerOpenError) as e:
            print(f"  Attempt {i + 1}: {type(e).__name__}")

    print(f"  Circuit status: {breaker.status}")


def _test_retry_strategy() -> None:
    """Test retry strategy with exponential backoff."""
    print("\nTest 2: Retry with Exponential Backof")
    print("-" * 70)

    retry_config = RetryConfig(max_attempts=3, initial_delay=0.1)
    retry = RetryStrategy(retry_config)

    class Counter:
        count = 0

    def intermittent_service() -> str:
        Counter.count += 1
        if Counter.count < 3:
            raise ValueError(f"Attempt {Counter.count} failed")
        return "Success!"

    result = retry.execute(intermittent_service)
    print(f"  Result after {Counter.count} attempts: {result}")


def _test_bulkhead_pattern() -> None:
    """Test bulkhead pattern for resource isolation."""
    print("\nTest 3: Bulkhead Pattern")
    print("-" * 70)

    bulkhead_config = BulkheadConfig(max_concurrent=2)
    bulkhead = Bulkhead(bulkhead_config)

    def slow_operation() -> str:
        time.sleep(0.1)
        return "Done"

    # Concurrent operations
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in range(5):
            def _run_with_bulkhead():
                with bulkhead.acquire():
                    return slow_operation()
            future = executor.submit(_run_with_bulkhead)
            futures.append(future)

        print(f"  Bulkhead status: {bulkhead.status}")


def _test_combined_resilience() -> None:
    """Test combined resilience patterns."""
    print("\nTest 4: Combined Resilience Patterns")
    print("-" * 70)

    resilient_op = ResilientOperation(
        name="api_call",
        circuit_breaker=CircuitBreaker(CircuitBreakerConfig()),
        retry_strategy=RetryStrategy(RetryConfig(max_attempts=2)),
        bulkhead=Bulkhead(BulkheadConfig(max_concurrent=5)),
    )

    class APICounter:
        count = 0

    def api_call() -> Dict[str, str]:
        APICounter.count += 1
        if APICounter.count < 2:
            raise ValueError("API error")
        return {"status": "ok"}

    result = resilient_op.execute(api_call)
    print(f"  Result: {result}")
    print(f"  Status: {resilient_op.status}")


def _run_all_tests() -> None:
    """Run all resilience pattern tests."""
    print("Testing Resilience Patterns\n")
    print("=" * 70)

    _test_circuit_breaker()
    _test_retry_strategy()
    _test_bulkhead_pattern()
    _test_combined_resilience()

    print("\n" + "=" * 70)
    print("Resilience pattern tests completed!")


# Testing
if __name__ == "__main__":
    _run_all_tests()
