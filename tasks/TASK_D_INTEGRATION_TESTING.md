# Task D: Integration Testing for Week 2 MVP Phase 1 & 2

**Task ID**: Task D
**Module**: Integration Testing
**Test Suites**: Core Foundation + API Modules
**Estimated Time**: 4h
**Worker Type**: Codex Worker (use `--use-codex` flag)

---

## 🎯 Mission

Create comprehensive integration tests for Week 2 MVP Phase 1 (Core Foundation) and Phase 2 (API Modules) to achieve 75%+ test coverage and ensure production readiness.

---

## 📋 Prerequisites (Already Complete)

✅ Database models: `orchestrator/core/db_models.py` (698 lines)
✅ State machine: `orchestrator/core/state_machine.py` (489 lines)
✅ Authentication: `orchestrator/core/auth.py` (376 lines)
✅ Database config: `orchestrator/core/database.py` (283 lines)
✅ Supervisor API: `orchestrator/api/supervisor_api.py`
✅ Resource Manager API: `orchestrator/api/resources_api.py`
✅ Job Orchestrator API: `orchestrator/api/jobs_api.py`
✅ Dependencies: `orchestrator/api/dependencies.py`

---

## 📁 Files to Create

```
tests/integration/
├── test_week2_core_foundation.py     ← Create: Phase 1 core tests
├── test_week2_api_modules.py         ← Create: Phase 2 API tests
├── test_week2_end_to_end.py          ← Create: E2E workflow tests
└── conftest.py                       ← Update: Test fixtures
```

---

## 🔨 Implementation Tasks

### Task D.1: Core Foundation Integration Tests (1.5h)

**File**: `tests/integration/test_week2_core_foundation.py`

**Requirements**:
- Test database session lifecycle
- Test state machine transitions (Worker, Job)
- Test authentication (password hashing, JWT generation/validation)
- Test database models (CRUD operations, relationships, constraints)

**Test Cases** (minimum 12 tests):
1. `test_database_session_lifecycle` - Connection pool, session creation/cleanup
2. `test_worker_state_transitions` - All valid transitions
3. `test_worker_invalid_transitions` - StateTransitionError handling
4. `test_job_state_transitions` - All valid transitions
5. `test_job_invalid_transitions` - StateTransitionError handling
6. `test_password_hashing_security` - Argon2id, salt uniqueness
7. `test_jwt_token_generation` - Valid token structure
8. `test_jwt_token_validation` - Signature verification, expiration
9. `test_worker_model_crud` - Create, read, update, delete
10. `test_job_model_relationships` - Foreign keys, cascades
11. `test_resource_allocation_constraints` - Unique constraints, validation
12. `test_idempotency_key_uniqueness` - Duplicate prevention

**Pattern**:
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from orchestrator.core.database import Base
from orchestrator.core.db_models import Worker, Job, WorkerStatus, JobStatus
from orchestrator.core.state_machine import WorkerStateMachine, JobStateMachine
from orchestrator.core.auth import hash_password, verify_password, create_access_token, verify_token

@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_database_session_lifecycle(test_db):
    """Test database session creation and cleanup"""
    assert test_db.is_active
    worker = Worker(worker_id="test-worker-1", status=WorkerStatus.IDLE)
    test_db.add(worker)
    test_db.commit()
    assert test_db.query(Worker).count() == 1

def test_worker_state_transitions(test_db):
    """Test all valid worker state transitions"""
    worker = Worker(worker_id="worker-1", status=WorkerStatus.IDLE)
    test_db.add(worker)
    test_db.commit()

    state_machine = WorkerStateMachine(test_db)

    # IDLE → BUSY
    state_machine.transition(worker, WorkerStatus.BUSY)
    assert worker.status == WorkerStatus.BUSY

    # BUSY → IDLE
    state_machine.transition(worker, WorkerStatus.IDLE)
    assert worker.status == WorkerStatus.IDLE

    # IDLE → FAILED
    state_machine.transition(worker, WorkerStatus.FAILED)
    assert worker.status == WorkerStatus.FAILED

