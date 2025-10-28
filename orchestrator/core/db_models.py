"""
SQLAlchemy database models for Parallel AI Coding Orchestrator - Week 2 MVP.

This module defines the database schema including:
- Worker instances and state transitions
- Job submissions and lifecycle
- Resource allocations
- Idempotency keys for duplicate operation prevention

Security:
- SQL parameterization via SQLAlchemy ORM (Excellence AI Standard)
- No raw SQL string concatenation

Type Safety:
- Explicit type annotations with Optional/List
- Enum types for status fields

Usage:
    from orchestrator.core.db_models import Worker, Job, ResourceAllocation
    from orchestrator.core.database import SessionLocal

    db = SessionLocal()
    worker = Worker(workspace_id="ws_123", status=WorkerStatus.IDLE)
    db.add(worker)
    db.commit()
"""

from datetime import datetime, timedelta
from typing import Optional, List
import enum
import uuid

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    Enum as SQLEnum,
    JSON,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from orchestrator.core.database import Base


# ============================================================================
# Enumerations
# ============================================================================

class WorkerStatus(str, enum.Enum):
    """
    Worker lifecycle status enumeration.

    States:
        IDLE: Worker created but not yet started
        RUNNING: Worker actively executing task
        PAUSED: Worker temporarily suspended
        COMPLETED: Worker finished successfully
        FAILED: Worker encountered fatal error
        TERMINATED: Worker manually terminated
    """

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"


class JobStatus(str, enum.Enum):
    """
    Job lifecycle status enumeration.

    States:
        SUBMITTED: Job received but not yet queued
        PENDING: Job queued, waiting for resources
        RUNNING: Job actively being processed
        COMPLETED: Job finished successfully
        FAILED: Job encountered fatal error
        CANCELED: Job canceled by user
    """

    SUBMITTED = "SUBMITTED"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


# ============================================================================
# Worker Models
# ============================================================================

