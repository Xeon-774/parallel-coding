"""
Metrics API Endpoints

Provides access to worker performance metrics for visualization.
Phase 2.2 implementation.
"""

from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from orchestrator.config import DEFAULT_CONFIG
from orchestrator.core.common.metrics import MetricsCollector

router = APIRouter(prefix="/api / v1", tags=["metrics"])

# Initialize metrics collector using default config
metrics_collector = MetricsCollector(workspace_root=Path(DEFAULT_CONFIG.workspace_root))


@router.get("/workers/{worker_id}/metrics")
async def get_worker_metrics(worker_id: str) -> Dict[str, Any]:
    """
    Get all metrics for a worker.

    Returns:
        {
            "worker_id": str,
            "metrics": [...],
            "count": int
        }
    """
    metrics = metrics_collector.get_metrics(worker_id)

    return {"worker_id": worker_id, "metrics": metrics, "count": len(metrics)}


@router.get("/workers/{worker_id}/metrics / summary")
async def get_worker_metrics_summary(worker_id: str) -> Dict[str, Any]:
    """
    Get aggregated metrics summary for a worker.

    Returns:
        {
            "worker_id": str,
            "total_metrics": int,
            "confirmations": {...},
            "output": {...},
            "execution": {...}
        }
    """
    summary = metrics_collector.get_metrics_summary(worker_id)
    return summary


@router.get("/metrics / current")
async def get_current_hybrid_metrics() -> Dict[str, Any]:
    """
    Get current hybrid engine metrics aggregated across all workers.

    This endpoint is used by the MetricsDashboard component to display
    real - time decision statistics.

    Returns:
        {
            "total_decisions": int,
            "rules_decisions": int,
            "ai_decisions": int,
            "template_fallbacks": int,
            "average_latency_ms": float,
            "rules_percentage": float
        }
    """
    workspace = Path(DEFAULT_CONFIG.workspace_root)

    # Aggregate metrics from all workers
    all_metrics = []
    if workspace.exists():
        for worker_dir in workspace.iterdir():
            if worker_dir.is_dir() and worker_dir.name.startswith("worker_"):
                try:
                    metrics = metrics_collector.get_metrics(worker_dir.name)
                    all_metrics.extend(metrics)
                except Exception as e:
                    # Log and continue if one worker fails
                    print(f"Warning: Failed to get metrics for {worker_dir.name}: {e}")

    # Initialize counters
    total_decisions = 0
    rules_decisions = 0
    ai_decisions = 0
    template_fallbacks = 0
    all_latencies = []

    # Process all confirmation metrics
    for metric in all_metrics:
        if metric.get("type") == "confirmation":
            total_decisions += 1

            decided_by = metric.get("decided_by", "unknown")
            if decided_by == "rules":
                rules_decisions += 1
            elif decided_by == "ai":
                ai_decisions += 1
            elif decided_by == "template":
                template_fallbacks += 1

            # Collect latency if available
            if "latency_ms" in metric:
                all_latencies.append(metric["latency_ms"])

    # Calculate average latency
    average_latency_ms = sum(all_latencies) / len(all_latencies) if all_latencies else 0.0

    # Calculate rules percentage
    rules_percentage = (rules_decisions / total_decisions * 100) if total_decisions > 0 else 0.0

    return {
        "total_decisions": total_decisions,
        "rules_decisions": rules_decisions,
        "ai_decisions": ai_decisions,
        "template_fallbacks": template_fallbacks,
        "average_latency_ms": round(average_latency_ms, 2),
        "rules_percentage": round(rules_percentage, 2),
    }


@router.get("/decisions / recent")
async def get_recent_decisions(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get recent decision events from all workers.

    This endpoint returns the latest confirmation decisions sorted by timestamp
    for display in the MetricsDashboard decision history table.

    Args:
        limit: Maximum number of decisions to return (default: 100)

    Returns:
        List of decision events, each containing:
        {
            "timestamp": float,
            "worker_id": str,
            "decision_type": str,
            "decided_by": str,
            "latency_ms": float,
            "is_fallback": bool,
            "confirmation_type": str,
            "reasoning": str
        }
    """
    workspace = Path(DEFAULT_CONFIG.workspace_root)

    # Collect all confirmation metrics from all workers
    decisions = []
    if workspace.exists():
        for worker_dir in workspace.iterdir():
            if worker_dir.is_dir() and worker_dir.name.startswith("worker_"):
                try:
                    metrics = metrics_collector.get_metrics(worker_dir.name)

                    for metric in metrics:
                        if metric.get("type") == "confirmation":
                            decisions.append(
                                {
                                    "timestamp": metric.get("timestamp", 0),
                                    "worker_id": worker_dir.name,
                                    "decision_type": metric.get("decision", "unknown"),
                                    "decided_by": metric.get("decided_by", "unknown"),
                                    "latency_ms": metric.get("latency_ms", 0),
                                    "is_fallback": metric.get("is_fallback", False),
                                    "confirmation_type": metric.get("confirmation_type", ""),
                                    "reasoning": metric.get("reasoning", ""),
                                }
                            )
                except Exception as e:
                    # Log and continue if one worker fails
                    print(f"Warning: Failed to get decisions for {worker_dir.name}: {e}")

    # Sort by timestamp (descending - most recent first)
    decisions.sort(key=lambda x: x["timestamp"], reverse=True)

    # Return only the requested number
    return decisions[:limit]
