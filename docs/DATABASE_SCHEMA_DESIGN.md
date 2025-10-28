# Database Schema Design - Week 2 MVP

**Document Version**: 1.0
**Created**: 2025-10-28
**Status**: Active

---

## Executive Summary

This document defines the database schema for Week 2 MVP, including SQLAlchemy models, Alembic migrations, and indexing strategies. The schema supports worker supervision, resource management, and job orchestration with full audit trails.

**Key Design Principles**:
- **PostgreSQL primary** (SQLite for development)
- **Audit trails**: All state transitions logged
- **Multi-tenancy**: Workspace-level isolation
- **Idempotency**: Request ID tracking
- **Performance**: Strategic indexing

---

## 1. Database Strategy

### 1.1 Database Selection

| Environment | Database | Rationale |
|-------------|----------|-----------|
| Development | SQLite | Simple setup, file-based, no server |
| Testing | SQLite (in-memory) | Fast, isolated tests |
| Production | PostgreSQL 14+ | JSONB support, scalability, reliability |

### 1.2 Connection Configuration

```python
"""
Database configuration module.
"""
from typing import Optional
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    database_url: str = "sqlite:///./parallel_ai.db"
    echo_sql: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_prefix = "DB_"

# Global settings instance
settings = DatabaseSettings()

# SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    echo=settings.echo_sql,
    pool_size=settings.pool_size,
    max_overflow=settings.max_overflow,
    pool_timeout=settings.pool_timeout,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """
    Dependency injection for database session.

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 2. Core Tables

### 2.1 Workers Table

Stores worker metadata and current state.

```python
"""
Worker model.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Enum,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
import enum
import uuid

class WorkerStatus(str, enum.Enum):
    """Worker status enumeration."""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"

class Worker(Base):
    """
    Worker database model.

    Represents a Claude Code worker instance managed by Supervisor.
    """

    __tablename__ = "workers"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: f"w_{uuid.uuid4().hex[:12]}",
    )
    workspace_id = Column(
        String(36), nullable=False, index=True, comment="Workspace ID"
    )
    status = Column(
        Enum(WorkerStatus),
        nullable=False,
        default=WorkerStatus.IDLE,
        index=True,
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    metadata = Column(
        JSON, nullable=True, comment="Additional worker metadata"
    )

    # Relationships
    state_transitions = relationship(
        "WorkerStateTransition",
        back_populates="worker",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("ix_workers_workspace_status", "workspace_id", "status"),
        Index("ix_workers_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Worker(id={self.id}, status={self.status}, "
            f"workspace={self.workspace_id})>"
        )
```

**SQL Schema**:

```sql
CREATE TABLE workers (
    id VARCHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(36) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB,
    CONSTRAINT ck_worker_status CHECK (
        status IN ('IDLE', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'TERMINATED')
    )
);

CREATE INDEX ix_workers_workspace_id ON workers(workspace_id);
CREATE INDEX ix_workers_status ON workers(status);
CREATE INDEX ix_workers_workspace_status ON workers(workspace_id, status);
CREATE INDEX ix_workers_created_at ON workers(created_at);
```

---

### 2.2 Worker State Transitions Table

Audit trail for all worker state changes.

```python
"""
Worker state transition model.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

