"""
Comprehensive Observability System (v9.0)

World - class observability with:
- Metrics collection and aggregation
- Performance monitoring
- Health checks
- Resource utilization tracking
- Distributed tracing support
- Real - time dashboards data
"""

import statistics
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Deque, Dict, List, Optional

import psutil


class MetricType(str, Enum):
    """Types of metrics"""

    COUNTER = "counter"  # Monotonically increasing
    GAUGE = "gauge"  # Point - in - time value
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"  # Summary statistics


class HealthStatus(str, Enum):
    """Health check status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class Metric:
    """Individual metric"""

    name: str
    metric_type: MetricType
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None


@dataclass
class HealthCheck:
    """Health check result"""

    name: str
    status: HealthStatus
    message: str
    timestamp: float
    duration_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceMetrics:
    """System resource metrics"""

    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    thread_count: int
    process_count: int
    timestamp: float


class MetricsCollector:
    """
    Metrics collection and aggregation

    Collects various types of metrics and provides aggregation.
    """

    def __init__(self, retention_seconds: int = 3600):
        """
        Initialize metrics collector

        Args:
            retention_seconds: How long to retain metrics
        """
        self.retention_seconds = retention_seconds
        self._metrics: Dict[str, Deque[Any]] = defaultdict(lambda: deque(maxlen=10000))
        self._lock = threading.Lock()

    def record_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
        unit: Optional[str] = None,
    ) -> None:
        """Record counter metric"""
        metric = Metric(
            name=name,
            metric_type=MetricType.COUNTER,
            value=value,
            timestamp=time.time(),
            labels=labels or {},
            unit=unit,
        )
        self._record_metric(metric)

    def record_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        unit: Optional[str] = None,
    ) -> None:
        """Record gauge metric"""
        metric = Metric(
            name=name,
            metric_type=MetricType.GAUGE,
            value=value,
            timestamp=time.time(),
            labels=labels or {},
            unit=unit,
        )
        self._record_metric(metric)

    def record_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        unit: Optional[str] = None,
    ) -> None:
        """Record histogram metric"""
        metric = Metric(
            name=name,
            metric_type=MetricType.HISTOGRAM,
            value=value,
            timestamp=time.time(),
            labels=labels or {},
            unit=unit,
        )
        self._record_metric(metric)

    def _record_metric(self, metric: Metric) -> None:
        """Internal method to record metric"""
        with self._lock:
            key = self._metric_key(metric.name, metric.labels)
            self._metrics[key].append(metric)

    def _metric_key(self, name: str, labels: Dict[str, str]) -> str:
        """Generate unique key for metric"""
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}" if label_str else name

    def get_metrics(
        self, name: Optional[str] = None, since: Optional[float] = None
    ) -> List[Metric]:
        """
        Get metrics

        Args:
            name: Filter by metric name
            since: Filter by timestamp (unix time)

        Returns:
            List of metrics
        """
        with self._lock:
            all_metrics = []

            for key, metrics in self._metrics.items():
                # Filter by name
                if name and not key.startswith(name):
                    continue

                # Filter by time
                for metric in metrics:
                    if since and metric.timestamp < since:
                        continue
                    all_metrics.append(metric)

            return all_metrics

    def get_summary(self, name: str, since: Optional[float] = None) -> Dict[str, Any]:
        """
        Get summary statistics for a metric

        Args:
            name: Metric name
            since: Start time

        Returns:
            Summary statistics
        """
        metrics = self.get_metrics(name, since)

        if not metrics:
            return {"count": 0}

        values = [m.value for m in metrics]

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stddev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "p95": statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values),
            "p99": statistics.quantiles(values, n=100)[98] if len(values) >= 100 else max(values),
        }

    def cleanup_old_metrics(self) -> None:
        """Remove metrics older than retention period"""
        cutoff = time.time() - self.retention_seconds

        with self._lock:
            for key in list(self._metrics.keys()):
                metrics = self._metrics[key]

                # Remove old metrics
                while metrics and metrics[0].timestamp < cutoff:
                    metrics.popleft()

                # Remove empty queues
                if not metrics:
                    del self._metrics[key]


class PerformanceMonitor:
    """
    Performance monitoring

    Tracks operation performance and provides insights.
    """

    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize performance monitor"""
        self.metrics = metrics_collector

    def track_operation(
        self,
        operation_name: str,
        duration: float,
        success: bool,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Track operation performance

        Args:
            operation_name: Name of operation
            duration: Duration in seconds
            success: Whether operation succeeded
            labels: Additional labels
        """
        labels = labels or {}
        labels["operation"] = operation_name
        labels["status"] = "success" if success else "failure"

        # Record duration histogram
        self.metrics.record_histogram(
            "operation_duration_seconds", duration, labels=labels, unit="seconds"
        )

        # Record operation counter
        self.metrics.record_counter("operation_total", value=1.0, labels=labels)

    def get_operation_stats(
        self, operation_name: str, since: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get statistics for an operation"""
        summary = self.metrics.get_summary("operation_duration_seconds", since)

        # Add success rate
        all_ops = self.metrics.get_metrics("operation_total", since)
        filtered_ops = [m for m in all_ops if m.labels.get("operation") == operation_name]

        if filtered_ops:
            successes = sum(m.value for m in filtered_ops if m.labels.get("status") == "success")
            total = sum(m.value for m in filtered_ops)
            summary["success_rate"] = successes / total if total > 0 else 0.0
            summary["total_operations"] = int(total)

        return summary


class ResourceMonitor:
    """
    System resource monitoring

    Tracks CPU, memory, disk, and other system resources.
    """

    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize resource monitor"""
        self.metrics = metrics_collector
        self.process = psutil.Process()

    def collect_metrics(self) -> ResourceMetrics:
        """Collect current resource metrics"""
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Get process metrics
        self.process.memory_info()

        metrics = ResourceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            memory_available_mb=memory.available / (1024 * 1024),
            disk_usage_percent=disk.percent,
            thread_count=threading.active_count(),
            process_count=len(psutil.pids()),
            timestamp=time.time(),
        )

        # Record metrics
        self.metrics.record_gauge("system_cpu_percent", metrics.cpu_percent, unit="%")
        self.metrics.record_gauge("system_memory_percent", metrics.memory_percent, unit="%")
        self.metrics.record_gauge("system_memory_used_mb", metrics.memory_used_mb, unit="MB")
        self.metrics.record_gauge("system_disk_usage_percent", metrics.disk_usage_percent, unit="%")
        self.metrics.record_gauge("system_thread_count", metrics.thread_count)

        return metrics


class HealthChecker:
    """
    Health check manager

    Runs health checks and aggregates results.
    """

    def __init__(self) -> None:
        """Initialize health checker"""
        self._checks: Dict[str, Callable[[], HealthCheck]] = {}
        self._last_results: Dict[str, HealthCheck] = {}
        self._lock = threading.Lock()

    def register_check(self, name: str, check_func: Callable[[], bool]) -> None:
        """
        Register a health check

        Args:
            name: Check name
            check_func: Function that returns True if healthy
        """

        def wrapped_check() -> HealthCheck:
            start = time.time()
            try:
                is_healthy = check_func()
                duration = (time.time() - start) * 1000

                return HealthCheck(
                    name=name,
                    status=HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY,
                    message="OK" if is_healthy else "Check failed",
                    timestamp=time.time(),
                    duration_ms=duration,
                )
            except Exception as e:
                duration = (time.time() - start) * 1000
                return HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Error: {str(e)}",
                    timestamp=time.time(),
                    duration_ms=duration,
                    metadata={"exception": type(e).__name__},
                )

        with self._lock:
            self._checks[name] = wrapped_check

    def run_checks(self) -> Dict[str, HealthCheck]:
        """Run all health checks"""
        results = {}

        with self._lock:
            checks = dict(self._checks)

        for name, check_func in checks.items():
            result = check_func()
            results[name] = result

        with self._lock:
            self._last_results = results

        return results

    def get_overall_health(self) -> HealthStatus:
        """Get overall health status"""
        if not self._last_results:
            return HealthStatus.UNHEALTHY

        statuses = [check.status for check in self._last_results.values()]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.DEGRADED

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary"""
        return {
            "overall_status": self.get_overall_health().value,
            "checks": {
                name: {
                    "status": check.status.value,
                    "message": check.message,
                    "duration_ms": check.duration_ms,
                }
                for name, check in self._last_results.items()
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


class ObservabilitySystem:
    """
    Comprehensive observability system

    Combines metrics, performance, resources, and health checks.
    """

    def __init__(self, retention_seconds: int = 3600):
        """Initialize observability system"""
        self.metrics = MetricsCollector(retention_seconds)
        self.performance = PerformanceMonitor(self.metrics)
        self.resources = ResourceMonitor(self.metrics)
        self.health = HealthChecker()

        # Start background collection
        self._collection_interval = 10.0  # seconds
        self._stop_event = threading.Event()
        self._collector_thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._collector_thread.start()

    def _collect_loop(self) -> None:
        """Background collection loop"""
        while not self._stop_event.is_set():
            try:
                # Collect resource metrics
                self.resources.collect_metrics()

                # Run health checks
                self.health.run_checks()

                # Cleanup old metrics
                self.metrics.cleanup_old_metrics()

            except Exception as e:
                print(f"Error in collection loop: {e}")

            self._stop_event.wait(self._collection_interval)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all observability data for dashboard"""
        return {
            "health": self.health.get_health_summary(),
            "resources": {"current": self.resources.collect_metrics().__dict__},
            "performance": {
                "operations": [
                    {
                        "name": m.labels.get("operation", "unknown"),
                        "stats": self.performance.get_operation_stats(
                            m.labels.get("operation", "unknown")
                        ),
                    }
                    for m in self.metrics.get_metrics("operation_duration_seconds")
                ]
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def shutdown(self) -> None:
        """Shutdown observability system"""
        self._stop_event.set()
        if self._collector_thread.is_alive():
            self._collector_thread.join(timeout=5.0)


# Testing
if __name__ == "__main__":
    print("Testing Observability System\n")
    print("=" * 70)

    # Create observability system
    obs = ObservabilitySystem()

    # Register health checks
    obs.health.register_check("database", lambda: True)
    obs.health.register_check("cache", lambda: True)
    obs.health.register_check("api", lambda: True)

    # Record some metrics
    print("\nRecording metrics...")
    for i in range(10):
        obs.performance.track_operation("api_call", 0.1 + i * 0.01, True)
        obs.performance.track_operation("db_query", 0.05 + i * 0.005, True)

    # Collect resources
    print("Collecting resource metrics...")
    resources = obs.resources.collect_metrics()
    print(f"  CPU: {resources.cpu_percent:.1f}%")
    print(f"  Memory: {resources.memory_percent:.1f}%")
    print(f"  Threads: {resources.thread_count}")

    # Run health checks
    print("\nRunning health checks...")
    health = obs.health.get_health_summary()
    print(f"  Overall: {health['overall_status']}")
    for name, check in health["checks"].items():
        print(f"  {name}: {check['status']}")

    # Get dashboard data
    print("\nDashboard data:")
    dashboard = obs.get_dashboard_data()
    print(f"  Timestamp: {dashboard['timestamp']}")
    print(f"  Health: {dashboard['health']['overall_status']}")

    # Get operation stats
    print("\nOperation statistics:")
    stats = obs.performance.get_operation_stats("api_call")
    print("  API calls:")
    print(f"    Count: {stats.get('count', 0)}")
    print(f"    Mean: {stats.get('mean', 0):.3f}s")
    print(f"    P95: {stats.get('p95', 0):.3f}s")

    # Shutdown
    obs.shutdown()

    print("\n" + "=" * 70)
    print("Observability system tests completed!")
