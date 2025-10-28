"""Unit tests for state machine module.

Tests worker and job state transitions, validation, and error handling.
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from orchestrator.core.state_machine import (
    WorkerStateMachine,
    JobStateMachine,
    StateTransitionError,
    EntityNotFoundError,
    WORKER_TRANSITIONS,
    JOB_TRANSITIONS,
)
from orchestrator.core.db_models import (
    Worker,
    WorkerStatus,
    WorkerStateTransition,
    Job,
    JobStatus,
    JobStateTransition,
)
from orchestrator.core.database import SessionLocal, init_db, drop_all_tables


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Only drop/create if tables don't exist
    try:
        session = SessionLocal()
        # Test if tables exist
        session.execute("SELECT 1 FROM workers LIMIT 1")
    except:
        drop_all_tables()
        init_db()
    finally:
        session = SessionLocal()

    yield session

    # Clean up test data but don't drop tables
    session.query(WorkerStateTransition).delete()
    session.query(JobStateTransition).delete()
    session.query(Worker).delete()
    session.query(Job).delete()
    session.commit()
    session.close()


@pytest.fixture
def sample_worker(db_session):
    """Create a sample worker for testing."""
    worker = Worker(
        id="test-worker-001",
        workspace_id="test-workspace",
        status=WorkerStatus.IDLE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(worker)
    db_session.commit()
    db_session.refresh(worker)
    return worker


@pytest.fixture
def sample_job(db_session):
    """Create a sample job for testing."""
    job = Job(
        id="test-job-001",
        task_description="Test task",
        status=JobStatus.PENDING,
        depth=0,
        worker_count=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


# ======================= Worker State Machine Tests =======================


class TestWorkerStateMachine:
    """Test WorkerStateMachine functionality."""

    def test_can_transition_valid(self, db_session):
        """Test can_transition returns True for valid transitions."""
        sm = WorkerStateMachine(db_session)

        assert sm.can_transition(WorkerStatus.IDLE, WorkerStatus.RUNNING) is True
        assert sm.can_transition(WorkerStatus.RUNNING, WorkerStatus.PAUSED) is True
        assert sm.can_transition(WorkerStatus.PAUSED, WorkerStatus.RUNNING) is True

    def test_can_transition_invalid(self, db_session):
        """Test can_transition returns False for invalid transitions."""
        sm = WorkerStateMachine(db_session)

        # Final states cannot transition
        assert sm.can_transition(WorkerStatus.COMPLETED, WorkerStatus.RUNNING) is False
        assert sm.can_transition(WorkerStatus.FAILED, WorkerStatus.RUNNING) is False
        assert sm.can_transition(WorkerStatus.TERMINATED, WorkerStatus.RUNNING) is False

    def test_transition_worker_success(self, db_session, sample_worker):
        """Test successful worker state transition."""
        sm = WorkerStateMachine(db_session)

        worker = sm.transition_worker(
            worker_id=sample_worker.id,
            to_state=WorkerStatus.RUNNING,
            reason="Test transition"
        )

        assert worker.status == WorkerStatus.RUNNING
        assert worker.updated_at is not None

    def test_transition_worker_logs_audit_trail(self, db_session, sample_worker):
        """Test that transitions are logged to audit trail."""
        sm = WorkerStateMachine(db_session)

        sm.transition_worker(
            worker_id=sample_worker.id,
            to_state=WorkerStatus.RUNNING,
            reason="Test audit"
        )

        # Check audit trail
        transitions = db_session.query(WorkerStateTransition).filter(
            WorkerStateTransition.worker_id == sample_worker.id
        ).all()

        assert len(transitions) == 1
        assert transitions[0].from_state == WorkerStatus.IDLE.value
        assert transitions[0].to_state == WorkerStatus.RUNNING.value
        assert transitions[0].reason == "Test audit"

    def test_transition_worker_nonexistent_raises_error(self, db_session):
        """Test transitioning non-existent worker raises EntityNotFoundError."""
        sm = WorkerStateMachine(db_session)

        with pytest.raises(EntityNotFoundError, match="Worker not found"):
            sm.transition_worker(
                worker_id="nonexistent-worker",
                to_state=WorkerStatus.RUNNING
            )

    def test_transition_worker_invalid_transition_raises_error(self, db_session, sample_worker):
        """Test invalid transition raises StateTransitionError."""
        sm = WorkerStateMachine(db_session)

        # Transition to COMPLETED (final state)
        sm.transition_worker(
            worker_id=sample_worker.id,
            to_state=WorkerStatus.TERMINATED
        )

        # Try to transition from final state
        with pytest.raises(StateTransitionError) as exc_info:
            sm.transition_worker(
                worker_id=sample_worker.id,
                to_state=WorkerStatus.RUNNING
            )

        assert exc_info.value.from_state == WorkerStatus.TERMINATED.value
        assert exc_info.value.to_state == WorkerStatus.RUNNING.value
        assert exc_info.value.entity_id == sample_worker.id

    def test_get_transition_history(self, db_session, sample_worker):
        """Test getting worker transition history."""
        sm = WorkerStateMachine(db_session)

        # Create multiple transitions
        sm.transition_worker(sample_worker.id, WorkerStatus.RUNNING, "Start")
        sm.transition_worker(sample_worker.id, WorkerStatus.PAUSED, "Pause")
        sm.transition_worker(sample_worker.id, WorkerStatus.RUNNING, "Resume")

        history = sm.get_transition_history(sample_worker.id, limit=10)

        assert len(history) == 3
        # Newest first
        assert history[0].to_state == WorkerStatus.RUNNING.value
        assert history[0].reason == "Resume"
        assert history[2].to_state == WorkerStatus.RUNNING.value
        assert history[2].reason == "Start"

    def test_get_transition_history_with_limit(self, db_session, sample_worker):
        """Test transition history respects limit."""
        sm = WorkerStateMachine(db_session)

        # Create multiple transitions
        sm.transition_worker(sample_worker.id, WorkerStatus.RUNNING)
        sm.transition_worker(sample_worker.id, WorkerStatus.PAUSED)
        sm.transition_worker(sample_worker.id, WorkerStatus.RUNNING)

        history = sm.get_transition_history(sample_worker.id, limit=2)

        assert len(history) == 2


# ======================= Job State Machine Tests =======================


class TestJobStateMachine:
    """Test JobStateMachine functionality."""

    def test_can_transition_valid(self, db_session):
        """Test can_transition returns True for valid transitions."""
        sm = JobStateMachine(db_session)

        assert sm.can_transition(JobStatus.PENDING, JobStatus.RUNNING) is True
        assert sm.can_transition(JobStatus.RUNNING, JobStatus.COMPLETED) is True
        assert sm.can_transition(JobStatus.RUNNING, JobStatus.FAILED) is True

    def test_can_transition_invalid(self, db_session):
        """Test can_transition returns False for invalid transitions."""
        sm = JobStateMachine(db_session)

        # Final states cannot transition
        assert sm.can_transition(JobStatus.COMPLETED, JobStatus.RUNNING) is False
        assert sm.can_transition(JobStatus.FAILED, JobStatus.RUNNING) is False
        assert sm.can_transition(JobStatus.CANCELED, JobStatus.RUNNING) is False

    def test_transition_job_success(self, db_session, sample_job):
        """Test successful job state transition."""
        sm = JobStateMachine(db_session)

        job = sm.transition_job(
            job_id=sample_job.id,
            to_state=JobStatus.RUNNING,
            reason="Test transition"
        )

        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None

    def test_transition_job_sets_started_at(self, db_session, sample_job):
        """Test that transitioning to RUNNING sets started_at."""
        sm = JobStateMachine(db_session)

        assert sample_job.started_at is None

        job = sm.transition_job(
            job_id=sample_job.id,
            to_state=JobStatus.RUNNING
        )

        assert job.started_at is not None

    def test_transition_job_sets_completed_at(self, db_session, sample_job):
        """Test that transitioning to final states sets completed_at."""
        sm = JobStateMachine(db_session)

        # Transition to RUNNING first
        sm.transition_job(sample_job.id, JobStatus.RUNNING)

        assert sample_job.completed_at is None

        # Transition to COMPLETED
        job = sm.transition_job(sample_job.id, JobStatus.COMPLETED)

        assert job.completed_at is not None

    def test_transition_job_logs_audit_trail(self, db_session, sample_job):
        """Test that job transitions are logged to audit trail."""
        sm = JobStateMachine(db_session)

        sm.transition_job(
            job_id=sample_job.id,
            to_state=JobStatus.RUNNING,
            reason="Test audit"
        )

        # Check audit trail
        transitions = db_session.query(JobStateTransition).filter(
            JobStateTransition.job_id == sample_job.id
        ).all()

        assert len(transitions) == 1
        assert transitions[0].from_state == JobStatus.PENDING.value
        assert transitions[0].to_state == JobStatus.RUNNING.value
        assert transitions[0].reason == "Test audit"

    def test_transition_job_nonexistent_raises_error(self, db_session):
        """Test transitioning non-existent job raises EntityNotFoundError."""
        sm = JobStateMachine(db_session)

        with pytest.raises(EntityNotFoundError, match="Job not found"):
            sm.transition_job(
                job_id="nonexistent-job",
                to_state=JobStatus.RUNNING
            )

    def test_transition_job_invalid_transition_raises_error(self, db_session, sample_job):
        """Test invalid job transition raises StateTransitionError."""
        sm = JobStateMachine(db_session)

        # Transition to RUNNING then COMPLETED (final state)
        sm.transition_job(sample_job.id, JobStatus.RUNNING)
        sm.transition_job(sample_job.id, JobStatus.COMPLETED)

        # Try to transition from final state
        with pytest.raises(StateTransitionError) as exc_info:
            sm.transition_job(
                job_id=sample_job.id,
                to_state=JobStatus.RUNNING
            )

        assert exc_info.value.from_state == JobStatus.COMPLETED.value
        assert exc_info.value.to_state == JobStatus.RUNNING.value
        assert exc_info.value.entity_id == sample_job.id

    def test_cancel_job(self, db_session, sample_job):
        """Test cancel_job convenience method."""
        sm = JobStateMachine(db_session)

        job = sm.cancel_job(
            job_id=sample_job.id,
            reason="User requested cancellation"
        )

        assert job.status == JobStatus.CANCELED
        assert job.completed_at is not None

    def test_cancel_job_default_reason(self, db_session, sample_job):
        """Test cancel_job with default reason."""
        sm = JobStateMachine(db_session)

        sm.cancel_job(job_id=sample_job.id)

        transitions = db_session.query(JobStateTransition).filter(
            JobStateTransition.job_id == sample_job.id
        ).all()

        assert transitions[0].reason == "Job canceled"

    def test_get_transition_history(self, db_session, sample_job):
        """Test getting job transition history."""
        sm = JobStateMachine(db_session)

        # Create multiple transitions
        sm.transition_job(sample_job.id, JobStatus.RUNNING, "Start")
        sm.transition_job(sample_job.id, JobStatus.COMPLETED, "Done")

        history = sm.get_transition_history(sample_job.id, limit=10)

        assert len(history) == 2
        # Newest first
        assert history[0].to_state == JobStatus.COMPLETED.value
        assert history[0].reason == "Done"
        assert history[1].to_state == JobStatus.RUNNING.value
        assert history[1].reason == "Start"

    def test_get_transition_history_with_limit(self, db_session, sample_job):
        """Test job transition history respects limit."""
        sm = JobStateMachine(db_session)

        # Create multiple transitions
        sm.transition_job(sample_job.id, JobStatus.RUNNING)
        sm.transition_job(sample_job.id, JobStatus.FAILED)

        history = sm.get_transition_history(sample_job.id, limit=1)

        assert len(history) == 1
        assert history[0].to_state == JobStatus.FAILED.value


# ======================= Exception Tests =======================


class TestExceptions:
    """Test custom exceptions."""

    def test_state_transition_error_default_message(self):
        """Test StateTransitionError with default message."""
        error = StateTransitionError(
            from_state="IDLE",
            to_state="COMPLETED",
            entity_id="w_123"
        )

        assert "Invalid state transition" in str(error)
        assert "IDLE" in str(error)
        assert "COMPLETED" in str(error)
        assert error.from_state == "IDLE"
        assert error.to_state == "COMPLETED"
        assert error.entity_id == "w_123"

    def test_state_transition_error_custom_message(self):
        """Test StateTransitionError with custom message."""
        error = StateTransitionError(
            from_state="IDLE",
            to_state="COMPLETED",
            entity_id="w_123",
            message="Custom error message"
        )

        assert str(error) == "Custom error message"

    def test_entity_not_found_error(self):
        """Test EntityNotFoundError."""
        error = EntityNotFoundError("Worker", "w_123")

        assert "Worker not found: w_123" in str(error)