class WorkerStateTransition(Base):
    """
    Worker state transition audit log.

    Records all state changes for workers with timestamp and reason.
    """

    __tablename__ = "worker_state_transitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_id = Column(
        String(36),
        ForeignKey("workers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_state = Column(
        String(20), nullable=True, comment="Previous state (NULL for initial)"
    )
    to_state = Column(String(20), nullable=False, comment="New state")
    reason = Column(Text, nullable=True, comment="Reason for transition")
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    worker = relationship("Worker", back_populates="state_transitions")

    # Indexes
    __table_args__ = (
        Index("ix_wst_worker_id", "worker_id"),
        Index("ix_wst_timestamp", "timestamp"),
        Index("ix_wst_worker_timestamp", "worker_id", "timestamp"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<WorkerStateTransition(worker={self.worker_id}, "
            f"{self.from_state} → {self.to_state})>"
        )
```

**SQL Schema**:

```sql
CREATE TABLE worker_state_transitions (
    id SERIAL PRIMARY KEY,
    worker_id VARCHAR(36) NOT NULL REFERENCES workers(id) ON DELETE CASCADE,
    from_state VARCHAR(20),
    to_state VARCHAR(20) NOT NULL,
    reason TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_wst_worker_id ON worker_state_transitions(worker_id);
CREATE INDEX ix_wst_timestamp ON worker_state_transitions(timestamp);
CREATE INDEX ix_wst_worker_timestamp ON worker_state_transitions(worker_id, timestamp);
```

---

### 2.3 Jobs Table

Stores job metadata and hierarchical relationships.

```python
"""
Job model.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    Enum,
    ForeignKey,
    JSON,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
import enum
import uuid

class JobStatus(str, enum.Enum):
    """Job status enumeration."""

    SUBMITTED = "SUBMITTED"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"

class Job(Base):
    """
    Job database model.

    Represents a task submitted for hierarchical execution.
    """

    __tablename__ = "jobs"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: f"j_{uuid.uuid4().hex[:12]}",
    )
    parent_job_id = Column(
        String(36),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    depth = Column(
        Integer,
        nullable=False,
        comment="Depth in hierarchy (0-5)",
    )
    status = Column(
        Enum(JobStatus),
        nullable=False,
        default=JobStatus.SUBMITTED,
        index=True,
    )
    worker_count = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Number of workers allocated",
    )
    task_description = Column(
        Text, nullable=False, comment="Task description or file path"
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True, comment="Job execution result")
    error = Column(JSON, nullable=True, comment="Error details if failed")

    # Relationships
    parent_job = relationship(
        "Job", remote_side=[id], backref="child_jobs"
    )
    state_transitions = relationship(
        "JobStateTransition",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    resource_allocations = relationship(
        "ResourceAllocation",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("depth >= 0 AND depth <= 5", name="ck_job_depth"),
        CheckConstraint("worker_count >= 1", name="ck_worker_count"),
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_parent_id", "parent_job_id"),
        Index("ix_jobs_depth_status", "depth", "status"),
        Index("ix_jobs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Job(id={self.id}, status={self.status}, "
            f"depth={self.depth})>"
        )
```

**SQL Schema**:

```sql
CREATE TABLE jobs (
    id VARCHAR(36) PRIMARY KEY,
    parent_job_id VARCHAR(36) REFERENCES jobs(id) ON DELETE SET NULL,
    depth INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    worker_count INTEGER NOT NULL DEFAULT 1,
    task_description TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result JSONB,
    error JSONB,
    CONSTRAINT ck_job_depth CHECK (depth >= 0 AND depth <= 5),
    CONSTRAINT ck_worker_count CHECK (worker_count >= 1),
    CONSTRAINT ck_job_status CHECK (
        status IN ('SUBMITTED', 'PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELED')
    )
);

CREATE INDEX ix_jobs_status ON jobs(status);
CREATE INDEX ix_jobs_parent_id ON jobs(parent_job_id);
CREATE INDEX ix_jobs_depth_status ON jobs(depth, status);
CREATE INDEX ix_jobs_created_at ON jobs(created_at);
```

---

### 2.4 Job State Transitions Table

Audit trail for job state changes.

```python
"""
Job state transition model.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

class JobStateTransition(Base):
    """
    Job state transition audit log.

    Records all state changes for jobs with timestamp and reason.
    """

    __tablename__ = "job_state_transitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(
        String(36),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_state = Column(
        String(20), nullable=True, comment="Previous state"
    )
    to_state = Column(String(20), nullable=False, comment="New state")
    reason = Column(Text, nullable=True, comment="Reason for transition")
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    job = relationship("Job", back_populates="state_transitions")

    # Indexes
    __table_args__ = (
        Index("ix_jst_job_id", "job_id"),
        Index("ix_jst_timestamp", "timestamp"),
        Index("ix_jst_job_timestamp", "job_id", "timestamp"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<JobStateTransition(job={self.job_id}, "
            f"{self.from_state} → {self.to_state})>"
        )
```

**SQL Schema**:

```sql
CREATE TABLE job_state_transitions (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    from_state VARCHAR(20),
    to_state VARCHAR(20) NOT NULL,
    reason TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_jst_job_id ON job_state_transitions(job_id);
CREATE INDEX ix_jst_timestamp ON job_state_transitions(timestamp);
CREATE INDEX ix_jst_job_timestamp ON job_state_transitions(job_id, timestamp);
```

---

### 2.5 Resource Allocations Table

Tracks resource allocations for jobs.

```python
"""
Resource allocation model.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

class ResourceAllocation(Base):
    """
    Resource allocation tracking.

    Records resource allocations for jobs at specific depth levels.
    """

    __tablename__ = "resource_allocations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(
        String(36),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    depth = Column(
        Integer, nullable=False, comment="Depth level (0-5)"
    )
    worker_count = Column(
        Integer, nullable=False, comment="Number of workers allocated"
    )
    allocated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    released_at = Column(
        DateTime, nullable=True, comment="When resources were released"
    )

    # Relationships
    job = relationship("Job", back_populates="resource_allocations")

    # Constraints
    __table_args__ = (
        CheckConstraint("depth >= 0 AND depth <= 5", name="ck_ra_depth"),
        CheckConstraint(
            "worker_count >= 1", name="ck_ra_worker_count"
        ),
        Index("ix_ra_job_id", "job_id"),
        Index("ix_ra_depth", "depth"),
        Index("ix_ra_released_at", "released_at"),
        Index("ix_ra_depth_released", "depth", "released_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ResourceAllocation(job={self.job_id}, depth={self.depth}, "
            f"workers={self.worker_count})>"
        )
```

**SQL Schema**:

```sql
CREATE TABLE resource_allocations (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    depth INTEGER NOT NULL,
    worker_count INTEGER NOT NULL,
    allocated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    released_at TIMESTAMP,
    CONSTRAINT ck_ra_depth CHECK (depth >= 0 AND depth <= 5),
    CONSTRAINT ck_ra_worker_count CHECK (worker_count >= 1)
);

CREATE INDEX ix_ra_job_id ON resource_allocations(job_id);
CREATE INDEX ix_ra_depth ON resource_allocations(depth);
CREATE INDEX ix_ra_released_at ON resource_allocations(released_at);
CREATE INDEX ix_ra_depth_released ON resource_allocations(depth, released_at);
```

---

### 2.6 Idempotency Keys Table

Tracks idempotent requests to prevent duplicate operations.

```python
"""
Idempotency key model.
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    Index,
)

class IdempotencyKey(Base):
    """
    Idempotency key tracking.

    Stores processed requests to enable idempotent operations.
    """

    __tablename__ = "idempotency_keys"

    request_id = Column(String(36), primary_key=True)
    endpoint = Column(
        String(255), nullable=False, comment="API endpoint path"
    )
    response_status = Column(
        Integer, nullable=False, comment="HTTP status code"
    )
    response_body = Column(
        Text, nullable=False, comment="Cached response body (JSON)"
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(
        DateTime, nullable=False, comment="TTL for cache entry"
    )

    # Indexes
    __table_args__ = (Index("ix_ik_expires_at", "expires_at"),)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<IdempotencyKey(request_id={self.request_id}, "
            f"endpoint={self.endpoint})>"
        )
```

**SQL Schema**:

```sql
CREATE TABLE idempotency_keys (
    request_id VARCHAR(36) PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    response_status INTEGER NOT NULL,
    response_body TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX ix_ik_expires_at ON idempotency_keys(expires_at);
```

---

## 3. Alembic Migrations

### 3.1 Migration Setup

```bash
# Initialize Alembic
alembic init alembic

# Edit alembic.ini
sqlalchemy.url = postgresql://user:pass@localhost/parallel_ai

# Edit alembic/env.py
from orchestrator.database import Base
from orchestrator.models import (
    Worker,
    WorkerStateTransition,
    Job,
    JobStateTransition,
    ResourceAllocation,
    IdempotencyKey,
)

target_metadata = Base.metadata
```

### 3.2 Initial Migration

```python
"""
Initial schema migration.

Revision ID: 001_initial_schema
Created: 2025-10-28
"""
from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Create initial schema."""
    # Workers table
    op.create_table(
        "workers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.CheckConstraint(
            "status IN ('IDLE', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'TERMINATED')",
            name="ck_worker_status",
        ),
    )
    op.create_index("ix_workers_workspace_id", "workers", ["workspace_id"])
    op.create_index("ix_workers_status", "workers", ["status"])
    op.create_index(
        "ix_workers_workspace_status",
        "workers",
        ["workspace_id", "status"],
    )

    # Worker state transitions
    op.create_table(
        "worker_state_transitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("worker_id", sa.String(36), nullable=False),
        sa.Column("from_state", sa.String(20), nullable=True),
        sa.Column("to_state", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["worker_id"], ["workers.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_wst_worker_id", "worker_state_transitions", ["worker_id"]
    )

    # Jobs table
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("parent_job_id", sa.String(36), nullable=True),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("worker_count", sa.Integer(), nullable=False),
        sa.Column("task_description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.JSON(), nullable=True),
        sa.CheckConstraint(
            "depth >= 0 AND depth <= 5", name="ck_job_depth"
        ),
        sa.CheckConstraint(
            "worker_count >= 1", name="ck_worker_count"
        ),
        sa.ForeignKeyConstraint(
            ["parent_job_id"], ["jobs.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_parent_id", "jobs", ["parent_job_id"])

    # Resource allocations
    op.create_table(
        "resource_allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.Column("worker_count", sa.Integer(), nullable=False),
        sa.Column("allocated_at", sa.DateTime(), nullable=False),
        sa.Column("released_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "depth >= 0 AND depth <= 5", name="ck_ra_depth"
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["jobs.id"], ondelete="CASCADE"
        ),
    )
    op.create_index("ix_ra_job_id", "resource_allocations", ["job_id"])

    # Idempotency keys
    op.create_table(
        "idempotency_keys",
        sa.Column("request_id", sa.String(36), primary_key=True),
        sa.Column("endpoint", sa.String(255), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_ik_expires_at", "idempotency_keys", ["expires_at"]
    )

def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("idempotency_keys")
    op.drop_table("resource_allocations")
    op.drop_table("job_state_transitions")
    op.drop_table("jobs")
    op.drop_table("worker_state_transitions")
    op.drop_table("workers")
```

### 3.3 Running Migrations

```bash
# Generate migration from models
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current revision
alembic current

# Show migration history
alembic history
```

---

## 4. Query Patterns

### 4.1 Common Queries

```python
"""
Common database query patterns.
"""
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Get all running workers for workspace
def get_running_workers(db: Session, workspace_id: str):
    """Get all running workers for a workspace."""
    return (
        db.query(Worker)
        .filter(
            and_(
                Worker.workspace_id == workspace_id,
                Worker.status == WorkerStatus.RUNNING,
            )
        )
        .all()
    )

# Get jobs by depth and status
def get_jobs_by_depth_status(
    db: Session, depth: int, status: JobStatus
):
    """Get jobs at specific depth with status."""
    return (
        db.query(Job)
        .filter(and_(Job.depth == depth, Job.status == status))
        .order_by(Job.created_at.desc())
        .all()
    )

# Get active resource allocations at depth
def get_active_allocations_at_depth(db: Session, depth: int):
    """Get active (not released) resource allocations at depth."""
    return (
        db.query(ResourceAllocation)
        .filter(
            and_(
                ResourceAllocation.depth == depth,
                ResourceAllocation.released_at.is_(None),
            )
        )
        .all()
    )

# Count workers by status for workspace
def count_workers_by_status(db: Session, workspace_id: str):
    """Count workers grouped by status."""
    return (
        db.query(Worker.status, func.count(Worker.id))
        .filter(Worker.workspace_id == workspace_id)
        .group_by(Worker.status)
        .all()
    )

# Get worker state history
def get_worker_state_history(db: Session, worker_id: str, limit: int = 10):
    """Get recent state transitions for worker."""
    return (
        db.query(WorkerStateTransition)
        .filter(WorkerStateTransition.worker_id == worker_id)
        .order_by(WorkerStateTransition.timestamp.desc())
        .limit(limit)
        .all()
    )

# Cleanup expired idempotency keys
def cleanup_expired_idempotency_keys(db: Session) -> int:
    """Delete expired idempotency keys."""
    now = datetime.utcnow()
    result = (
        db.query(IdempotencyKey)
        .filter(IdempotencyKey.expires_at < now)
        .delete()
    )
    db.commit()
    return result
```

---

## 5. Performance Optimization

### 5.1 Indexing Strategy

**Key indexes** (already included in models):

- `ix_workers_workspace_status`: Efficient workspace-scoped queries
- `ix_jobs_depth_status`: Fast job queries by depth
- `ix_ra_depth_released`: Quick active allocation checks
- `ix_wst_worker_timestamp`: Fast state history lookups

### 5.2 Query Optimization Tips

```python
# Use eager loading to avoid N+1 queries
from sqlalchemy.orm import joinedload

workers = (
    db.query(Worker)
    .options(joinedload(Worker.state_transitions))
    .filter(Worker.workspace_id == workspace_id)
    .all()
)

# Use pagination for large result sets
def get_jobs_paginated(db: Session, limit: int = 50, offset: int = 0):
    """Get paginated jobs list."""
    return (
        db.query(Job)
        .order_by(Job.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

# Use exists() for existence checks
def worker_exists(db: Session, worker_id: str) -> bool:
    """Check if worker exists efficiently."""
    return db.query(
        db.query(Worker).filter(Worker.id == worker_id).exists()
    ).scalar()
```

---

## 6. Testing Strategy

### 6.1 Database Fixtures

```python
"""
Pytest fixtures for database testing.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from orchestrator.database import Base

@pytest.fixture(scope="function")
def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def sample_worker(db_session):
    """Create sample worker for testing."""
    worker = Worker(
        id="w_test123",
        workspace_id="ws_test",
        status=WorkerStatus.IDLE,
    )
    db_session.add(worker)
    db_session.commit()
    return worker
```

### 6.2 Model Tests

```python
"""
Unit tests for database models.
"""
import pytest
from orchestrator.models import Worker, WorkerStatus

def test_create_worker(db_session):
    """Test creating worker."""
    worker = Worker(workspace_id="ws_test")
    db_session.add(worker)
    db_session.commit()

    assert worker.id.startswith("w_")
    assert worker.status == WorkerStatus.IDLE

def test_worker_state_transition(db_session, sample_worker):
    """Test recording state transition."""
    transition = WorkerStateTransition(
        worker_id=sample_worker.id,
        from_state=WorkerStatus.IDLE,
        to_state=WorkerStatus.RUNNING,
        reason="Task assigned",
    )
    db_session.add(transition)
    db_session.commit()

    assert transition.id is not None
    assert transition.worker_id == sample_worker.id
```

---

## 7. Migration Strategy

### 7.1 Production Deployment

```bash
# 1. Backup database
pg_dump parallel_ai > backup_$(date +%Y%m%d).sql

# 2. Test migration on staging
alembic upgrade head --sql > migration.sql
psql -f migration.sql staging_db

# 3. Apply to production
alembic upgrade head
```

### 7.2 Rollback Plan

```bash
# Rollback to previous version
alembic downgrade -1

# Restore from backup if needed
psql parallel_ai < backup_20251028.sql
```

---

## 8. References

- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- Alembic Documentation: https://alembic.sqlalchemy.org/
- PostgreSQL 14 Documentation: https://www.postgresql.org/docs/14/
- Week 2 MVP Specification
- State Machine Design

---

**Approval Status**: Ready for implementation
**Next Steps**: Create SQLAlchemy models + Alembic migrations
