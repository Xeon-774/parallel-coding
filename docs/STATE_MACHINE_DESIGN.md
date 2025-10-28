# State Machine Design - Week 2 MVP

**Document Version**: 1.0
**Created**: 2025-10-28
**Status**: Active

---

## Executive Summary

This document defines the state machines for Worker and Job lifecycle management in the Week 2 MVP. It includes state transition rules, validation logic, idempotency handling, and error recovery strategies.

**Key Design Principles**:
- **Deterministic transitions**: All state changes follow predefined rules
- **Idempotency**: Request IDs prevent duplicate operations
- **Audit trail**: All transitions logged with timestamps and reasons
- **Error recovery**: Failed states have clear recovery paths

---

## 1. Worker State Machine

### 1.1 States

| State | Description | Terminal |
|-------|-------------|----------|
| IDLE | Worker created but not yet assigned tasks | No |
| RUNNING | Worker actively executing tasks | No |
| PAUSED | Worker temporarily suspended by supervisor | No |
| COMPLETED | Worker finished all tasks successfully | Yes |
| FAILED | Worker encountered unrecoverable error | Yes |
| TERMINATED | Worker forcefully stopped by supervisor | Yes |

### 1.2 State Transition Diagram

```
┌─────────┐
│  IDLE   │──────────────────┐
└─────────┘                  │
     │                       │
     │ start_task           │ terminate
     ▼                       ▼
┌─────────┐  pause      ┌────────────┐
│ RUNNING │────────────▶│   PAUSED   │
└─────────┘             └────────────┘
     │                       │
     │ resume                │
     │◀──────────────────────┘
     │
     │ error_unrecoverable   │ complete_tasks
     ▼                       ▼
┌─────────┐             ┌────────────┐
│ FAILED  │             │ COMPLETED  │
└─────────┘             └────────────┘
     │                       │
     │ (any state)           │
     └───────────────────────┴──▶ TERMINATED
```

### 1.3 Transition Rules

| From State | To State | Trigger | Conditions | Validation |
|------------|----------|---------|------------|------------|
| IDLE | RUNNING | start_task | Task assigned | Worker has capacity |
| RUNNING | PAUSED | pause | Supervisor request | Worker not in terminal state |
| PAUSED | RUNNING | resume | Supervisor request | Worker was previously RUNNING |
| RUNNING | COMPLETED | complete_tasks | All tasks done | No pending tasks |
| RUNNING | FAILED | error_unrecoverable | Critical error | Error is not retryable |
| * | TERMINATED | terminate | Supervisor command | Any state (force stop) |

### 1.4 Invalid Transitions

The following transitions are **forbidden** and will return `409 Conflict`:

- IDLE → PAUSED (cannot pause worker that hasn't started)
- IDLE → COMPLETED (cannot complete without running)
- COMPLETED → RUNNING (cannot restart completed worker)
- COMPLETED → PAUSED (terminal state)
- FAILED → RUNNING (terminal state, create new worker instead)
- TERMINATED → * (terminal state, no transitions allowed)

### 1.5 Implementation Example

```python
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class WorkerState(str, Enum):
    """Worker state enumeration."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"

class StateTransitionRequest(BaseModel):
    """Request to transition worker state."""
    worker_id: str = Field(..., description="Worker identifier")
    to_state: WorkerState = Field(..., description="Target state")
    reason: Optional[str] = Field(None, description="Reason for transition")
    request_id: Optional[str] = Field(None, description="Idempotency key")

class StateTransitionResult(BaseModel):
    """Result of state transition."""
    worker_id: str
    from_state: WorkerState
    to_state: WorkerState
    timestamp: datetime
    success: bool
    error: Optional[str] = None

class WorkerStateMachine:
    """Worker state machine implementation."""

    # Valid transitions map
    VALID_TRANSITIONS: Dict[WorkerState, set[WorkerState]] = {
        WorkerState.IDLE: {WorkerState.RUNNING, WorkerState.TERMINATED},
        WorkerState.RUNNING: {
            WorkerState.PAUSED,
            WorkerState.COMPLETED,
            WorkerState.FAILED,
            WorkerState.TERMINATED,
        },
        WorkerState.PAUSED: {WorkerState.RUNNING, WorkerState.TERMINATED},
        WorkerState.COMPLETED: set(),  # Terminal state
        WorkerState.FAILED: set(),  # Terminal state
        WorkerState.TERMINATED: set(),  # Terminal state
    }

    @classmethod
    def is_valid_transition(
        cls, from_state: WorkerState, to_state: WorkerState
    ) -> bool:
        """
        Check if state transition is valid.

        Args:
            from_state: Current worker state
            to_state: Target worker state

        Returns:
            True if transition is allowed
        """
        return to_state in cls.VALID_TRANSITIONS.get(from_state, set())

    @classmethod
    def is_terminal_state(cls, state: WorkerState) -> bool:
        """
        Check if state is terminal (no further transitions).

        Args:
            state: Worker state to check

        Returns:
            True if state is terminal
        """
        return state in {
            WorkerState.COMPLETED,
            WorkerState.FAILED,
            WorkerState.TERMINATED,
        }

    @classmethod
    def validate_transition(
        cls, from_state: WorkerState, to_state: WorkerState
    ) -> Optional[str]:
        """
        Validate state transition and return error message if invalid.

        Args:
            from_state: Current state
            to_state: Target state

        Returns:
            Error message if invalid, None if valid
        """
        if from_state == to_state:
            return f"Worker already in {to_state} state"

        if cls.is_terminal_state(from_state):
            return (
                f"Cannot transition from terminal state {from_state} "
                f"to {to_state}"
            )

        if not cls.is_valid_transition(from_state, to_state):
            return (
                f"Invalid state transition: {from_state} → {to_state}. "
                f"Allowed transitions from {from_state}: "
                f"{cls.VALID_TRANSITIONS.get(from_state, set())}"
            )

        return None
```

---

## 2. Job State Machine

### 2.1 States

| State | Description | Terminal |
|-------|-------------|----------|
| SUBMITTED | Job received but not yet validated | No |
| PENDING | Job validated, waiting for resources | No |
| RUNNING | Job executing with allocated resources | No |
| COMPLETED | Job finished successfully | Yes |
| FAILED | Job failed due to error | Yes |
| CANCELED | Job canceled by user/system | Yes |

### 2.2 State Transition Diagram

```
┌───────────┐
│ SUBMITTED │
└───────────┘
     │
     │ validate
     ▼
┌───────────┐  cancel
│  PENDING  │─────────────────┐
└───────────┘                 │
     │                        │
     │ allocate_resources     │
     ▼                        ▼
┌───────────┐  cancel    ┌───────────┐
│  RUNNING  │───────────▶│ CANCELED  │
└───────────┘            └───────────┘
     │
     │ error              │ success
     ▼                    ▼
┌───────────┐        ┌────────────┐
│  FAILED   │        │ COMPLETED  │
└───────────┘        └────────────┘
```

### 2.3 Transition Rules

| From State | To State | Trigger | Conditions | Side Effects |
|------------|----------|---------|------------|--------------|
| SUBMITTED | PENDING | validate | Schema valid | Store job metadata |
| PENDING | RUNNING | allocate_resources | Resources available | Allocate workers |
| PENDING | CANCELED | cancel | User/system request | Release resources |
| RUNNING | COMPLETED | success | Task finished | Release resources, store result |
| RUNNING | FAILED | error | Execution error | Release resources, log error |
| RUNNING | CANCELED | cancel | User/system request | Kill workers, release resources |

### 2.4 Invalid Transitions

- SUBMITTED → RUNNING (must go through PENDING)
- COMPLETED → * (terminal state)
- FAILED → RUNNING (create new job instead)
- CANCELED → RUNNING (create new job instead)

### 2.5 Implementation Example

```python
from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

class JobState(str, Enum):
    """Job state enumeration."""
    SUBMITTED = "SUBMITTED"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"

class JobStateTransition(BaseModel):
    """Job state transition record."""
    from_state: Optional[JobState] = None
    to_state: JobState
    reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Job(BaseModel):
    """Job model with state machine."""
    id: str = Field(default_factory=lambda: f"j_{uuid.uuid4().hex[:12]}")
    status: JobState = JobState.SUBMITTED
    depth: int = Field(..., ge=0, le=5)
    parent_job_id: Optional[str] = None
    worker_count: int = Field(1, ge=1, le=10)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    state_history: List[JobStateTransition] = Field(default_factory=list)

    def transition_to(
        self, new_state: JobState, reason: Optional[str] = None
    ) -> None:
        """
        Transition job to new state.

        Args:
            new_state: Target state
            reason: Reason for transition

        Raises:
            ValueError: If transition is invalid
        """
        error = JobStateMachine.validate_transition(self.status, new_state)
        if error:
            raise ValueError(error)

        # Record transition
        transition = JobStateTransition(
            from_state=self.status, to_state=new_state, reason=reason
        )
        self.state_history.append(transition)

        # Update state
        old_state = self.status
        self.status = new_state

        # Update timestamps
        if new_state == JobState.RUNNING and not self.started_at:
            self.started_at = datetime.utcnow()
        elif JobStateMachine.is_terminal_state(new_state):
            self.completed_at = datetime.utcnow()

class JobStateMachine:
    """Job state machine logic."""

    VALID_TRANSITIONS: Dict[JobState, set[JobState]] = {
        JobState.SUBMITTED: {JobState.PENDING, JobState.CANCELED},
        JobState.PENDING: {JobState.RUNNING, JobState.CANCELED},
        JobState.RUNNING: {
            JobState.COMPLETED,
            JobState.FAILED,
            JobState.CANCELED,
        },
        JobState.COMPLETED: set(),
        JobState.FAILED: set(),
        JobState.CANCELED: set(),
    }

    @classmethod
    def is_valid_transition(
        cls, from_state: JobState, to_state: JobState
    ) -> bool:
        """Check if transition is valid."""
        return to_state in cls.VALID_TRANSITIONS.get(from_state, set())

    @classmethod
    def is_terminal_state(cls, state: JobState) -> bool:
        """Check if state is terminal."""
        return state in {
            JobState.COMPLETED,
            JobState.FAILED,
            JobState.CANCELED,
        }

    @classmethod
    def validate_transition(
        cls, from_state: JobState, to_state: JobState
    ) -> Optional[str]:
        """
        Validate transition and return error if invalid.

        Args:
            from_state: Current state
            to_state: Target state

        Returns:
            Error message or None
        """
        if from_state == to_state:
            return f"Job already in {to_state} state"

        if cls.is_terminal_state(from_state):
            return (
                f"Cannot transition from terminal state {from_state}. "
                f"Create new job instead."
            )

        if not cls.is_valid_transition(from_state, to_state):
            allowed = cls.VALID_TRANSITIONS.get(from_state, set())
            return (
                f"Invalid transition: {from_state} → {to_state}. "
                f"Allowed: {allowed}"
            )

        return None
```

---

## 3. Idempotency Handling

### 3.1 Request ID Pattern

All state-changing operations accept optional `request_id` (UUID) for idempotency.

**Implementation**:

```python
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

class IdempotencyCache:
    """
    In-memory cache for idempotent requests.

    In production, use Redis or database table.
    """

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache.

        Args:
            ttl_seconds: Time-to-live for cached requests
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl_seconds = ttl_seconds

    def check_and_store(
        self, request_id: str, result: Any
    ) -> Optional[Any]:
        """
        Check if request already processed and store result.

        Args:
            request_id: Unique request identifier
            result: Result to cache

        Returns:
            Cached result if request already processed, None otherwise
        """
        # Check if request already processed
        if request_id in self._cache:
            cached = self._cache[request_id]
            if datetime.utcnow() < cached["expires_at"]:
                return cached["result"]
            else:
                # Expired, remove from cache
                del self._cache[request_id]

        # Store new result
        self._cache[request_id] = {
            "result": result,
            "expires_at": datetime.utcnow()
            + timedelta(seconds=self._ttl_seconds),
        }

        return None

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        now = datetime.utcnow()
        expired_keys = [
            k
            for k, v in self._cache.items()
            if now >= v["expires_at"]
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)

# Usage example
idempotency_cache = IdempotencyCache()

async def pause_worker(
    worker_id: str,
    reason: Optional[str] = None,
    request_id: Optional[str] = None,
) -> WorkerDetail:
    """
    Pause worker with idempotency support.

    Args:
        worker_id: Worker to pause
        reason: Reason for pausing
        request_id: Idempotency key

    Returns:
        Updated worker details
    """
    # Check idempotency
    if request_id:
        cached = idempotency_cache.check_and_store(request_id, None)
        if cached is not None:
            return cached  # Already processed

    # Get worker
    worker = await get_worker(worker_id)

    # Validate transition
    error = WorkerStateMachine.validate_transition(
        worker.status, WorkerState.PAUSED
    )
    if error:
        raise ValueError(error)

    # Perform transition
    worker.status = WorkerState.PAUSED
    await save_worker(worker)

    # Log transition
    await log_state_transition(
        worker_id=worker_id,
        from_state=WorkerState.RUNNING,
        to_state=WorkerState.PAUSED,
        reason=reason,
    )

    # Cache result
    if request_id:
        idempotency_cache.check_and_store(request_id, worker)

    return worker
```

### 3.2 Idempotency Keys in Database

For production, store idempotency keys in database:

```sql
CREATE TABLE idempotency_keys (
    request_id VARCHAR(36) PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    response_status INTEGER NOT NULL,
    response_body TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    INDEX idx_expires_at (expires_at)
);
```

---

## 4. Error Recovery

### 4.1 Worker Error Recovery

| Error Type | Recovery Strategy | New State |
|------------|------------------|-----------|
| Transient network error | Auto-retry (3 attempts) | RUNNING |
| Resource exhaustion | Pause worker, release resources | PAUSED |
| Unrecoverable error | Mark failed, log error | FAILED |
| Supervisor timeout | Terminate worker | TERMINATED |

### 4.2 Job Error Recovery

| Error Type | Recovery Strategy | New State |
|------------|------------------|-----------|
| Worker crash | Spawn new worker, retry | RUNNING |
| Validation error | Fail immediately | FAILED |
| Timeout | Cancel job | CANCELED |
| Resource unavailable | Keep in PENDING (retry allocation) | PENDING |

---

## 5. State Persistence

### 5.1 Database Schema

```sql
-- Worker state
CREATE TABLE workers (
    id VARCHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(36) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    metadata JSONB,
    CHECK (status IN ('IDLE', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'TERMINATED'))
);

-- Worker state transitions (audit trail)
CREATE TABLE worker_state_transitions (
    id SERIAL PRIMARY KEY,
    worker_id VARCHAR(36) NOT NULL REFERENCES workers(id),
    from_state VARCHAR(20),
    to_state VARCHAR(20) NOT NULL,
    reason TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    INDEX idx_worker_id (worker_id),
    INDEX idx_timestamp (timestamp)
);

-- Job state
CREATE TABLE jobs (
    id VARCHAR(36) PRIMARY KEY,
    parent_job_id VARCHAR(36) REFERENCES jobs(id),
    depth INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    worker_count INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    task_description TEXT NOT NULL,
    CHECK (status IN ('SUBMITTED', 'PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELED')),
    CHECK (depth >= 0 AND depth <= 5)
);

-- Job state transitions (audit trail)
CREATE TABLE job_state_transitions (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL REFERENCES jobs(id),
    from_state VARCHAR(20),
    to_state VARCHAR(20) NOT NULL,
    reason TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    INDEX idx_job_id (job_id),
    INDEX idx_timestamp (timestamp)
);
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

Test all state transitions:

```python
import pytest
from state_machine import WorkerState, WorkerStateMachine

class TestWorkerStateMachine:
    """Unit tests for worker state machine."""

    def test_valid_transition_idle_to_running(self):
        """Test valid transition from IDLE to RUNNING."""
        assert WorkerStateMachine.is_valid_transition(
            WorkerState.IDLE, WorkerState.RUNNING
        )

    def test_invalid_transition_idle_to_paused(self):
        """Test invalid transition from IDLE to PAUSED."""
        assert not WorkerStateMachine.is_valid_transition(
            WorkerState.IDLE, WorkerState.PAUSED
        )

    def test_terminal_state_completed(self):
        """Test COMPLETED is terminal state."""
        assert WorkerStateMachine.is_terminal_state(WorkerState.COMPLETED)
        assert not WorkerStateMachine.is_valid_transition(
            WorkerState.COMPLETED, WorkerState.RUNNING
        )

    def test_force_terminate_from_any_state(self):
        """Test TERMINATED can be reached from any state."""
        for state in WorkerState:
            if state != WorkerState.TERMINATED:
                assert WorkerStateMachine.is_valid_transition(
                    state, WorkerState.TERMINATED
                )
```

### 6.2 Integration Tests

Test state transitions with API:

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_pause_running_worker(client: AsyncClient):
    """Test pausing a running worker via API."""
    # Create worker
    response = await client.post(
        "/api/workers", json={"workspace_id": "ws_test"}
    )
    worker_id = response.json()["id"]

    # Start worker (IDLE → RUNNING)
    await client.post(f"/api/workers/{worker_id}/start")

    # Pause worker (RUNNING → PAUSED)
    response = await client.post(
        f"/api/supervisor/workers/{worker_id}/pause",
        json={"reason": "Test pause"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "PAUSED"

@pytest.mark.asyncio
async def test_idempotent_pause(client: AsyncClient):
    """Test idempotent pause operation."""
    worker_id = "w_test123"
    request_id = "req_abc123"

    # First pause request
    response1 = await client.post(
        f"/api/supervisor/workers/{worker_id}/pause",
        json={"request_id": request_id},
    )

    # Second pause request with same request_id
    response2 = await client.post(
        f"/api/supervisor/workers/{worker_id}/pause",
        json={"request_id": request_id},
    )

    # Should return same result
    assert response1.json() == response2.json()
```

---

## 7. State Machine Metrics

Track metrics for monitoring:

- **Transition counts** by state pair (e.g., RUNNING → PAUSED)
- **Time in state** (distribution of how long workers stay in each state)
- **Failed transitions** (attempts to make invalid transitions)
- **Idempotency cache hit rate**

---

## 8. References

- Week 2 MVP Specification
- OpenAPI 3.0 Specification
- Excellence AI Standard (error handling patterns)
- Finite State Machine patterns (Gang of Four)

---

**Approval Status**: Ready for review
**Next Steps**: Implement state machine classes + unit tests