def test_password_hashing_security(test_db):
    """Test Argon2id password hashing security"""
    password = "SecurePassword123!"

    # Test hashing
    hashed1 = hash_password(password)
    hashed2 = hash_password(password)

    # Verify salt uniqueness
    assert hashed1 != hashed2

    # Verify correct password
    assert verify_password(password, hashed1) is True

    # Verify incorrect password
    assert verify_password("WrongPassword", hashed1) is False

# Add 9 more tests following similar patterns...
```

**Success Criteria**:
- [ ] All 12+ tests pass
- [ ] Coverage ≥90% for core modules (database, state_machine, auth, db_models)
- [ ] NO TODO/FIXME/HACK comments
- [ ] All functions ≤50 lines
- [ ] Comprehensive docstrings

---

### Task D.2: API Modules Integration Tests (1.5h)

**File**: `tests/integration/test_week2_api_modules.py`

**Requirements**:
- Test FastAPI dependencies (get_db, get_current_user, require_scope)
- Test Supervisor API endpoints (list, get, pause, resume, terminate, metrics)
- Test Resource Manager API (quotas, allocate, release, usage)
- Test Job Orchestrator API (submit, get, cancel, list)
- Test error handling (401, 403, 404, 422)

**Test Cases** (minimum 15 tests):
1. `test_get_db_dependency` - Database session injection
2. `test_get_current_user_valid_token` - JWT validation success
3. `test_get_current_user_invalid_token` - 401 Unauthorized
4. `test_require_scope_authorized` - Scope check success
5. `test_require_scope_forbidden` - 403 Forbidden
6. `test_supervisor_list_workers` - GET /api/supervisor/workers
7. `test_supervisor_get_worker` - GET /api/supervisor/workers/{id}
8. `test_supervisor_pause_worker` - POST /api/supervisor/workers/{id}/pause
9. `test_supervisor_metrics` - GET /api/supervisor/metrics
10. `test_resources_get_quotas` - GET /api/resources/quotas
11. `test_resources_allocate` - POST /api/resources/allocate
12. `test_resources_release` - POST /api/resources/release
13. `test_jobs_submit` - POST /api/jobs/submit
14. `test_jobs_get` - GET /api/jobs/{id}
15. `test_jobs_cancel` - POST /api/jobs/{id}/cancel

**Pattern**:
```python
import pytest
from fastapi.testclient import TestClient
from orchestrator.api.main import app
from orchestrator.core.auth import create_access_token

