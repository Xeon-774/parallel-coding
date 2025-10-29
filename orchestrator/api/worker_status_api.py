"""
Worker Status REST and WebSocket API

Provides endpoints for monitoring worker execution status in real - time.
Milestone 1.3: Worker Status UI implementation.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from orchestrator.core.worker_status_monitor import (
    WorkerStatusMonitor,
    get_global_monitor,
)

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api / v1 / status", tags=["worker - status"])

# Global workspace root (will be initialized from main.py)
_workspace_root: Optional[Path] = None


def init_worker_status_api(workspace_root: Path) -> None:
    """Initialize worker status API with workspace root."""
    global _workspace_root
    _workspace_root = workspace_root
    get_global_monitor(workspace_root)
    logger.info(f"Worker status API initialized with workspace: {workspace_root}")


def _get_monitor() -> WorkerStatusMonitor:
    """Get global status monitor instance"""
    if _workspace_root is None:
        raise RuntimeError("Worker status API not initialized")
    return get_global_monitor(_workspace_root)


@router.get("/workers")
async def list_worker_statuses():
    """Get status for all registered workers."""
    try:
        monitor = _get_monitor()
        statuses = monitor.get_all_statuses()
        return {
            "workers": [status.to_dict() for status in statuses],
            "count": len(statuses),
        }
    except Exception as e:
        logger.error(f"Error listing worker statuses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workers/{worker_id}")
async def get_worker_status(worker_id: str):
    """Get detailed status for a specific worker."""
    try:
        monitor = _get_monitor()
        status = monitor.get_worker_status(worker_id)
        if status is None:
            raise HTTPException(status_code=404, detail=f"Worker {worker_id} not found")
        return status.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting worker status for {worker_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_status_summary():
    """Get aggregated summary of all workers."""
    try:
        monitor = _get_monitor()
        return monitor.get_summary()
    except Exception as e:
        logger.error(f"Error getting status summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{worker_id}")
async def worker_status_websocket(websocket: WebSocket, worker_id: str):
    """WebSocket endpoint for real - time worker status streaming."""
    await websocket.accept()
    logger.info(f"New status WebSocket connection for worker {worker_id}")

    try:
        monitor = _get_monitor()
        status = monitor.get_worker_status(worker_id)
        if not status:
            await websocket.send_json({"type": "error", "message": f"Worker {worker_id} not found"})
            await websocket.close()
            return

        await websocket.send_json({"type": "status", "data": status.to_dict()})

        while True:
            await asyncio.sleep(0.5)
            status = monitor.get_worker_status(worker_id)
            if status:
                await websocket.send_json({"type": "status", "data": status.to_dict()})
                if status.is_terminal:
                    break
            else:
                break
    except WebSocketDisconnect:
        logger.info(f"Status WebSocket disconnected: {worker_id}")
    except Exception as e:
        logger.error(f"Status WebSocket error for {worker_id}: {e}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@router.get("/health")
async def status_api_health():
    """Health check for status API."""
    return {
        "status": "healthy",
        "monitor_initialized": _workspace_root is not None,
        "workspace_root": str(_workspace_root) if _workspace_root else None,
    }
