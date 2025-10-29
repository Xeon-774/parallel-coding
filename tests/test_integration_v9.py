"""
Comprehensive Integration Tests for v9.0

Tests all new world - class features:
- Structured logging
- Resilience patterns
- Observability system
- Validated configuration
- End - to - end workflows
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from orchestrator.core.observability import (
    HealthChecker,
    HealthStatus,
    MetricsCollector,
    ObservabilitySystem,
    PerformanceMonitor,
    ResourceMonitor,
)
from orchestrator.core.resilience import (
    Bulkhead,
    BulkheadConfig,
    BulkheadFullError,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    ResilientOperation,
    RetryConfig,
    RetryStrategy,
)

# Import v9.0 components
from orchestrator.core.structured_logging import LogCategory, LogContext, LogLevel, StructuredLogger
from orchestrator.core.validated_config import (
    ConfigurationPreset,
    OrchestratorValidatedConfig,
    ResilienceConfig,
    WorkerConfig,
    create_preset_config,
)


class TestStructuredLogging:
    """Test structured logging system"""

    def test_logger_initialization(self, tmp_path):
        """Test logger can be initialized"""
        with StructuredLogger(
            name="test_logger",
            level=LogLevel.DEBUG,
            log_dir=tmp_path,
            context=LogContext(session_id="test - session"),
        ) as logger:
            assert logger.name == "test_logger"
            assert logger.context.session_id == "test - session"

    def test_basic_logging(self, tmp_path):
        """Test basic log methods"""
        with StructuredLogger(name="test", log_dir=tmp_path, enable_console=False) as logger:
            # Should not raise
            logger.debug("Debug message", key="value")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

    def test_performance_logging(self, tmp_path):
        """Test performance logging"""
        with StructuredLogger(name="test", log_dir=tmp_path, enable_console=False) as logger:
            logger.log_performance("test_op", 0.123, True, task_id="task_1")

        # Check log file was created (after logger is closed)
        log_files = list(tmp_path.glob("*.jsonl"))
        assert len(log_files) > 0

    def test_operation_context_manager(self, tmp_path):
        """Test operation context manager"""
        with StructuredLogger(name="test", log_dir=tmp_path, enable_console=False) as logger:
            with logger.operation("test_operation", param="value"):
                time.sleep(0.01)

        # Should log start and performance (after logger is closed)
        log_files = list(tmp_path.glob("*.jsonl"))
        assert len(log_files) > 0

    def test_context_propagation(self, tmp_path):
        """Test context propagation"""
        with StructuredLogger(
            name="test", log_dir=tmp_path, context=LogContext(session_id="session - 123")
        ) as logger:
            worker_logger = logger.with_context(worker_id="worker - 1")

            assert worker_logger.context.session_id == "session - 123"
            assert worker_logger.context.worker_id == "worker - 1"

            # Close worker logger too
            worker_logger.close()


class TestResiliencePatterns:
    """Test resilience patterns"""

    def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after failures"""
        config = CircuitBreakerConfig(failure_threshold=3, timeout=1.0)
        breaker = CircuitBreaker(config)

        def failing_func():
            raise ValueError("Service down")

        # First 3 failures should pass through
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(failing_func)

        # Next call should be blocked
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(failing_func)

    def test_circuit_breaker_half_open(self):
        """Test circuit breaker half - open state"""
        config = CircuitBreakerConfig(failure_threshold=2, success_threshold=2, timeout=0.1)
        breaker = CircuitBreaker(config)

        # Open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        # Wait for timeout
        time.sleep(0.2)

        # Should allow one attempt (half - open)
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

    def test_retry_strategy_succeeds(self):
        """Test retry strategy eventual success"""
        config = RetryConfig(max_attempts=3, initial_delay=0.01)
        retry = RetryStrategy(config)

        attempts = [0]

        def intermittent_service():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = retry.execute(intermittent_service)
        assert result == "success"
        assert attempts[0] == 3

    def test_retry_strategy_exhausts(self):
        """Test retry strategy exhausts attempts"""
        config = RetryConfig(max_attempts=3, initial_delay=0.01)
        retry = RetryStrategy(config)

        def always_failing():
            raise ValueError("Permanent failure")

        with pytest.raises(ValueError):
            retry.execute(always_failing)

    def test_bulkhead_limits_concurrent(self):
        """Test bulkhead limits concurrent operations"""
        config = BulkheadConfig(max_concurrent=2, max_wait=0.1)
        bulkhead = Bulkhead(config)

        # Acquire 2 slots
        with bulkhead.acquire():
            with bulkhead.acquire():
                # Third should timeout
                with pytest.raises(BulkheadFullError):
                    with bulkhead.acquire(timeout=0.05):
                        pass

    def test_resilient_operation_combined(self):
        """Test combined resilience patterns"""
        resilient_op = ResilientOperation(
            name="test_op",
            circuit_breaker=CircuitBreaker(CircuitBreakerConfig(failure_threshold=5)),
            retry_strategy=RetryStrategy(RetryConfig(max_attempts=2, initial_delay=0.01)),
            bulkhead=Bulkhead(BulkheadConfig(max_concurrent=5)),
        )

        attempts = [0]

        def flaky_service():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ValueError("Flaky")
            return "ok"

        result = resilient_op.execute(flaky_service)
        assert result == "ok"
        assert attempts[0] == 2


