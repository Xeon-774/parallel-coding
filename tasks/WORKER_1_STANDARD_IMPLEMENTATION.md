# Worker 1: Standard Implementation - Week 2 MVP

**Worker ID**: Worker 1 (Standard & Conservative Approach)
**Approach**: SQLAlchemy ORM + Enum-based State Machine + FastAPI Standard
**Priority**: Speed, Simplicity, Maintainability
**Estimated Time**: 40-50h
**Codex Worker**: Use regular Claude workers (not Codex)

---

## 🎯 Mission

Implement Week 2 MVP (Supervisor API + Resource Manager + Job Orchestrator) using **standard, battle-tested patterns** for rapid development and easy maintenance.

---

## 📋 Implementation Strategy

### Philosophy
- ✅ **Standard patterns** over novel approaches
- ✅ **Proven libraries** (SQLAlchemy ORM, FastAPI)
- ✅ **Simple is better** than complex
- ✅ **Maintainability** over cleverness

### Technology Stack
- **Database**: SQLAlchemy 2.0 ORM (synchronous)
- **State Machine**: Python Enum + explicit validation functions
- **API**: FastAPI with standard dependency injection
- **Auth**: python-jose for JWT, passlib + argon2-cffi for passwords
- **Testing**: pytest + pytest-asyncio

---

## 📁 Project Structure

```
orchestrator/
├── core/
│   ├── database.py          ← Already created ✅
│   ├── models.py            ← Create: SQLAlchemy models
│   ├── state_machine.py     ← Create: Enum-based state machine
│   └── auth.py              ← Create: JWT authentication
├── api/
│   ├── main.py              ← Update: Add new routers
│   ├── dependencies.py      ← Create: DB session, auth dependencies
│   ├── supervisor_api.py    ← Create: 6 supervisor endpoints
│   ├── resources_api.py     ← Create: 4 resource endpoints
│   └── jobs_api.py          ← Create: 4 job endpoints
└── alembic/
    ├── versions/
    │   └── 001_initial_schema.py  ← Create: Initial migration
    └── env.py               ← Configure: Alembic environment
```

---

## 🔨 Implementation Tasks

### Phase 1: Database & Models (8h)

#### Task 1.1: Create SQLAlchemy Models (4h)

**File**: `orchestrator/core/models.py`

**Requirements**:
- Worker model (id, workspace_id, status, metadata, created_at, updated_at)
- Job model (id, workspace_id, depth, status, parent_job_id, created_at)
- ResourceAllocation model (id, job_id, allocated_at, released_at)
- StateTransition model (audit trail for all state changes)
- IdempotencyKey model (prevent duplicate operations)

**Standards**:
- ✅ Pydantic validation for all inputs
- ✅ Explicit type annotations (no 'any')
- ✅ Comprehensive docstrings with examples
- ✅ Functions ≤50 lines, complexity ≤10

**Example Pattern**:
```python
from sqlalchemy import Column, String, DateTime, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

class WorkerStatus(enum.Enum):
    """Worker lifecycle states"""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"

class Worker(Base):
    """
    Worker instance model.

    Represents a Claude Code worker with lifecycle state management.
    """
    __tablename__ = "workers"

    id = Column(String(36), primary_key=True)
    workspace_id = Column(String(255), nullable=False, index=True)
    status = Column(SQLEnum(WorkerStatus), nullable=False, index=True)
    # ... additional columns
```

#### Task 1.2: Initialize Alembic (2h)

**Commands**:
```bash
cd tools/parallel-coding
alembic init alembic
# Configure alembic.ini and env.py
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

#### Task 1.3: Create Database Utilities (2h)

**File**: `orchestrator/core/database.py` (already exists, verify completeness)

---

### Phase 2: State Machine (6h)

#### Task 2.1: Worker State Machine (3h)

**File**: `orchestrator/core/state_machine.py`

**Requirements**:
- WorkerStateMachine class
- Explicit transition validation (IDLE → RUNNING, RUNNING → PAUSED, etc.)
- State persistence to database
- Audit trail logging

**Pattern**:
```python
class WorkerStateMachine:
    """
    Manages worker state transitions with validation.

    Simple enum-based approach for clarity and maintainability.
    """

    VALID_TRANSITIONS = {
        WorkerStatus.IDLE: {WorkerStatus.RUNNING},
        WorkerStatus.RUNNING: {
            WorkerStatus.PAUSED,
            WorkerStatus.COMPLETED,
            WorkerStatus.FAILED,
            WorkerStatus.TERMINATED
        },
        WorkerStatus.PAUSED: {WorkerStatus.RUNNING, WorkerStatus.TERMINATED},
        # ...
    }

    @classmethod
    def can_transition(cls, from_state: WorkerStatus, to_state: WorkerStatus) -> bool:
        """Check if state transition is valid"""
        return to_state in cls.VALID_TRANSITIONS.get(from_state, set())