@pytest.fixture
def client():
    """Create FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def auth_headers():
    """Create valid JWT token for testing"""
    token = create_access_token(
        user_id="test-user",
        scopes=["supervisor:read", "supervisor:write", "jobs:write"]
    )
    return {"Authorization": f"Bearer {token}"}

def test_supervisor_list_workers(client, auth_headers):
    """Test GET /api/supervisor/workers endpoint"""
    response = client.get("/api/supervisor/workers", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "workers" in data
    assert isinstance(data["workers"], list)

def test_get_current_user_invalid_token(client):
    """Test JWT validation with invalid token"""
    headers = {"Authorization": "Bearer invalid-token"}
    response = client.get("/api/supervisor/workers", headers=headers)
    assert response.status_code == 401
    assert "Invalid authentication credentials" in response.json()["detail"]

# Add 13 more tests following similar patterns...
```

**Success Criteria**:
- [ ] All 15+ tests pass
- [ ] Coverage ≥75% for API modules (supervisor_api, resources_api, jobs_api, dependencies)
- [ ] All HTTP status codes tested (200, 401, 403, 404, 422)
- [ ] Request/response validation tested
- [ ] Excellence AI Standard 100% compliance

---

### Task D.3: End-to-End Workflow Tests (1h)

**File**: `tests/integration/test_week2_end_to_end.py`

**Requirements**:
- Test complete workflows (job submission → execution → completion)
- Test worker lifecycle (idle → busy → idle)
- Test resource allocation and deallocation
- Test authentication + authorization flow

**Test Cases** (minimum 5 tests):
1. `test_complete_job_workflow` - Submit job → Allocate resources → Execute → Complete
2. `test_worker_lifecycle` - Worker state transitions during job execution
3. `test_resource_allocation_workflow` - Check quotas → Allocate → Release
4. `test_authentication_flow` - Login → Get token → Access protected endpoint
5. `test_concurrent_jobs` - Multiple jobs executing simultaneously

**Pattern**:
```python
import pytest
from fastapi.testclient import TestClient
from orchestrator.api.main import app
from orchestrator.core.auth import create_access_token

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def admin_token():
    return create_access_token(
        user_id="admin",
        scopes=["supervisor:read", "supervisor:write", "jobs:write", "resources:write"]
    )

def test_complete_job_workflow(client, admin_token):
    """Test complete job submission to completion workflow"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Check initial worker status
    response = client.get("/api/supervisor/workers", headers=headers)
    assert response.status_code == 200

    # 2. Check resource quotas
    response = client.get("/api/resources/quotas", headers=headers)
    assert response.status_code == 200
    quotas = response.json()
    assert quotas["available_workers"] > 0

    # 3. Submit job
    job_data = {
        "task_description": "Test task",
        "required_workers": 1
    }
    response = client.post("/api/jobs/submit", headers=headers, json=job_data)
    assert response.status_code == 201
    job_id = response.json()["job_id"]

    # 4. Verify job created
    response = client.get(f"/api/jobs/{job_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "pending"

    # 5. Verify worker allocated
    response = client.get("/api/supervisor/workers", headers=headers)
    workers = response.json()["workers"]
    busy_workers = [w for w in workers if w["status"] == "busy"]
    assert len(busy_workers) >= 1

# Add 4 more E2E tests...
```

**Success Criteria**:
- [ ] All 5+ E2E tests pass
- [ ] Complete workflows tested end-to-end
- [ ] Multi-step operations validated
- [ ] Concurrent operations tested
- [ ] NO race conditions or deadlocks

---

## ✅ Success Criteria (Overall)

- [ ] **32+ integration tests** (12 core + 15 API + 5 E2E) all passing
- [ ] **Coverage ≥75%** for Week 2 MVP modules
  - Core modules: ≥90% (database, state_machine, auth, db_models)
  - API modules: ≥75% (supervisor_api, resources_api, jobs_api, dependencies)
- [ ] **Excellence AI Standard 100%** compliance
  - Security: JWT validation, scope checking, password hashing
  - Type Safety: Full type annotations
  - Documentation: Comprehensive test docstrings
  - Code Quality: All functions ≤50 lines
  - NO TODO/FIXME/HACK
- [ ] **CI/CD Ready**: All tests pass in automated pipeline
- [ ] **Production Ready**: E2E workflows validated

---

## 📚 References

**Core Modules**:
- [database.py:1-283](../../dev-tools/parallel-coding/orchestrator/core/database.py) - Database session management
- [db_models.py:1-698](../../dev-tools/parallel-coding/orchestrator/core/db_models.py) - SQLAlchemy models
- [state_machine.py:1-489](../../dev-tools/parallel-coding/orchestrator/core/state_machine.py) - State transitions
- [auth.py:1-376](../../dev-tools/parallel-coding/orchestrator/core/auth.py) - Argon2id + JWT

**API Modules**:
- [supervisor_api.py](../../dev-tools/parallel-coding/orchestrator/api/supervisor_api.py) - Worker monitoring
- [resources_api.py](../../dev-tools/parallel-coding/orchestrator/api/resources_api.py) - Resource management
- [jobs_api.py](../../dev-tools/parallel-coding/orchestrator/api/jobs_api.py) - Job orchestration
- [dependencies.py](../../dev-tools/parallel-coding/orchestrator/api/dependencies.py) - FastAPI dependencies

**Standards**:
- [Excellence AI Standard](../../dev-tools/excellence-ai-standard/.claude_code_config.md) - World-class quality requirements

---

**Generated with**: Excellence AI Standard 100% | Token Efficiency v6.0 | Codex-Driven Development
