"""
State machine module for worker and job lifecycle management.

Provides explicit state transition validation and audit trail logging.
Uses simple Enum - based approach for clarity and maintainability.

Security:
- SQL parameterization via SQLAlchemy ORM
- No direct state manipulation without validation

Type Safety:
- Explicit type annotations on all functions
- Enum types for state definitions

Usage:
    from orchestrator.core.state_machine import WorkerStateMachine
    from orchestrator.core.database import SessionLocal

    db = SessionLocal()
    sm = WorkerStateMachine(db)

    # Transition worker state with validation
    worker = sm.transition_worker(
        worker_id="w_abc123",
        to_state=WorkerStatus.RUNNING,
        reason="User started worker"
    )
"""

from datetime import datetime
from typing import Dict, Optional, Set

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from orchestrator.core.db_models import (
    Job,
    JobStateTransition,
    JobStatus,
    Worker,
    WorkerStateTransition,
    WorkerStatus,
)

# ============================================================================
# State Transition Definitions
# ============================================================================

# Valid worker state transitions (from_state -> {allowed_to_states})
WORKER_TRANSITIONS: Dict[WorkerStatus, Set[WorkerStatus]] = {
    WorkerStatus.IDLE: {
        WorkerStatus.RUNNING,
        WorkerStatus.TERMINATED,
    },
    WorkerStatus.RUNNING: {
        WorkerStatus.PAUSED,
        WorkerStatus.COMPLETED,
        WorkerStatus.FAILED,
        WorkerStatus.TERMINATED,
    },
    WorkerStatus.PAUSED: {
        WorkerStatus.RUNNING,
        WorkerStatus.TERMINATED,
    },
    WorkerStatus.COMPLETED: set(),  # Final state
    WorkerStatus.FAILED: set(),  # Final state
    WorkerStatus.TERMINATED: set(),  # Final state
}

# Valid job state transitions
JOB_TRANSITIONS: Dict[JobStatus, Set[JobStatus]] = {
    JobStatus.SUBMITTED: {
        JobStatus.PENDING,
        JobStatus.CANCELED,
    },
    JobStatus.PENDING: {
        JobStatus.RUNNING,
        JobStatus.CANCELED,
    },
    JobStatus.RUNNING: {
        JobStatus.COMPLETED,
        JobStatus.FAILED,
        JobStatus.CANCELED,
    },
    JobStatus.COMPLETED: set(),  # Final state
    JobStatus.FAILED: set(),  # Final state
    JobStatus.CANCELED: set(),  # Final state
}


# ============================================================================
# Custom Exceptions
# ============================================================================


class StateTransitionError(Exception):
    """
    Raised when state transition is invalid.

    Attributes:
        from_state: Current state
        to_state: Attempted target state
        entity_id: Worker or job identifier
    """

    def __init__(
        self, from_state: str, to_state: str, entity_id: str, message: Optional[str] = None
    ):
        """Initialize state transition error."""
        self.from_state = from_state
        self.to_state = to_state
        self.entity_id = entity_id

        if message is None:
            message = f"Invalid state transition for {entity_id}: " f"{from_state} → {to_state}"

        super().__init__(message)


class EntityNotFoundError(Exception):
    """Raised when worker or job not found in database."""

    def __init__(self, entity_type: str, entity_id: str):
        """Initialize entity not found error."""
        super().__init__(f"{entity_type} not found: {entity_id}")


# ============================================================================
# Worker State Machine
# ============================================================================