```

#### Task 2.2: Job State Machine (3h)

Similar structure for Job lifecycle.

---

### Phase 3: Authentication (4h)

#### Task 3.1: JWT Module (4h)

**File**: `orchestrator/core/auth.py`

**Requirements**:
- Token generation (create_access_token)
- Token validation (verify_token)
- Scope checking (check_scopes)
- Argon2id password hashing

**Standards**:
- ✅ Argon2id ONLY (Excellence AI Standard)
- ✅ Secret keys from environment variables
- ✅ Token expiration handling

---

### Phase 4: API Endpoints (16h)

#### Task 4.1: API Dependencies (2h)

**File**: `orchestrator/api/dependencies.py`

- get_db() - Database session
- get_current_user() - JWT validation
- check_permission() - Scope validation

#### Task 4.2: Supervisor API (6h)

**File**: `orchestrator/api/supervisor_api.py`

**Endpoints**:
1. GET /api/supervisor/workers (list workers)
2. GET /api/supervisor/workers/{id} (get worker details)
3. POST /api/supervisor/workers/{id}/pause
4. POST /api/supervisor/workers/{id}/resume
5. POST /api/supervisor/workers/{id}/terminate
6. GET /api/supervisor/metrics

**Pattern**:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from orchestrator.api.dependencies import get_db, get_current_user

router = APIRouter(prefix="/api/supervisor", tags=["supervisor"])

@router.get("/workers")
async def list_workers(
    workspace_id: str = None,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all workers with optional filters.

    Security: JWT required, supervisor:read scope
    """
    # Implementation
```

#### Task 4.3: Resource Manager API (4h)

**File**: `orchestrator/api/resources_api.py`

**Endpoints**:
1. GET /api/resources/quotas
2. POST /api/resources/allocate
3. POST /api/resources/release
4. GET /api/resources/usage

#### Task 4.4: Job Orchestrator API (4h)

**File**: `orchestrator/api/jobs_api.py`

**Endpoints**:
1. POST /api/jobs/submit
2. GET /api/jobs/{id}
3. POST /api/jobs/{id}/cancel
4. GET /api/jobs (list jobs)

---

### Phase 5: Testing (10h)

#### Task 5.1: Unit Tests (6h)

**Files**:
- `tests/unit/test_models.py` (2h)
- `tests/unit/test_state_machine.py` (2h)
- `tests/unit/test_auth.py` (2h)

**Coverage Target**: 75% minimum

#### Task 5.2: Integration Tests (4h)

**Files**:
- `tests/integration/test_supervisor_api.py` (2h)
- `tests/integration/test_resources_api.py` (1h)
- `tests/integration/test_jobs_api.py` (1h)

**Test Categories** (Excellence AI Standard):
- ✅ Happy path
- ✅ Edge cases
- ✅ Error cases
- ✅ Security cases

---

### Phase 6: Documentation (4h)

#### Task 6.1: API Documentation (2h)

- Update FastAPI OpenAPI spec
- Swagger UI verification

#### Task 6.2: Postman Collection (2h)

**File**: `tools/parallel-coding/postman/Week2_MVP_Collection.json`

---

## 🎯 Deliverables

### Code Files (14 files)
1. ✅ `orchestrator/core/database.py` (already exists)
2. `orchestrator/core/models.py`
3. `orchestrator/core/state_machine.py`
4. `orchestrator/core/auth.py`
5. `orchestrator/api/dependencies.py`
6. `orchestrator/api/supervisor_api.py`
7. `orchestrator/api/resources_api.py`
8. `orchestrator/api/jobs_api.py`
9. `orchestrator/api/main.py` (updated)
10. `alembic/versions/001_initial_schema.py`
11-14. Test files (unit + integration)

### Documentation
- API documentation (Swagger UI)
- Postman collection

### Tests
- Unit tests (≥75% coverage)
- Integration tests (happy paths)

---

## ✅ Success Criteria

- [ ] All 14 API endpoints functional
- [ ] State machine validated with unit tests
- [ ] JWT authentication working
- [ ] 75%+ test coverage
- [ ] All tests passing
- [ ] Postman collection complete
- [ ] No TODO/FIXME/HACK comments
- [ ] Excellence AI Standard 100% compliance

---

## 📚 Reference Documents

**Week 2 MVP Spec**: `tools/parallel-coding/docs/WEEK2_MVP_SPECIFICATION.md`
**API Spec**: `tools/parallel-coding/docs/API_SPECIFICATION.yaml`
**Database Schema**: `tools/parallel-coding/docs/DATABASE_SCHEMA_DESIGN.md`
**State Machine**: `tools/parallel-coding/docs/STATE_MACHINE_DESIGN.md`
**Excellence AI Standard**: `token_efficiency_standard/summaries/excellence_ai_standard_summary.md`

---

## 🔧 Development Commands

```bash
# Setup
cd tools/parallel-coding
pip install -r requirements.txt

# Database
alembic upgrade head

# Run API server
uvicorn orchestrator.api.main:app --reload --port 8000

# Run tests
pytest tests/ -v --cov=orchestrator --cov-report=html

# Check coverage
open htmlcov/index.html
```

---

## 🚨 Important Notes

1. **UTF-8 with BOM**: All Python files must have UTF-8 BOM
2. **Argon2id passwords**: NEVER use bcrypt or MD5
3. **SQL parameterization**: NEVER use string concatenation
4. **Type safety**: NO 'any' types
5. **Complete implementation**: NO TODO/FIXME/HACK
6. **Test coverage**: Target 75% minimum (90% in Week 3)

---

**Remember**: Speed and simplicity are priorities. Use standard patterns that work.

Good luck, Worker 1! 🚀