class Worker(Base):
    """
    Worker instance model.

    Represents a Claude Code worker managed by the Supervisor API.
    Tracks worker lifecycle, status, and metadata.

    Attributes:
        id: Unique worker identifier (format: w_<12 hex chars>)
        workspace_id: Workspace identifier for multi-tenancy
        status: Current worker status (WorkerStatus enum)
        created_at: Worker creation timestamp
        updated_at: Last update timestamp (auto-updated)
        metadata: Additional worker metadata (JSON)

    Relationships:
        state_transitions: List of state transition audit records

    Example:
        >>> worker = Worker(workspace_id="ws_abc123")
        >>> worker.id  # 'w_a1b2c3d4e5f6'
        >>> worker.status  # WorkerStatus.IDLE
    """

    __tablename__ = "workers"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: f"w_{uuid.uuid4().hex[:12]}",
        comment="Unique worker identifier",
    )
    workspace_id = Column(
        String(36),
        nullable=False,
        index=True,
        comment="Workspace ID for multi-tenancy",
    )
    status = Column(
        SQLEnum(WorkerStatus),
        nullable=False,
        default=WorkerStatus.IDLE,
        index=True,
        comment="Current worker status",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Worker creation time",
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Last update time",
    )
    worker_metadata = Column(
        JSON,
        nullable=True,
        comment="Additional worker metadata (JSON)",
        name="metadata"  # DB column name remains 'metadata' for compatibility
    )

    # Relationships
    state_transitions = relationship(
        "WorkerStateTransition",
        back_populates="worker",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Indexes for performance
    __table_args__ = (
        Index("ix_workers_workspace_status", "workspace_id", "status"),
        Index("ix_workers_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<Worker(id={self.id}, status={self.status.value}, "
            f"workspace={self.workspace_id})>"
        )


class WorkerStateTransition(Base):
    """
    Worker state transition audit log.

    Records all state changes for workers with timestamp and reason.
    Provides complete audit trail for compliance and debugging.

    Attributes:
        id: Auto-incrementing primary key
        worker_id: Foreign key to workers table
        from_state: Previous state (NULL for initial state)
        to_state: New state after transition
        reason: Optional reason for transition
        timestamp: When transition occurred

    Relationships:
        worker: Associated worker instance

    Example:
        >>> transition = WorkerStateTransition(
        ...     worker_id="w_a1b2c3",
        ...     from_state="IDLE",
        ...     to_state="RUNNING",
        ...     reason="User started worker"
        ... )
    """

    __tablename__ = "worker_state_transitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_id = Column(
        String(36),
        ForeignKey("workers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Worker ID",
    )
    from_state = Column(
        String(20),
        nullable=True,
        comment="Previous state (NULL for initial)",
    )
    to_state = Column(
        String(20),
        nullable=False,
        comment="New state",
    )
    reason = Column(
        Text,
        nullable=True,
        comment="Reason for transition",
    )
    timestamp = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="Transition timestamp",
    )

    # Relationships
    worker = relationship("Worker", back_populates="state_transitions")

    # Indexes
    __table_args__ = (
        Index("ix_wst_worker_timestamp", "worker_id", "timestamp"),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<WorkerStateTransition(worker={self.worker_id}, "
            f"{self.from_state} → {self.to_state})>"
        )


# ============================================================================
# Job Models
# ============================================================================

class Job(Base):
    """
    Job submission model.

    Represents a task submitted for hierarchical execution.
    Supports parent-child relationships for recursive task decomposition.

    Attributes:
        id: Unique job identifier (format: j_<12 hex chars>)
        parent_job_id: Parent job ID (NULL for root jobs)
        depth: Depth in hierarchy (0-5, 0 = root)
        status: Current job status (JobStatus enum)
        worker_count: Number of workers allocated
        task_description: Task description or file path
        created_at: Job creation timestamp
        started_at: Job start timestamp (NULL if not started)
        completed_at: Job completion timestamp (NULL if not completed)
        result: Job execution result (JSON)
        error: Error details if failed (JSON)

    Relationships:
        parent_job: Parent job (if any)
        child_jobs: List of child jobs
        state_transitions: List of state transition audit records
        resource_allocations: List of resource allocations

    Constraints:
        - depth: 0 <= depth <= 5
        - worker_count: >= 1

    Example:
        >>> job = Job(
        ...     depth=0,
        ...     worker_count=3,
        ...     task_description="Implement Week 2 MVP"
        ... )
    """

    __tablename__ = "jobs"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: f"j_{uuid.uuid4().hex[:12]}",
        comment="Unique job identifier",
    )
    parent_job_id = Column(
        String(36),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Parent job ID (NULL for root)",
    )
    depth = Column(
        Integer,
        nullable=False,
        comment="Depth in hierarchy (0-5)",
    )
    status = Column(
        SQLEnum(JobStatus),
        nullable=False,
        default=JobStatus.SUBMITTED,
        index=True,
        comment="Current job status",
    )
    worker_count = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Number of workers allocated",
    )
    task_description = Column(
        Text,
        nullable=False,
        comment="Task description or file path",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="Job creation time",
    )
    started_at = Column(
        DateTime,
        nullable=True,
        comment="Job start time",
    )
    completed_at = Column(
        DateTime,
        nullable=True,
        comment="Job completion time",
    )
    result = Column(
        JSON,
        nullable=True,
        comment="Job execution result (JSON)",
    )
    error = Column(
        JSON,
        nullable=True,
        comment="Error details if failed (JSON)",
    )

    # Relationships
    parent_job = relationship(
        "Job",
        remote_side=[id],
        backref="child_jobs",
        foreign_keys=[parent_job_id],
    )
    state_transitions = relationship(
        "JobStateTransition",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    resource_allocations = relationship(
        "ResourceAllocation",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("depth >= 0 AND depth <= 5", name="ck_job_depth"),
        CheckConstraint("worker_count >= 1", name="ck_worker_count"),
        Index("ix_jobs_depth_status", "depth", "status"),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<Job(id={self.id}, status={self.status.value}, "
            f"depth={self.depth}, workers={self.worker_count})>"
        )


class JobStateTransition(Base):
    """
    Job state transition audit log.

    Records all state changes for jobs with timestamp and reason.

    Attributes:
        id: Auto-incrementing primary key
        job_id: Foreign key to jobs table
        from_state: Previous state (NULL for initial)
        to_state: New state after transition
        reason: Optional reason for transition
        timestamp: When transition occurred

    Relationships:
        job: Associated job instance
    """

    __tablename__ = "job_state_transitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(
        String(36),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Job ID",
    )
    from_state = Column(
        String(20),
        nullable=True,
        comment="Previous state (NULL for initial)",
    )
    to_state = Column(
        String(20),
        nullable=False,
        comment="New state",
    )
    reason = Column(
        Text,
        nullable=True,
        comment="Reason for transition",
    )
    timestamp = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="Transition timestamp",
    )

    # Relationships
    job = relationship("Job", back_populates="state_transitions")

    # Indexes
    __table_args__ = (
        Index("ix_jst_job_timestamp", "job_id", "timestamp"),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<JobStateTransition(job={self.job_id}, "
            f"{self.from_state} → {self.to_state})>"
        )


# ============================================================================
# Resource Models
# ============================================================================

class ResourceAllocation(Base):
    """
    Resource allocation tracking model.

    Records resource allocations for jobs at specific depth levels.
    Enables resource quota management and tracking.

    Attributes:
        id: Auto-incrementing primary key
        job_id: Foreign key to jobs table
        depth: Depth level (0-5)
        worker_count: Number of workers allocated
        allocated_at: When resources were allocated
        released_at: When resources were released (NULL if still allocated)

    Relationships:
        job: Associated job instance

    Constraints:
        - depth: 0 <= depth <= 5
        - worker_count: >= 1

    Example:
        >>> allocation = ResourceAllocation(
        ...     job_id="j_abc123",
        ...     depth=1,
        ...     worker_count=3
        ... )
    """

    __tablename__ = "resource_allocations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(
        String(36),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Job ID",
    )
    depth = Column(
        Integer,
        nullable=False,
        comment="Depth level (0-5)",
    )
    worker_count = Column(
        Integer,
        nullable=False,
        comment="Number of workers allocated",
    )
    allocated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Allocation timestamp",
    )
    released_at = Column(
        DateTime,
        nullable=True,
        comment="Release timestamp (NULL if still allocated)",
    )

    # Relationships
    job = relationship("Job", back_populates="resource_allocations")

    # Constraints
    __table_args__ = (
        CheckConstraint("depth >= 0 AND depth <= 5", name="ck_ra_depth"),
        CheckConstraint("worker_count >= 1", name="ck_ra_worker_count"),
        Index("ix_ra_depth_released", "depth", "released_at"),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<ResourceAllocation(job={self.job_id}, depth={self.depth}, "
            f"workers={self.worker_count}, "
            f"released={self.released_at is not None})>"
        )


# ============================================================================
# Idempotency Models
# ============================================================================

class IdempotencyKey(Base):
    """
    Idempotency key tracking model.

    Stores processed requests to enable idempotent API operations.
    Prevents duplicate executions of state-changing operations.

    Attributes:
        request_id: Unique request identifier (primary key)
        endpoint: API endpoint path
        response_status: HTTP status code of cached response
        response_body: Cached response body (JSON string)
        created_at: When request was first processed
        expires_at: TTL expiration time

    Example:
        >>> key = IdempotencyKey(
        ...     request_id="req_abc123",
        ...     endpoint="/api/supervisor/workers/pause",
        ...     response_status=200,
        ...     response_body='{"status": "paused"}',
        ...     expires_at=datetime.utcnow() + timedelta(hours=1)
        ... )
    """

    __tablename__ = "idempotency_keys"

    request_id = Column(
        String(36),
        primary_key=True,
        comment="Unique request identifier",
    )
    endpoint = Column(
        String(255),
        nullable=False,
        comment="API endpoint path",
    )
    response_status = Column(
        Integer,
        nullable=False,
        comment="HTTP status code",
    )
    response_body = Column(
        Text,
        nullable=False,
        comment="Cached response body (JSON string)",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Request processing time",
    )
    expires_at = Column(
        DateTime,
        nullable=False,
        comment="TTL expiration time",
    )

    # Indexes
    __table_args__ = (
        Index("ix_ik_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<IdempotencyKey(id={self.request_id}, "
            f"endpoint={self.endpoint}, status={self.response_status})>"
        )
