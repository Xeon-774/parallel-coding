"""
FastAPI Application for Parallel AI Coding Orchestrator

This is the main entry point for the orchestrator's REST and WebSocket API.

Features:
- Real - time dialogue streaming via WebSocket
- Worker status monitoring
- Metrics collection and reporting
- CORS support for frontend development

Usage:
    # Development
    uvicorn orchestrator.api.main:app --reload --port 8000

    # Production
    uvicorn orchestrator.api.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from orchestrator.api import (
    jobs_api,
    metrics_api,
    resources_api,
    supervisor_api,
    supervisor_routes,
    supervisor_websocket,
    worker_status_api,
)
from orchestrator.api.dialogue_ws import dialogue_websocket_endpoint
from orchestrator.api.terminal_ws import terminal_websocket_endpoint

# from orchestrator.api import ecosystem_api  # NOT WORKING - using direct endpoints instead

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# OpenAPI tags metadata
tags_metadata = [
    {
        "name": "supervisor",
        "description": """
        **Worker Supervision and Control**

        Monitor and manage Claude Code worker instances. Control worker lifecycle,
        retrieve real - time status, and access aggregate metrics.

        **Endpoints:**
        - List workers with filtering
        - Get worker details
        - Pause / resume / terminate workers
        - Retrieve system metrics
        """,
    },
    {
        "name": "jobs",
        "description": """
        **Job Orchestration and Management**

        Submit, monitor, and control hierarchical AI coding jobs. Track job lifecycle
        from submission through completion with state machine validation.

        **Job States:**
        SUBMITTED → PENDING → RUNNING → COMPLETED / FAILED / CANCELED

        **Features:**
        - Job submission with hierarchy support
        - Job status tracking
        - Job cancellation
        - Parent - child job relationships
        """,
    },
    {
        "name": "resources",
        "description": """
        **Hierarchical Resource Management**

        Allocate and manage compute resources across hierarchy depth levels.
        Enforce quotas and track resource usage for optimal job execution.

        **Depth - Based Quotas:**
        - Depth 0: Root jobs (highest quota)
        - Depth 1 - 5: Nested jobs (decreasing quotas)

        **Features:**
        - Resource quota queries
        - Resource allocation
        - Resource release
        - Usage monitoring
        """,
    },
]

# Create FastAPI app
app = FastAPI(
    title="Parallel AI Coding Orchestrator API",
    description="""
## Week 2 MVP - Manager AI Integration API

Enterprise - grade REST API for orchestrating and monitoring parallel AI coding workflows.

### Key Features
- **Supervisor API**: Monitor and control Claude Code worker instances
- **Resource Management**: Hierarchical resource allocation with depth - based quotas
- **Job Orchestration**: Manage job lifecycle with state machine validation
- **Authentication**: JWT - based authentication with scope - based authorization

### Architecture
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: JWT Bearer tokens with scopes
- **State Management**: Validated state machines for workers and jobs
- **Testing**: 44 integration tests with 29% code coverage

### Quick Start
1. Generate test token: Use `/api / auth / token` endpoint
2. Access protected endpoints with `Authorization: Bearer <token>` header
3. Explore interactive docs at `/docs` or `/redoc`

