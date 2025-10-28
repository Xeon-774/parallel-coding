# Task A: Supervisor API Implementation

**Task ID**: Task A
**Module**: Supervisor API
**Endpoints**: 6 endpoints
**Estimated Time**: 8h
**Worker Type**: Codex Worker (use `--use-codex` flag)

---

## 🎯 Mission

Implement Supervisor API with 6 endpoints for worker monitoring and control.

---

## 📋 Prerequisites (Already Complete)

✅ Database models: `orchestrator/core/db_models.py`
✅ State machine: `orchestrator/core/state_machine.py`
✅ Authentication: `orchestrator/core/auth.py`
✅ Database config: `orchestrator/core/database.py`

---

## 📁 Files to Create

```
orchestrator/api/
├── dependencies.py          ← Create: DB session, JWT validation
├── supervisor_api.py        ← Create: 6 supervisor endpoints
└── main.py                  ← Update: Add supervisor router

tests/integration/
└── test_supervisor_api.py   ← Create: Integration tests
```

---

## 🔨 Implementation Tasks

### Task A.1: FastAPI Dependencies (2h)

**File**: `orchestrator/api/dependencies.py`

**Requirements**:
- `get_db()` - Database session injection
- `get_current_user()` - JWT token validation
- `require_scope(scope: str)` - Scope checking dependency factory

**Pattern**:
```python
from typing import Annotated, Generator
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError

from orchestrator.core.database import get_db
from orchestrator.core.auth import verify_token, TokenData, check_scope

security = HTTPBearer()

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(security)]
) -> TokenData:
    """
    Validate JWT token and return user data.

    Raises:
        HTTPException: 401 if token invalid
    """
    try:
        token_data = verify_token(credentials.credentials)
        return token_data
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )

def require_scope(required_scope: str):
    """Dependency factory for scope checking"""
    def check_scope_dependency(
        user: Annotated[TokenData, Depends(get_current_user)]
    ) -> TokenData:
        if required_scope not in user.scopes:
            raise HTTPException(
                status_code=403,
                detail=f"Missing required scope: {required_scope}"
            )
        return user
    return check_scope_dependency
```

---

### Task A.2: Supervisor API Endpoints (4h)

**File**: `orchestrator/api/supervisor_api.py`

**Endpoints** (from API_SPECIFICATION.yaml):

#### 1. GET /api/supervisor/workers

List all workers with filters.

**Query Params**:
- workspace_id (optional)
- status (optional)
- limit (default: 50, max: 100)
- offset (default: 0)

**Response**:
```json
{
  "workers": [{"id": "w_abc", "status": "RUNNING", ...}],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

**Pattern**:
```python
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from orchestrator.core.database import get_db
from orchestrator.core.db_models import Worker, WorkerStatus
from orchestrator.api.dependencies import require_scope

router = APIRouter(prefix="/api/supervisor", tags=["supervisor"])

class WorkerResponse(BaseModel):
    id: str
    workspace_id: str
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class WorkerListResponse(BaseModel):
    workers: List[WorkerResponse]
    total: int
    limit: int
    offset: int

@router.get("/workers", response_model=WorkerListResponse)
async def list_workers(
    workspace_id: Optional[str] = Query(None),
    status: Optional[WorkerStatus] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: TokenData = Depends(require_scope("supervisor:read"))
):
    """List all workers with optional filters"""
    query = db.query(Worker)

    if workspace_id:
        query = query.filter(Worker.workspace_id == workspace_id)
    if status:
        query = query.filter(Worker.status == status)

    total = query.count()
    workers = query.offset(offset).limit(limit).all()

    return WorkerListResponse(
        workers=workers,
        total=total,
        limit=limit,
        offset=offset
    )
```

#### 2. GET /api/supervisor/workers/{worker_id}

Get worker details.

#### 3. POST /api/supervisor/workers/{worker_id}/pause

Pause worker (use WorkerStateMachine).

**Pattern**:
```python
from orchestrator.core.state_machine import WorkerStateMachine

@router.post("/workers/{worker_id}/pause")
async def pause_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    user: TokenData = Depends(require_scope("supervisor:write"))
):
    """Pause worker execution"""
    sm = WorkerStateMachine(db)
    worker = sm.transition_worker(
        worker_id=worker_id,
        to_state=WorkerStatus.PAUSED,
        reason="User paused worker"
    )
    return WorkerResponse.model_validate(worker)
```

#### 4. POST /api/supervisor/workers/{worker_id}/resume

Resume worker.

#### 5. POST /api/supervisor/workers/{worker_id}/terminate

Terminate worker.

#### 6. GET /api/supervisor/metrics

Get aggregate metrics.

**Response**:
```json
{
  "total_workers": 10,
  "by_status": {
    "IDLE": 2,
    "RUNNING": 5,
    "PAUSED": 1,
    "COMPLETED": 2
  }
}
```

---

### Task A.3: Update main.py (1h)

**File**: `orchestrator/api/main.py`

**Changes**:
```python
from orchestrator.api import supervisor_api

app.include_router(supervisor_api.router)
```

---

### Task A.4: Integration Tests (1h)

**File**: `tests/integration/test_supervisor_api.py`

**Requirements**:
- Test all 6 endpoints
- Happy path + error cases
- Use TestClient from FastAPI

**Pattern**:
```python
from fastapi.testclient import TestClient
from orchestrator.api.main import app
from orchestrator.core.auth import create_dev_token

client = TestClient(app)

def test_list_workers():
    """Test GET /api/supervisor/workers"""
    token = create_dev_token()
    response = client.get(
        "/api/supervisor/workers",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "workers" in response.json()

def test_pause_worker():
    """Test POST /api/supervisor/workers/{id}/pause"""
    # Create test worker first
    # Then test pause
    pass
```

---

## ✅ Success Criteria

- [ ] All 6 endpoints functional
- [ ] JWT authentication working
- [ ] State machine transitions validated
- [ ] Integration tests pass
- [ ] No TODO/FIXME/HACK comments
- [ ] Functions ≤50 lines
- [ ] Comprehensive docstrings

---

## 📚 Reference Documents

**API Spec**: `tools/parallel-coding/docs/API_SPECIFICATION.yaml:32-200`
**Models**: `orchestrator/core/db_models.py:95-189`
**State Machine**: `orchestrator/core/state_machine.py:101-182`
**Auth**: `orchestrator/core/auth.py`

---

## 🔧 Development Commands

```bash
# Run API server
cd tools/parallel-coding
uvicorn orchestrator.api.main:app --reload --port 8000

# Test endpoints
pytest tests/integration/test_supervisor_api.py -v

# Manual testing
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/supervisor/workers
```

---

**Remember**: Use Codex worker. Apply Excellence AI Standard. Functions ≤50 lines, NO TODO/FIXME/HACK.

Good luck, Task A Worker! 🚀
