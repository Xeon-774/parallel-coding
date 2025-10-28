# Worker 2: Type-Safe Implementation - Week 2 MVP

**Worker ID**: Worker 2 (Type Safety & Robustness Approach)
**Approach**: SQLAlchemy ORM + python-statemachine + Pydantic v2 Strict + FastAPI Advanced
**Priority**: Type Safety, Validation, Robustness
**Estimated Time**: 50-60h
**Codex Worker**: Use regular Claude workers (not Codex)

---

## 🎯 Mission

Implement Week 2 MVP with **maximum type safety and validation** using python-statemachine library and Pydantic v2 strict mode for bulletproof robustness.

---

## 📋 Implementation Strategy

### Philosophy
- ✅ **Type safety first** - Catch errors at compile time
- ✅ **Explicit validation** - Pydantic v2 strict mode
- ✅ **State machine library** - python-statemachine for formal FSM
- ✅ **Robustness** over speed

### Technology Stack
- **Database**: SQLAlchemy 2.0 ORM (synchronous)
- **State Machine**: python-statemachine library (formal FSM)
- **API**: FastAPI with advanced dependency injection
- **Validation**: Pydantic v2 strict mode
- **Auth**: python-jose for JWT, passlib + argon2-cffi
- **Testing**: pytest + pytest-asyncio + hypothesis (property-based)

### Additional Dependencies

Add to `requirements.txt`:
```python
python-statemachine>=2.1.0  # Formal state machine library
hypothesis>=6.90.0          # Property-based testing
```

---

## 📁 Project Structure

```
orchestrator/
├── core/
│   ├── database.py          ← Already created ✅
│   ├── models.py            ← Create: SQLAlchemy models with strict typing
│   ├── schemas.py           ← Create: Pydantic v2 strict schemas
│   ├── state_machine.py     ← Create: python-statemachine FSM
│   └── auth.py              ← Create: JWT with strict typing
├── api/
│   ├── main.py              ← Update: Add new routers
│   ├── dependencies.py      ← Create: Strict type dependencies
│   ├── supervisor_api.py    ← Create: 6 endpoints with strict validation
│   ├── resources_api.py     ← Create: 4 endpoints with strict validation
│   └── jobs_api.py          ← Create: 4 endpoints with strict validation
└── alembic/
    ├── versions/
    │   └── 001_initial_schema.py
    └── env.py
```

---

## 🔨 Implementation Tasks

### Phase 1: Database & Models (10h)

#### Task 1.1: Create Pydantic v2 Schemas (4h)

**File**: `orchestrator/core/schemas.py`

**Requirements**:
- Strict mode enabled (no implicit type coercion)
- Field validators for all inputs
- Comprehensive type annotations
- JSON schema generation

**Example Pattern**:
```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Literal
from datetime import datetime
import uuid

class WorkerStatus(str, Enum):
    """Worker lifecycle states (type-safe enum)"""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"

class WorkerBase(BaseModel):
    """
    Base worker schema with strict validation.

    Type Safety: Pydantic v2 strict mode (no implicit coercion)
    """
    model_config = ConfigDict(strict=True)  # Enable strict mode

    workspace_id: str = Field(..., min_length=1, max_length=255)
    status: WorkerStatus

    @field_validator('workspace_id')
    @classmethod
    def validate_workspace_id(cls, v: str) -> str:
        """Validate workspace ID format"""
        if not v.strip():
            raise ValueError("workspace_id cannot be empty")
        return v.strip()

class WorkerCreate(WorkerBase):
    """Schema for creating new worker"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class WorkerResponse(WorkerBase):
    """Schema for worker API responses"""
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)  # Enable ORM mode
```

#### Task 1.2: Create SQLAlchemy Models (4h)

**File**: `orchestrator/core/models.py`

**Requirements**:
- Explicit type annotations using SQLAlchemy 2.0 style
- Relationships with type hints
- Comprehensive docstrings

**Example Pattern**:
```python
from typing import List, Optional
from sqlalchemy import String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

class Worker(Base):
    """
    Worker instance model with strict typing.

    Type Safety: SQLAlchemy 2.0 Mapped types
    """
    __tablename__ = "workers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[WorkerStatus] = mapped_column(SQLEnum(WorkerStatus), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships with type hints
    state_transitions: Mapped[List["StateTransition"]] = relationship(back_populates="worker")
```

#### Task 1.3: Initialize Alembic (2h)

Same as Worker 1.

---

### Phase 2: State Machine (10h)

#### Task 2.1: Worker State Machine with python-statemachine (5h)

**File**: `orchestrator/core/state_machine.py`

**Requirements**:
- Use python-statemachine library
- Formal FSM with guards and actions
- Type-safe transitions
- Comprehensive event logging

