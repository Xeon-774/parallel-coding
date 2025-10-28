"""FastAPI application wiring for the Job Orchestrator."""
from __future__ import annotations

from fastapi import FastAPI

from .jobs_api import router as jobs_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance.

    Returns:
        A FastAPI app including the jobs router.
    """

    app = FastAPI(title="Job Orchestrator API")
    app.include_router(jobs_router)
    return app


app = create_app()