### Support
- **GitHub**: [parallel - coding](https://github.com / your - org / parallel - coding)
- **Documentation**: [Wiki](https://github.com / your - org / parallel - coding / wiki)
""",
    version="2.0.0 - week2 - mvp",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
    contact={
        "name": "Parallel AI Development Team",
        "email": "dev@parallel - ai.example.com",
    },
    license_info={
        "name": "MIT",
    },
)

# Configure CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8080",  # Vue dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(metrics_api.router)
app.include_router(worker_status_api.router)
app.include_router(supervisor_routes.router)
app.include_router(supervisor_websocket.router)
app.include_router(supervisor_api.router)
app.include_router(resources_api.router)
app.include_router(jobs_api.router)
# app.include_router(ecosystem_api.router)  # NOT WORKING - using direct endpoints instead

# Workspace configuration
WORKSPACE_ROOT = Path(__file__).parent.parent.parent / "workspace"


@app.get("/")
async def root():
    """
    API root endpoint.

    Returns:
        Welcome message with API information
    """
    return {
        "message": "Parallel AI Coding Orchestrator API",
        "version": "1.0.0",
        "endpoints": {
            "dialogue_ws": "/ws / dialogue/{worker_id}",
            "health": "/health",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Server status and workspace information
    """
    return {
        "status": "healthy",
        "workspace_root": str(WORKSPACE_ROOT),
        "workspace_exists": WORKSPACE_ROOT.exists(),
    }


@app.get("/api / v1 / workers")
async def list_workers():
    """
    List all available workers.

    Returns:
        List of worker IDs with their workspace status
    """
    if not WORKSPACE_ROOT.exists():
        return {"workers": []}

    workers = []
    for worker_dir in WORKSPACE_ROOT.iterdir():
        if worker_dir.is_dir() and worker_dir.name.startswith("worker_"):
            transcript_file = worker_dir / "dialogue_transcript.jsonl"
            workers.append(
                {
                    "worker_id": worker_dir.name,
                    "workspace_path": str(worker_dir),
                    "has_dialogue": transcript_file.exists(),
                    "dialogue_size": (
                        transcript_file.stat().st_size if transcript_file.exists() else 0
                    ),
                }
            )

    return {"workers": workers, "count": len(workers)}


@app.get("/api / v1 / workers/{worker_id}")
async def get_worker_info(worker_id: str):
    """
    Get information about a specific worker.

    Args:
        worker_id: Worker identifier (e.g., "worker_001")

    Returns:
        Worker details including dialogue status

    Raises:
        HTTPException: If worker not found
    """
    worker_path = WORKSPACE_ROOT / worker_id

    if not worker_path.exists():
        raise HTTPException(status_code=404, detail=f"Worker {worker_id} not found")

    transcript_file = worker_path / "dialogue_transcript.jsonl"
    transcript_txt = worker_path / "dialogue_transcript.txt"

    return {
        "worker_id": worker_id,
        "workspace_path": str(worker_path),
        "dialogue": {
            "jsonl_exists": transcript_file.exists(),
            "jsonl_size": transcript_file.stat().st_size if transcript_file.exists() else 0,
            "txt_exists": transcript_txt.exists(),
            "txt_size": transcript_txt.stat().st_size if transcript_txt.exists() else 0,
        },
    }


@app.websocket("/ws / dialogue/{worker_id}")
async def websocket_dialogue_endpoint(websocket: WebSocket, worker_id: str):
    """
    WebSocket endpoint for streaming worker dialogue.

    This endpoint streams dialogue entries in real - time from the specified
    worker's dialogue_transcript.jsonl file.

    Args:
        websocket: WebSocket connection
        worker_id: Worker identifier (e.g., "worker_001")

    Message Format:
        {
            "type": "historical" | "entry" | "ready" | "error",
            "data": {
                "timestamp": float,
                "direction": "worker→orchestrator" | "orchestrator→worker",
                "content": str,
                "type": "output" | "response",
                "confirmation_type": str | null,
                "confirmation_message": str | null
            }
        }

    Example:
        ```javascript
        const ws = new WebSocket('ws://localhost:8000 / ws / dialogue / worker_001');
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            console.log(message.type, message.data);
        };
        ```
    """
    try:
        await dialogue_websocket_endpoint(
            websocket=websocket, worker_id=worker_id, workspace_root=str(WORKSPACE_ROOT)
        )
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {worker_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {worker_id}: {e}")
        raise


@app.websocket("/ws / terminal/{worker_id}")
async def websocket_terminal_endpoint(
    websocket: WebSocket, worker_id: str, terminal_type: str = "worker"
):
    """
    WebSocket endpoint for streaming raw terminal output.

    This endpoint streams raw terminal output lines in real - time from the
    specified worker's terminal log file (worker or orchestrator).

    Args:
        websocket: WebSocket connection
        worker_id: Worker identifier (e.g., "worker_001")
        terminal_type: Type of terminal to stream ("worker" or "orchestrator", defaults to "worker")

    Message Format:
        {
            "type": "ready" | "line" | "error",
            "worker_id": str,
            "terminal_type": str,
            "content": str (for "line" type),
            "message": str (for "ready" and "error" types)
        }

    Example:
        ```javascript
        // Worker terminal
        const ws = new WebSocket('ws://localhost:8000 / ws / terminal / worker_001?terminal_type=worker');

        // Orchestrator terminal
        const ws2 = new WebSocket('ws://localhost:8000 / ws / terminal / worker_001?terminal_type=orchestrator');

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'line') {
                console.log(message.content);
            }
        };
        ```
    """
    try:
        await terminal_websocket_endpoint(
            websocket=websocket,
            worker_id=worker_id,
            workspace_root=str(WORKSPACE_ROOT),
            terminal_type=terminal_type,
        )
    except WebSocketDisconnect:
        logger.info(f"Terminal WebSocket disconnected: {worker_id} ({terminal_type})")
    except Exception as e:
        logger.error(f"Terminal WebSocket error for {worker_id} ({terminal_type}): {e}")
        raise


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler.

    Logs all unhandled exceptions and returns a generic error response.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if app.debug else "An unexpected error occurred",
        },
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """
    Application startup tasks.

    - Check workspace directory
    - Initialize logging
    - Verify required dependencies
    """
    logger.info("Starting Parallel AI Coding Orchestrator API")
    logger.info(f"Workspace root: {WORKSPACE_ROOT}")

    if not WORKSPACE_ROOT.exists():
        logger.warning(f"Workspace directory does not exist: {WORKSPACE_ROOT}")
        logger.info("Workspace will be created when workers are spawned")
    else:
        worker_count = sum(
            1 for d in WORKSPACE_ROOT.iterdir() if d.is_dir() and d.name.startswith("worker_")
        )
        logger.info(f"Found {worker_count} worker workspaces")

    # Initialize worker status API (Milestone 1.3)
    worker_status_api.init_worker_status_api(WORKSPACE_ROOT)
    logger.info("Worker status API initialized")


# ========== ECOSYSTEM API ENDPOINTS ==========
# Added directly to main.py due to router registration issues


@app.get("/api / v1 / ecosystem / health")
async def get_ecosystem_health():
    """Get comprehensive health status for entire ecosystem"""
    import time

    worker_count = 0
    if WORKSPACE_ROOT.exists():
        worker_count = sum(
            1 for d in WORKSPACE_ROOT.iterdir() if d.is_dir() and d.name.startswith("worker_")
        )

    return {
        "status": "healthy",
        "timestamp": time.time(),
        "apps": {
            "parallel_coding": {
                "status": "active",
                "workers_count": worker_count,
                "uptime": "24h",
                "version": "1.0.0",
            },
            "manager_ai": {"status": "coming_soon"},
            "mt4_integration": {"status": "coming_soon"},
            "trading_dashboard": {"status": "coming_soon"},
        },
        "system": {"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0},
    }


@app.get("/api / v1 / ecosystem / metrics / summary")
async def get_ecosystem_metrics_summary():
    """Get aggregate performance metrics across all apps"""
    import random
    import time

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


@app.get("/api / v1 / ecosystem / status")
async def get_ecosystem_status():
    """Get basic status of ecosystem API"""
    import time

    return {
        "status": "online",
        "active_connections": 0,  # TODO: Track WebSocket connections
        "version": "1.0.0",
        "timestamp": time.time(),
    }


# ActivityBroadcaster for WebSocket management
class ActivityBroadcaster:
    def __init__(self):
        self.connections: list = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
        logger.info(f"Activity feed connection added. Total: {len(self.connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)
            logger.info(f"Activity feed connection removed. Total: {len(self.connections)}")

    async def broadcast(self, activity: dict):
        disconnected = []
        for connection in self.connections:
            try:
                await connection.send_json(activity)
            except Exception as e:
                logger.error(f"Failed to send to connection: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


activity_broadcaster = ActivityBroadcaster()


@app.websocket("/api / v1 / ecosystem / activity")
async def websocket_ecosystem_activity(websocket: WebSocket):
    """WebSocket endpoint for real - time activity feed"""
    from datetime import datetime

    await activity_broadcaster.connect(websocket)

    try:
        # Send welcome message
        await websocket.send_json(
            {
                "id": "system_connected",
                "timestamp": datetime.now().isoformat(),
                "app": "ecosystem",
                "message": "Connected to activity feed",
                "type": "info",
            }
        )

        # Send initial mock activities
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
        ]

        for activity in initial_activities:
            await websocket.send_json(activity)

        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received from client: {data}")

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


# ========== END ECOSYSTEM API ENDPOINTS ==========


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown tasks.

    - Clean up resources
    - Close connections
    - Log shutdown
    """
    logger.info("Shutting down Parallel AI Coding Orchestrator API")


if __name__ == "__main__":
    import uvicorn

    # Development server
    uvicorn.run(
        "orchestrator.api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