**Pattern**:
```python
from statemachine import StateMachine, State
from typing import Optional
from orchestrator.core.schemas import WorkerStatus

class WorkerStateMachine(StateMachine):
    """
    Worker lifecycle state machine using python-statemachine.

    Type Safety: Explicit state definitions with type-safe transitions
    Robustness: Guards prevent invalid transitions
    """

    # State definitions
    idle = State(WorkerStatus.IDLE, initial=True)
    running = State(WorkerStatus.RUNNING)
    paused = State(WorkerStatus.PAUSED)
    completed = State(WorkerStatus.COMPLETED, final=True)
    failed = State(WorkerStatus.FAILED, final=True)
    terminated = State(WorkerStatus.TERMINATED, final=True)

    # Transitions
    start = idle.to(running)
    pause = running.to(paused)
    resume = paused.to(running)
    complete = running.to(completed)
    fail = running.to(failed) | paused.to(failed)
    terminate = running.to(terminated) | paused.to(terminated)

    def __init__(self, worker_id: str, db_session: Session):
        """
        Initialize state machine for specific worker.

        Args:
            worker_id: Worker identifier
            db_session: Database session for persistence
        """
        self.worker_id = worker_id
        self.db_session = db_session
        super().__init__()

    def on_enter_running(self) -> None:
        """Action: Log when entering RUNNING state"""
        self._log_state_transition(WorkerStatus.RUNNING)

    def on_enter_paused(self) -> None:
        """Action: Log when entering PAUSED state"""
        self._log_state_transition(WorkerStatus.PAUSED)

    def _log_state_transition(self, new_state: WorkerStatus) -> None:
        """Persist state transition to database"""
        transition = StateTransition(
            worker_id=self.worker_id,
            from_state=self.current_state.id,
            to_state=new_state,
            timestamp=datetime.utcnow()
        )
        self.db_session.add(transition)
        self.db_session.commit()
```

#### Task 2.2: Job State Machine (5h)

Similar structure for Job lifecycle with python-statemachine.

---

### Phase 3: Authentication (5h)

#### Task 3.1: JWT Module with Strict Types (5h)

**File**: `orchestrator/core/auth.py`

**Requirements**:
- Strict type annotations on all functions
- Pydantic models for token payloads
- Comprehensive error handling with typed exceptions

**Pattern**:
```python
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from jose import JWTError, jwt

class TokenPayload(BaseModel):
    """
    JWT token payload with strict validation.

    Type Safety: Pydantic v2 strict mode
    """
    model_config = ConfigDict(strict=True)

    sub: str = Field(..., description="User ID")
    exp: datetime = Field(..., description="Expiration time")
    scopes: List[str] = Field(default_factory=list)

class TokenData(BaseModel):
    """Token data after validation"""
    user_id: str
    scopes: List[str]

def create_access_token(
    user_id: str,
    scopes: List[str],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token with strict typing.

    Args:
        user_id: User identifier (non-empty string)
        scopes: List of permission scopes
        expires_delta: Token expiration duration

    Returns:
        JWT token string

    Raises:
        ValueError: If user_id is empty
    """
    if not user_id.strip():
        raise ValueError("user_id cannot be empty")

    expire = datetime.utcnow() + (expires_delta or timedelta(hours=24))
    payload = TokenPayload(sub=user_id, exp=expire, scopes=scopes)

    return jwt.encode(payload.model_dump(), SECRET_KEY, algorithm=ALGORITHM)
```

---

### Phase 4: API Endpoints (15h)

#### Task 4.1: API Dependencies with Strict Types (3h)

**File**: `orchestrator/api/dependencies.py`

**Requirements**:
- Strict type annotations on all dependencies
- Custom exception classes with types
- Comprehensive validation

**Pattern**:
```python
from typing import Annotated
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(security)]
) -> TokenData:
    """
    Validate JWT token and return user data.

    Type Safety: Explicit return type with Pydantic model
    Security: Bearer token validation

    Returns:
        TokenData: Validated user data with scopes

    Raises:
        HTTPException: 401 if token invalid
    """
    try:
        token_data = verify_token(credentials.credentials)
        return token_data
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def require_scope(required_scope: str):
    """
    Dependency factory for scope checking.

    Type Safety: Returns typed dependency function
    """
    def check_scope(user: Annotated[TokenData, Depends(get_current_user)]) -> TokenData:
        if required_scope not in user.scopes:
            raise HTTPException(status_code=403, detail=f"Missing required scope: {required_scope}")
        return user
    return check_scope
```

#### Task 4.2: Supervisor API with Strict Validation (6h)

**File**: `orchestrator/api/supervisor_api.py`

**Requirements**:
- All request/response models use Pydantic v2 strict schemas
- Comprehensive input validation
- Typed exception handling