class TestObservability:
    """Test observability system"""

    def test_metrics_collector(self):
        """Test metrics collection"""
        collector = MetricsCollector(retention_seconds=60)

        collector.record_counter("requests", value=1.0, labels={"endpoint": "/api"})
        collector.record_gauge("cpu_percent", value=45.5)
        collector.record_histogram("latency", value=0.123)

        metrics = collector.get_metrics()
        assert len(metrics) == 3

    def test_metrics_summary(self):
        """Test metrics summary statistics"""
        collector = MetricsCollector()

        # Record multiple values
        for i in range(10):
            collector.record_histogram("response_time", value=0.1 + i * 0.01)

        summary = collector.get_summary("response_time")
        assert summary["count"] == 10
        assert summary["min"] > 0
        assert summary["max"] > summary["min"]
        assert "mean" in summary
        assert "p95" in summary

    def test_performance_monitor(self):
        """Test performance monitoring"""
        collector = MetricsCollector()
        monitor = PerformanceMonitor(collector)

        monitor.track_operation("api_call", 0.125, True, labels={"endpoint": "/users"})
        monitor.track_operation("api_call", 0.150, True, labels={"endpoint": "/users"})

        stats = monitor.get_operation_stats("api_call")
        assert stats["count"] == 2
        assert "mean" in stats

    def test_resource_monitor(self):
        """Test resource monitoring"""
        collector = MetricsCollector()
        monitor = ResourceMonitor(collector)

        metrics = monitor.collect_metrics()
        assert metrics.cpu_percent >= 0
        assert metrics.memory_percent >= 0
        assert metrics.thread_count > 0

    def test_health_checker(self):
        """Test health checking"""
        checker = HealthChecker()

        checker.register_check("test_check", lambda: True)
        checker.register_check("failing_check", lambda: False)

        results = checker.run_checks()
        assert len(results) == 2
        assert results["test_check"].status == HealthStatus.HEALTHY
        assert results["failing_check"].status == HealthStatus.UNHEALTHY

        overall = checker.get_overall_health()
        assert overall == HealthStatus.UNHEALTHY  # One check is failing

    def test_observability_system_integration(self):
        """Test full observability system"""
        obs = ObservabilitySystem(retention_seconds=60)

        # Register health checks
        obs.health.register_check("always_healthy", lambda: True)

        # Record metrics
        obs.performance.track_operation("test_op", 0.1, True)

        # Get dashboard data
        dashboard = obs.get_dashboard_data()

        assert "health" in dashboard
        assert "resources" in dashboard
        assert "performance" in dashboard
        assert "timestamp" in dashboard

        obs.shutdown()