class WorkerStateMachine:
    """
    Worker state machine with transition validation.

    Manages worker lifecycle states with explicit validation and
    audit trail logging. Uses simple Enum - based approach.

    Example:
        >>> sm = WorkerStateMachine(db_session)
        >>> worker = sm.transition_worker(
        ...     worker_id="w_abc123",
        ...     to_state=WorkerStatus.RUNNING
        ... )
        >>> worker.status  # WorkerStatus.RUNNING
    """

    def __init__(self, db: Session):
        """
        Initialize worker state machine.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def can_transition(self, from_state: WorkerStatus, to_state: WorkerStatus) -> bool:
        """
        Check if state transition is valid.

        Args:
            from_state: Current worker status
            to_state: Target worker status

        Returns:
            True if transition is allowed, False otherwise

        Example:
            >>> sm.can_transition(WorkerStatus.IDLE, WorkerStatus.RUNNING)
            True
            >>> sm.can_transition(WorkerStatus.COMPLETED, WorkerStatus.RUNNING)
            False
        """
        allowed_states = WORKER_TRANSITIONS.get(from_state, set())
        return to_state in allowed_states

    def transition_worker(
        self, worker_id: str, to_state: WorkerStatus, reason: Optional[str] = None
    ) -> Worker:
        """
        Transition worker to new state with validation.

        Validates transition, updates worker status, and logs to audit trail.

        Args:
            worker_id: Worker identifier
            to_state: Target state
            reason: Optional reason for transition

        Returns:
            Updated worker instance

        Raises:
            EntityNotFoundError: If worker not found
            StateTransitionError: If transition invalid
            SQLAlchemyError: If database operation fails

        Example:
            >>> worker = sm.transition_worker(
            ...     "w_abc123",
            ...     WorkerStatus.PAUSED,
            ...     reason="User paused worker"
            ... )
        """
        # Fetch worker
        worker = self.db.query(Worker).filter(Worker.id == worker_id).first()

        if not worker:
            raise EntityNotFoundError("Worker", worker_id)

        # Validate transition
        if not self.can_transition(worker.status, to_state):
            raise StateTransitionError(
                from_state=worker.status.value, to_state=to_state.value, entity_id=worker_id
            )

        # Record old state
        from_state = worker.status

        # Update worker status
        worker.status = to_state
        worker.updated_at = datetime.utcnow()

        # Log transition to audit trail
        transition = WorkerStateTransition(
            worker_id=worker_id,
            from_state=from_state.value,
            to_state=to_state.value,
            reason=reason,
            timestamp=datetime.utcnow(),
        )
        self.db.add(transition)

        # Commit transaction
        try:
            self.db.commit()
            self.db.refresh(worker)
        except SQLAlchemyError:
            self.db.rollback()
            raise

        return worker

    def get_transition_history(
        self, worker_id: str, limit: int = 50
    ) -> list[WorkerStateTransition]:
        """
        Get worker state transition history.

        Args:
            worker_id: Worker identifier
            limit: Maximum number of transitions to return

        Returns:
            List of state transitions (newest first)

        Example:
            >>> history = sm.get_transition_history("w_abc123", limit=10)
            >>> history[0].to_state  # Most recent state
        """
        return (
            self.db.query(WorkerStateTransition)
            .filter(WorkerStateTransition.worker_id == worker_id)
            .order_by(WorkerStateTransition.timestamp.desc())
            .limit(limit)
            .all()
        )


# ============================================================================
# Job State Machine
# ============================================================================


class JobStateMachine:
    """
    Job state machine with transition validation.

    Manages job lifecycle states with explicit validation and
    audit trail logging.

    Example:
        >>> sm = JobStateMachine(db_session)
        >>> job = sm.transition_job(
        ...     job_id="j_xyz789",
        ...     to_state=JobStatus.RUNNING
        ... )
    """

    def __init__(self, db: Session):
        """
        Initialize job state machine.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def can_transition(self, from_state: JobStatus, to_state: JobStatus) -> bool:
        """
        Check if state transition is valid.

        Args:
            from_state: Current job status
            to_state: Target job status

        Returns:
            True if transition is allowed, False otherwise

        Example:
            >>> sm.can_transition(JobStatus.PENDING, JobStatus.RUNNING)
            True
            >>> sm.can_transition(JobStatus.COMPLETED, JobStatus.RUNNING)
            False
        """
        allowed_states = JOB_TRANSITIONS.get(from_state, set())
        return to_state in allowed_states

    def transition_job(self, job_id: str, to_state: JobStatus, reason: Optional[str] = None) -> Job:
        """
        Transition job to new state with validation.

        Validates transition, updates job status, and logs to audit trail.
        Also updates started_at / completed_at timestamps as appropriate.

        Args:
            job_id: Job identifier
            to_state: Target state
            reason: Optional reason for transition

        Returns:
            Updated job instance

        Raises:
            EntityNotFoundError: If job not found
            StateTransitionError: If transition invalid
            SQLAlchemyError: If database operation fails

        Example:
            >>> job = sm.transition_job(
            ...     "j_xyz789",
            ...     JobStatus.RUNNING,
            ...     reason="Resources allocated"
            ... )
        """
        # Fetch job
        job = self.db.query(Job).filter(Job.id == job_id).first()

        if not job:
            raise EntityNotFoundError("Job", job_id)

        # Validate transition
        if not self.can_transition(job.status, to_state):
            raise StateTransitionError(
                from_state=job.status.value, to_state=to_state.value, entity_id=job_id
            )

        # Record old state
        from_state = job.status

        # Update job status
        job.status = to_state

        # Update timestamps based on state
        now = datetime.utcnow()
        if to_state == JobStatus.RUNNING and job.started_at is None:
            job.started_at = now  # type: ignore[unreachable]
        elif (
            to_state in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELED}
            and job.completed_at is None
        ):
            job.completed_at = now  # type: ignore[unreachable]

        # Log transition to audit trail
        transition = JobStateTransition(
            job_id=job_id,
            from_state=from_state.value,
            to_state=to_state.value,
            reason=reason,
            timestamp=now,
        )
        self.db.add(transition)

        # Commit transaction
        try:
            self.db.commit()
            self.db.refresh(job)
        except SQLAlchemyError:
            self.db.rollback()
            raise

        return job

    def cancel_job(self, job_id: str, reason: Optional[str] = None) -> Job:
        """
        Cancel a job by transitioning to CANCELED state.

        Args:
            job_id: Job identifier
            reason: Optional reason for cancellation

        Returns:
            Updated job instance

        Raises:
            EntityNotFoundError: If job not found
            StateTransitionError: If cancellation not allowed from current state

        Example:
            >>> job = sm.cancel_job("j_xyz789", reason="User requested cancellation")
        """
        return self.transition_job(
            job_id=job_id, to_state=JobStatus.CANCELED, reason=reason or "Job canceled"
        )

    def get_transition_history(self, job_id: str, limit: int = 50) -> list[JobStateTransition]:
        """
        Get job state transition history.

        Args:
            job_id: Job identifier
            limit: Maximum number of transitions to return

        Returns:
            List of state transitions (newest first)

        Example:
            >>> history = sm.get_transition_history("j_xyz789", limit=10)
            >>> history[0].to_state  # Most recent state
        """
        return (
            self.db.query(JobStateTransition)
            .filter(JobStateTransition.job_id == job_id)
            .order_by(JobStateTransition.timestamp.desc())
            .limit(limit)
            .all()
        )