**Pattern**:
```python
from typing import Annotated, List
from fastapi import APIRouter, Depends, Query
from orchestrator.core.schemas import WorkerResponse, WorkerListResponse

router = APIRouter(prefix="/api/supervisor", tags=["supervisor"])

@router.get("/workers", response_model=WorkerListResponse)
async def list_workers(
    workspace_id: Annotated[Optional[str], Query(min_length=1, max_length=255)] = None,
    status: Annotated[Optional[WorkerStatus], Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Annotated[Session, Depends(get_db)] = None,
    user: Annotated[TokenData, Depends(require_scope("supervisor:read"))] = None
) -> WorkerListResponse:
    """
    List workers with strict type validation.

    Type Safety: All parameters and return types explicitly annotated
    Validation: Query parameters validated by Pydantic

    Args:
        workspace_id: Filter by workspace (1-255 chars)
        status: Filter by worker status
        limit: Max results (1-100)
        offset: Pagination offset (≥0)
        db: Database session (injected)
        user: Current user (injected, requires supervisor:read scope)

    Returns:
        WorkerListResponse: List of workers with pagination metadata
    """
    # Implementation with strict typing
```

#### Task 4.3: Resource Manager API (3h)

#### Task 4.4: Job Orchestrator API (3h)

---

### Phase 5: Testing (12h)

#### Task 5.1: Unit Tests with Property-Based Testing (7h)

**Requirements**:
- Use hypothesis for property-based testing
- Test invariants (e.g., "state machine always reachable")
- Comprehensive edge case coverage

**Pattern**:
```python
import pytest
from hypothesis import given, strategies as st
from orchestrator.core.state_machine import WorkerStateMachine

@given(st.lists(st.sampled_from(['start', 'pause', 'resume', 'terminate'])))
def test_state_machine_invariants(transitions: List[str]):
    """
    Property-based test: State machine always remains in valid state.

    Uses hypothesis to generate random transition sequences
    and verify invariants hold.
    """
    sm = WorkerStateMachine(worker_id="test", db_session=mock_session)

    for transition_name in transitions:
        if hasattr(sm, transition_name):
            try:
                transition = getattr(sm, transition_name)
                transition()
            except:
                pass  # Invalid transitions expected

    # Invariant: Current state must always be one of defined states
    assert sm.current_state.id in [
        WorkerStatus.IDLE, WorkerStatus.RUNNING, WorkerStatus.PAUSED,
        WorkerStatus.COMPLETED, WorkerStatus.FAILED, WorkerStatus.TERMINATED
    ]
```

**Files**:
- `tests/unit/test_models.py` (2h)
- `tests/unit/test_state_machine.py` (3h, with property-based tests)
- `tests/unit/test_auth.py` (2h)

**Coverage Target**: 80% minimum

#### Task 5.2: Integration Tests (5h)

**Files**:
- `tests/integration/test_supervisor_api.py` (2h)
- `tests/integration/test_resources_api.py` (1.5h)
- `tests/integration/test_jobs_api.py` (1.5h)

---

### Phase 6: Documentation (4h)

Same as Worker 1.

---

## 🎯 Deliverables

### Code Files (15 files)
1. ✅ `orchestrator/core/database.py` (already exists)
2. `orchestrator/core/schemas.py` (NEW - Pydantic strict schemas)
3. `orchestrator/core/models.py`
4. `orchestrator/core/state_machine.py` (python-statemachine)
5. `orchestrator/core/auth.py`
6. `orchestrator/api/dependencies.py`
7. `orchestrator/api/supervisor_api.py`
8. `orchestrator/api/resources_api.py`
9. `orchestrator/api/jobs_api.py`
10. `orchestrator/api/main.py` (updated)
11. `alembic/versions/001_initial_schema.py`
12-15. Test files (unit + integration + property-based)

### Documentation
- API documentation with JSON schemas
- Postman collection

### Tests
- Unit tests (≥80% coverage)
- Integration tests
- Property-based tests (hypothesis)

---

## ✅ Success Criteria

- [ ] All 14 API endpoints functional with strict validation
- [ ] python-statemachine formal FSM implemented
- [ ] Pydantic v2 strict mode enforced
- [ ] 80%+ test coverage
- [ ] Property-based tests pass
- [ ] All type checks pass (mypy --strict)
- [ ] No TODO/FIXME/HACK
- [ ] Excellence AI Standard 100% compliance

---

## 📚 Reference Documents

Same as Worker 1, plus:
- python-statemachine docs: https://python-statemachine.readthedocs.io/
- Pydantic v2 strict mode: https://docs.pydantic.dev/latest/concepts/strict_mode/
- hypothesis docs: https://hypothesis.readthedocs.io/

---

## 🔧 Development Commands

```bash
# Install additional dependencies
pip install python-statemachine hypothesis

# Type checking
mypy orchestrator --strict

# Run tests
pytest tests/ -v --cov=orchestrator --cov-report=html

# Property-based tests
pytest tests/unit/test_state_machine.py -v --hypothesis-show-statistics
```

---

## 🚨 Important Notes

1. **Strict mode**: Pydantic v2 strict mode enabled (no implicit coercion)
2. **Type checking**: Run mypy --strict before committing
3. **FSM validation**: python-statemachine ensures formal state machine properties
4. **Property-based tests**: Use hypothesis for invariant testing

---

**Remember**: Type safety and robustness are priorities. Catch errors early!

Good luck, Worker 2! 🛡️
