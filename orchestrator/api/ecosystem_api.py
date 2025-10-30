"""
Ecosystem Dashboard API

Provides aggregate endpoints for the entire development ecosystem.

Features:
- System - wide health status
- Aggregate performance metrics
- Real - time activity feed via WebSocket
- Cross - app statistics

Created: 2025 - 10 - 24
Part of: Phase 2 Backend Integration
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api / v1 / ecosystem",
    tags=["ecosystem"],
)

# Global state for activity broadcasting
activity_connections: List[WebSocket] = []


class ActivityBroadcaster:
    """Manages WebSocket connections for activity broadcasting"""

    def __init__(self) -> None:
        self.connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Add a new WebSocket connection"""
        await websocket.accept()
        self.connections.append(websocket)
        logger.info(f"Activity feed connection added. Total: {len(self.connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection"""
        if websocket in self.connections:
            self.connections.remove(websocket)
            logger.info(f"Activity feed connection removed. Total: {len(self.connections)}")

    async def broadcast(self, activity: Dict[str, Any]) -> None:
        """Broadcast activity to all connected clients"""
        disconnected = []
        for connection in self.connections:
            try:
                await connection.send_json(activity)
            except Exception as e:
                logger.error(f"Failed to send to connection: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


# Global broadcaster instance
activity_broadcaster = ActivityBroadcaster()


@router.get("/health")
async def get_ecosystem_health() -> Dict[str, Any]:
    """
    Get comprehensive health status for the entire ecosystem.

    Returns:
        {
            "status": "healthy" | "degraded" | "unhealthy",
            "timestamp": float,
            "apps": {
                "parallel_coding": {
                    "status": "active",
                    "workers_count": int,
                    "uptime": str,
                    "version": str
                },
                "manager_ai": {
                    "status": "coming_soon"
                },
                "mt4_integration": {
                    "status": "coming_soon"
                }
            },
            "system": {
                "cpu_usage": float,
                "memory_usage": float,
                "disk_usage": float
            }
        }
    """
    try:
        # Get worker count from workspace
        workspace_root = Path(__file__).parent.parent.parent / "workspace"
        worker_count = 0
        if workspace_root.exists():
            worker_count = sum(
                1 for d in workspace_root.iterdir() if d.is_dir() and d.name.startswith("worker_")
            )

        # Calculate uptime (mock for now, should track actual start time)
        uptime = "24h"  # TODO: Track actual uptime

        return {
            "status": "healthy",
            "timestamp": time.time(),
            "apps": {
                "parallel_coding": {
                    "status": "active",
                    "workers_count": worker_count,
                    "uptime": uptime,
                    "version": "1.0.0",
                },
                "manager_ai": {"status": "coming_soon", "version": "N / A"},
                "mt4_integration": {"status": "coming_soon", "version": "N / A"},
                "trading_dashboard": {"status": "coming_soon", "version": "N / A"},
            },
            "system": {
                "cpu_usage": 0.0,  # TODO: Get real CPU usage
                "memory_usage": 0.0,  # TODO: Get real memory usage
                "disk_usage": 0.0,  # TODO: Get real disk usage
            },
        }
    except Exception as e:
        logger.error(f"Error getting ecosystem health: {e}")
        return JSONResponse(  # type: ignore[return - value]
            status_code=500,
            content={"status": "unhealthy", "error": str(e), "timestamp": time.time()},
        )


@router.get("/metrics / summary")
async def get_metrics_summary() -> Dict[str, Any]:
    """
    Get aggregate performance metrics across all apps.

    Returns:
        {
            "timestamp": float,
            "period": "24h",
            "cpu": {
                "average": float,
                "peak": float,
                "current": float
            },
            "memory": {
                "average": float,
                "peak": float,
                "current": float
            },
            "api_calls": {
                "total": int,
                "per_minute": float,
                "errors": int
            },
            "workers": {
                "total": int,
                "active": int,
                "idle": int,
                "failed": int
            }
        }
    """
    try:
        # Mock data for now - in production, this would aggregate from all apps
        import random

        return {
            "timestamp": time.time(),
            "period": "24h",
            "cpu": {
                "average": round(random.uniform(20, 40), 1),
                "peak": round(random.uniform(60, 80), 1),
                "current": round(random.uniform(15, 35), 1),
            },
            "memory": {
                "average": round(random.uniform(40, 60), 1),
                "peak": round(random.uniform(70, 85), 1),
                "current": round(random.uniform(45, 65), 1),
            },
            "api_calls": {
                "total": random.randint(500, 1000),
                "per_minute": round(random.uniform(5, 15), 2),
                "errors": random.randint(0, 5),
            },
            "workers": {"total": 0, "active": 0, "idle": 0, "failed": 0},
        }
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        return JSONResponse(status_code=500, content={"error": str(e), "timestamp": time.time()})  # type: ignore[return - value]


@router.websocket("/activity")
async def websocket_activity_feed(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real - time activity feed.

    Streams activities from all ecosystem apps in real - time.

    Message Format:
        {
            "id": str,
            "timestamp": str (ISO format),
            "app": "parallel_coding" | "manager_ai" | "mt4" | "trading",
            "message": str,
            "type": "info" | "success" | "warning" | "error",
            "details": dict (optional)
        }

    Example:
        ```javascript
        const ws = new WebSocket('ws://localhost:8001 / api / v1 / ecosystem / activity');
        ws.onmessage = (event) => {
            const activity = JSON.parse(event.data);
            console.log(activity.app, activity.message);
        };
        ```
    """
    await activity_broadcaster.connect(websocket)

    try:
        # Send initial welcome message
        await websocket.send_json(
            {
                "id": "system_connected",
                "timestamp": datetime.now().isoformat(),
                "app": "ecosystem",
                "message": "Connected to activity feed",
                "type": "info",
            }
        )

        # Send some initial mock activities
        initial_activities = [
            {
                "id": "1",
                "timestamp": datetime.now().isoformat(),
                "app": "parallel_coding",
                "message": "System initialized successfully",
                "type": "success",
            },
            {
                "id": "2",
                "timestamp": datetime.now().isoformat(),
                "app": "ecosystem",
                "message": "Ecosystem Dashboard online",
                "type": "success",
            },
            {
                "id": "3",
                "timestamp": datetime.now().isoformat(),
                "app": "parallel_coding",
                "message": "Module Federation configured",
                "type": "success",
            },
        ]

        for activity in initial_activities:
            await websocket.send_json(activity)

        # Keep connection alive and listen for messages
        while True:
            # Wait for any message from client (ping, etc.)
            data = await websocket.receive_text()
            logger.debug(f"Received from client: {data}")

            # Echo back as acknowledgment
            if data == "ping":
                await websocket.send_json(
                    {
                        "id": "pong",
                        "timestamp": datetime.now().isoformat(),
                        "app": "ecosystem",
                        "message": "pong",
                        "type": "info",
                    }
                )

    except WebSocketDisconnect:
        activity_broadcaster.disconnect(websocket)
        logger.info("Activity feed WebSocket disconnected")
    except Exception as e:
        logger.error(f"Activity feed WebSocket error: {e}")
        activity_broadcaster.disconnect(websocket)
        raise


async def broadcast_activity(
    app: str, message: str, activity_type: str = "info", details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Broadcast an activity to all connected clients.

    Args:
        app: Source app name
        message: Activity message
        activity_type: Activity type (info, success, warning, error)
        details: Optional additional details
    """
    activity = {
        "id": f"{app}_{int(time.time() * 1000)}",
        "timestamp": datetime.now().isoformat(),
        "app": app,
        "message": message,
        "type": activity_type,
    }

    if details:
        activity["details"] = details  # type: ignore[assignment]

    await activity_broadcaster.broadcast(activity)
    logger.info(f"Broadcast activity: {app} - {message}")


# Health check for ecosystem API
@router.get("/status")
async def get_ecosystem_status() -> Dict[str, Any]:
    """
    Get basic status of ecosystem API.

    Returns:
        {
            "status": "online",
            "active_connections": int,
            "version": str
        }
    """
    return {
        "status": "online",
        "active_connections": len(activity_broadcaster.connections),
        "version": "1.0.0",
        "timestamp": time.time(),
    }
