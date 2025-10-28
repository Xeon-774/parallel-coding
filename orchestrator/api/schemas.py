"""Pydantic schemas for Job API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from orchestrator.core.db_models import JobStatus


class JobSubmitRequest(BaseModel):
    """Request body for submitting a new job."""

    task_description: str = Field(min_length=1, max_length=4096)
    worker_count: int = Field(ge=1, le=1000)
    depth: int = Field(ge=0, le=1000, default=0)
    parent_job_id: Optional[str] = Field(default=None)


class JobResponse(BaseModel):
    """Serialized representation of a Job."""

    id: str
    depth: int
    worker_count: int
    task_description: str
    parent_job_id: Optional[str]
    status: JobStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