class TestValidatedConfiguration:
    """Test validated configuration"""

    def test_default_configuration(self):
        """Test default configuration is valid"""
        config = OrchestratorValidatedConfig()

        assert config.worker.max_workers == 4
        assert config.workspace_root.exists()

    def test_custom_configuration(self):
        """Test custom configuration"""
        config = OrchestratorValidatedConfig(
            worker=WorkerConfig(max_workers=8),
            resilience=ResilienceConfig(circuit_breaker_threshold=10),
        )

        assert config.worker.max_workers == 8
        assert config.resilience.circuit_breaker_threshold == 10

    def test_validation_errors(self):
        """Test validation catches errors"""
        with pytest.raises(Exception):  # ValidationError
            OrchestratorValidatedConfig(worker=WorkerConfig(max_workers=100))  # Exceeds max

    def test_configuration_presets(self):
        """Test configuration presets"""
        dev_config = create_preset_config(ConfigurationPreset.DEVELOPMENT)
        assert dev_config.worker.max_workers == 2
        assert dev_config.logging.level == LogLevel.DEBUG

        prod_config = create_preset_config(ConfigurationPreset.PRODUCTION)
        assert prod_config.worker.max_workers == 8
        assert prod_config.resilience.circuit_breaker_enabled is True

    def test_config_to_dict(self):
        """Test configuration export to dict"""
        config = OrchestratorValidatedConfig()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "worker" in config_dict
        assert "resilience" in config_dict
        assert "observability" in config_dict


class TestEndToEndWorkflow:
    """Test end - to - end workflows with v9.0 features"""

    def test_complete_workflow_with_all_features(self, tmp_path):
        """Test complete workflow using all v9.0 features"""
        # 1. Create validated configuration
        config = OrchestratorValidatedConfig(
            workspace_root=tmp_path,
            worker=WorkerConfig(max_workers=2),
            logging=LoggingConfig(log_dir=tmp_path / "logs"),
        )

        # 2. Initialize structured logging with context manager
        with StructuredLogger(
            name="integration_test", log_dir=config.logging.log_dir, level=config.logging.level
        ) as logger:
            # 3. Initialize observability
            obs = ObservabilitySystem()

            # 4. Create resilient operation
            resilient_op = ResilientOperation(
                name="test_workflow",
                circuit_breaker=CircuitBreaker(CircuitBreakerConfig()),
                retry_strategy=RetryStrategy(RetryConfig(max_attempts=2)),
                bulkhead=Bulkhead(BulkheadConfig()),
            )

            # 5. Execute operation with logging and monitoring
            attempts = [0]

            def workflow_task():
                attempts[0] += 1
                logger.info("Executing workflow task", attempt=attempts[0])

                # Simulate work
                time.sleep(0.01)

                if attempts[0] < 2:
                    raise ValueError("First attempt fails")

                return {"status": "success", "result": "completed"}

            # Execute with resilience
            with logger.operation("workflow_execution"):
                result = resilient_op.execute(workflow_task)

            # Track performance
            obs.performance.track_operation("workflow_task", 0.05, True)

            # Verify results
            assert result["status"] == "success"
            assert attempts[0] == 2  # Retried once

            # Check observability
            dashboard = obs.get_dashboard_data()
            assert dashboard is not None

            # Cleanup
            obs.shutdown()

    def test_configuration_and_logging_integration(self, tmp_path):
        """Test configuration and logging work together"""
        # Create config
        config = create_preset_config(ConfigurationPreset.DEVELOPMENT)
        config.workspace_root = tmp_path
        config.logging.log_dir = tmp_path / "logs"

        # Create logger from config with context manager
        with StructuredLogger(
            name="test",
            level=config.logging.level,
            log_dir=config.logging.log_dir,
            enable_console=config.logging.enable_console,
            enable_file=config.logging.enable_file,
        ) as logger:
            # Log messages
            logger.info("Test message", config_preset="development")

        # Verify log file created (after logger is closed)
        log_files = list(config.logging.log_dir.glob("*.jsonl"))
        assert len(log_files) > 0


# Import statement for LoggingConfig (missed earlier)
from orchestrator.core.validated_config import LoggingConfig


# Pytest fixtures
@pytest.fixture
def tmp_path():
    """Temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
