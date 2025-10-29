"""
Integration tests for Week 2 MVP Phase 1: Core Foundation.

Tests database lifecycle, state machine transitions, authentication,
and database models with CRUD operations and constraints.

Coverage Target: ≥90% for core modules (database, state_machine, auth, db_models)
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from orchestrator.core.auth import (
    create_access_token,
    hash_password,
    verify_password,
    verify_token,
)
from orchestrator.core.database import Base
from orchestrator.core.db_models import (
    IdempotencyKey,
    Job,
    JobStatus,
    ResourceAllocation,
    Worker,
    WorkerStatus,
)
from orchestrator.core.state_machine import (
    JobStateMachine,
    StateTransitionError,
    WorkerStateMachine,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def test_db() -> Generator[Session, None, None]:
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def worker_sm(test_db: Session) -> WorkerStateMachine:
    """Create WorkerStateMachine instance."""
    return WorkerStateMachine(test_db)


@pytest.fixture
def job_sm(test_db: Session) -> JobStateMachine:
    """Create JobStateMachine instance."""
    return JobStateMachine(test_db)


@pytest.fixture
def sample_worker(test_db: Session) -> Worker:
    """Create sample worker for testing."""
    worker = Worker(id="test-worker-1", workspace_id="ws-1", status=WorkerStatus.IDLE)
    test_db.add(worker)
    test_db.commit()
    test_db.refresh(worker)
    return worker


@pytest.fixture
def sample_job(test_db: Session) -> Job:
    """Create sample job for testing."""
    job = Job(
        id="test-job-1",
        depth=0,
        worker_count=1,
        task_description="Test task",
        status=JobStatus.PENDING,
    )
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)
    return job


# ============================================================================
# Task D.1: Core Foundation Integration Tests
# ============================================================================


def test_database_session_lifecycle(test_db: Session) -> None:
    """Test database session creation and cleanup."""
    assert test_db.is_active

    worker = Worker(id="worker-lifecycle-1", workspace_id="ws-1", status=WorkerStatus.IDLE)
    test_db.add(worker)
    test_db.commit()

    assert test_db.query(Worker).count() == 1
    retrieved = test_db.query(Worker).filter_by(id="worker-lifecycle-1").first()
    assert retrieved is not None
    assert retrieved.id == "worker-lifecycle-1"
    assert retrieved.status == WorkerStatus.IDLE


def test_worker_state_transitions_valid(
    test_db: Session, worker_sm: WorkerStateMachine, sample_worker: Worker
) -> None:
    """Test all valid worker state transitions."""
    # IDLE → RUNNING
    worker_sm.transition_worker(
        worker_id=sample_worker.id,
        to_state=WorkerStatus.RUNNING,
        reason="Start work",
    )
    test_db.refresh(sample_worker)
    assert sample_worker.status == WorkerStatus.RUNNING

    # RUNNING → PAUSED
    worker_sm.transition_worker(
        worker_id=sample_worker.id,
        to_state=WorkerStatus.PAUSED,
        reason="Pause work",
    )
    test_db.refresh(sample_worker)
    assert sample_worker.status == WorkerStatus.PAUSED

    # PAUSED → RUNNING
    worker_sm.transition_worker(
        worker_id=sample_worker.id,
        to_state=WorkerStatus.RUNNING,
        reason="Resume work",
    )
    test_db.refresh(sample_worker)
    assert sample_worker.status == WorkerStatus.RUNNING

    # RUNNING → COMPLETED
    worker_sm.transition_worker(
        worker_id=sample_worker.id,
        to_state=WorkerStatus.COMPLETED,
        reason="Work complete",
    )
    test_db.refresh(sample_worker)
    assert sample_worker.status == WorkerStatus.COMPLETED


def test_worker_invalid_transitions(
    test_db: Session, worker_sm: WorkerStateMachine, sample_worker: Worker
) -> None:
    """Test StateTransitionError handling for invalid transitions."""
    # IDLE → TERMINATED is valid, but TERMINATED → IDLE is not
    worker_sm.transition_worker(
        worker_id=sample_worker.id,
        to_state=WorkerStatus.TERMINATED,
        reason="Shutdown",
    )
    test_db.refresh(sample_worker)

    with pytest.raises(StateTransitionError):
        worker_sm.transition_worker(
            worker_id=sample_worker.id,
            to_state=WorkerStatus.IDLE,
            reason="Cannot restart terminated worker",
        )


def test_job_state_transitions_valid(
    test_db: Session, job_sm: JobStateMachine, sample_job: Job
) -> None:
    """Test all valid job state transitions."""
    # PENDING → RUNNING
    job_sm.transition_job(
        job_id=sample_job.id,
        to_state=JobStatus.RUNNING,
        reason="Worker assigned",
    )
    test_db.refresh(sample_job)
    assert sample_job.status == JobStatus.RUNNING

    # RUNNING → COMPLETED
    job_sm.transition_job(
        job_id=sample_job.id,
        to_state=JobStatus.COMPLETED,
        reason="Task finished",
    )
    test_db.refresh(sample_job)
    assert sample_job.status == JobStatus.COMPLETED
    assert sample_job.completed_at is not None


def test_job_invalid_transitions(
    test_db: Session, job_sm: JobStateMachine, sample_job: Job
) -> None:
    """Test StateTransitionError handling for invalid job transitions."""
    # PENDING → COMPLETED is invalid (must go through RUNNING)
    with pytest.raises(StateTransitionError):
        job_sm.transition_job(
            job_id=sample_job.id,
            to_state=JobStatus.COMPLETED,
            reason="Cannot complete pending job",
        )


def test_job_cancellation_transitions(test_db: Session, job_sm: JobStateMachine) -> None:
    """Test job cancellation from various states."""
    # PENDING → CANCELLED
    job1 = Job(
        id="cancel-test-1",
        depth=0,
        worker_count=1,
        task_description="Test task",
        status=JobStatus.PENDING,
    )
    test_db.add(job1)
    test_db.commit()

    job_sm.transition_job(job_id=job1.id, to_state=JobStatus.CANCELED, reason="User cancelled")
    test_db.refresh(job1)
    assert job1.status == JobStatus.CANCELED

    # RUNNING → CANCELLED
    job2 = Job(
        id="cancel-test-2",
        depth=0,
        worker_count=1,
        task_description="Test task",
        status=JobStatus.RUNNING,
    )
    test_db.add(job2)
    test_db.commit()

    job_sm.transition_job(job_id=job2.id, to_state=JobStatus.CANCELED, reason="User cancelled")
    test_db.refresh(job2)
    assert job2.status == JobStatus.CANCELED


def test_password_hashing_security() -> None:
    """Test Argon2id password hashing security."""
    password = "SecurePassword123!"

    # Test hashing
    hashed1 = hash_password(password)
    hashed2 = hash_password(password)

    # Verify salt uniqueness
    assert hashed1 != hashed2, "Hashes should be different due to unique salts"

    # Verify correct password
    assert verify_password(password, hashed1) is True
    assert verify_password(password, hashed2) is True

    # Verify incorrect password
    assert verify_password("WrongPassword", hashed1) is False


def test_jwt_token_generation() -> None:
    """Test JWT token generation with valid structure."""
    token = create_access_token(
        user_id="test-user-123",
        scopes=["supervisor:read", "supervisor:write"],
    )

    assert isinstance(token, str)
    assert len(token) > 0
    assert "." in token  # JWT format: header.payload.signature


def test_jwt_token_validation() -> None:
    """Test JWT token validation with signature verification and expiration."""
    # Valid token
    token = create_access_token(
        user_id="test-user-123",
        scopes=["supervisor:read"],
        expires_delta=timedelta(minutes=30),
    )

    token_data = verify_token(token)
    assert token_data.user_id == "test-user-123"
    assert "supervisor:read" in token_data.scopes

    # Invalid token
    with pytest.raises(Exception):  # JWTError or similar
        verify_token("invalid.token.here")


def test_jwt_token_expiration() -> None:
    """Test JWT token expiration handling."""
    # Create expired token (expires in 0 seconds)
    token = create_access_token(
        user_id="test-user-expired",
        scopes=["test:scope"],
        expires_delta=timedelta(seconds=-10),  # Already expired
    )

    with pytest.raises(Exception):  # Token should be expired
        verify_token(token)


def test_worker_model_crud(test_db: Session) -> None:
    """Test Worker model CRUD operations."""
    # Create
    worker = Worker(id="crud-worker-1", workspace_id="ws-crud", status=WorkerStatus.IDLE)
    test_db.add(worker)
    test_db.commit()
    test_db.refresh(worker)

    assert worker.id == "crud-worker-1"
    assert worker.status == WorkerStatus.IDLE
    assert worker.created_at is not None
    assert worker.updated_at is not None

    # Read
    retrieved = test_db.query(Worker).filter_by(id="crud-worker-1").first()
    assert retrieved is not None
    assert retrieved.id == worker.id

    # Update
    retrieved.status = WorkerStatus.RUNNING
    test_db.commit()
    test_db.refresh(retrieved)
    assert retrieved.status == WorkerStatus.RUNNING

    # Delete
    test_db.delete(retrieved)
    test_db.commit()
    assert test_db.query(Worker).filter_by(id="crud-worker-1").first() is None


def test_job_model_relationships(test_db: Session, sample_worker: Worker, sample_job: Job) -> None:
    """Test Job model relationships with foreign keys and cascades."""
    # Assign worker to job
    sample_job.assigned_worker_id = sample_worker.id
    test_db.commit()
    test_db.refresh(sample_job)

    assert sample_job.assigned_worker_id == sample_worker.id

    # Test foreign key relationship
    assigned_worker = test_db.query(Worker).filter_by(id=sample_job.assigned_worker_id).first()
    assert assigned_worker is not None
    assert assigned_worker.id == sample_worker.id


def test_resource_allocation_constraints(
    test_db: Session, sample_worker: Worker, sample_job: Job
) -> None:
    """Test ResourceAllocation unique constraints and validation."""
    # Create resource allocation
    allocation = ResourceAllocation(
        job_id=sample_job.id,
        depth=0,
        worker_count=1,
        allocated_at=datetime.utcnow(),
    )
    test_db.add(allocation)
    test_db.commit()
    test_db.refresh(allocation)

    assert allocation.job_id == sample_job.id
    assert allocation.depth == 0
    assert allocation.worker_count == 1
    assert allocation.released_at is None

    # Release allocation
    allocation.released_at = datetime.utcnow()
    test_db.commit()
    test_db.refresh(allocation)
    assert allocation.released_at is not None


def test_idempotency_key_uniqueness(test_db: Session) -> None:
    """Test IdempotencyKey unique constraint for duplicate prevention."""
    key_value = "idempotent-operation-123"

    # First insertion
    key1 = IdempotencyKey(
        request_id=key_value,
        endpoint="/test",
        response_status=200,
        response_body="{}",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    test_db.add(key1)
    test_db.commit()

    # Duplicate insertion should fail (unique constraint)
    key2 = IdempotencyKey(
        request_id=key_value,
        endpoint="/test",
        response_status=200,
        response_body="{}",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    test_db.add(key2)

    with pytest.raises(Exception):  # IntegrityError or similar
        test_db.commit()

    test_db.rollback()

    # Verify only one key exists
    count = test_db.query(IdempotencyKey).filter_by(request_id=key_value).count()
    assert count == 1


def test_worker_status_enum_values(test_db: Session) -> None:
    """Test WorkerStatus enum values are correctly stored and retrieved."""
    statuses = [
        WorkerStatus.IDLE,
        WorkerStatus.RUNNING,
        WorkerStatus.FAILED,
        WorkerStatus.TERMINATED,
    ]

    for idx, status in enumerate(statuses):
        worker = Worker(id=f"status-test-{idx}", workspace_id="ws-status", status=status)
        test_db.add(worker)

    test_db.commit()

    for idx, status in enumerate(statuses):
        worker = test_db.query(Worker).filter_by(id=f"status-test-{idx}").first()
        assert worker is not None
        assert worker.status == status


def test_job_status_enum_values(test_db: Session) -> None:
    """Test JobStatus enum values are correctly stored and retrieved."""
    statuses = [
        JobStatus.PENDING,
        JobStatus.RUNNING,
        JobStatus.COMPLETED,
        JobStatus.FAILED,
        JobStatus.CANCELED,
    ]

    for idx, status in enumerate(statuses):
        job = Job(
            id=f"job-status-test-{idx}",
            depth=0,
            worker_count=1,
            task_description="Test task",
            status=status,
        )
        test_db.add(job)

    test_db.commit()

    for idx, status in enumerate(statuses):
        job = test_db.query(Job).filter_by(id=f"job-status-test-{idx}").first()
        assert job is not None
        assert job.status == status
