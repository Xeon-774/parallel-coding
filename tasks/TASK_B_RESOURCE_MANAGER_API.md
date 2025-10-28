# Task B: Resource Manager API Implementation

**Task ID**: Task B
**Module**: Resource Manager API
**Endpoints**: 4 endpoints
**Estimated Time**: 6h
**Worker Type**: Codex Worker (use `--use-codex` flag)

---

## 🎯 Mission

Implement Resource Manager API for hierarchical resource allocation and quota management.

---

## 📋 Prerequisites (Already Complete)

✅ Database models: `orchestrator/core/db_models.py`
✅ Dependencies: `orchestrator/api/dependencies.py` (Task A creates this)

---

## 📁 Files to Create

```
orchestrator/api/
└── resources_api.py         ← Create: 4 resource endpoints

tests/integration/
└── test_resources_api.py    ← Create: Integration tests
```

---

## 🔨 Endpoints to Implement

### 1. GET /api/resources/quotas

Get resource quotas by depth level.

**Response**:
```json
{
  "quotas": [
    {"depth": 0, "max_workers": 10},
    {"depth": 1, "max_workers": 30},
    ...
  ]
}
```

### 2. POST /api/resources/allocate

Allocate resources for job.

**Request**:
```json
{
  "job_id": "j_abc123",
  "depth": 1,
  "worker_count": 3
}
```

**Pattern**:
```python
from orchestrator.core.db_models import ResourceAllocation

@router.post("/allocate")
async def allocate_resources(
    request: AllocateRequest,
    db: Session = Depends(get_db),
    user: TokenData = Depends(require_scope("resources:write"))
):
    """Allocate resources for job"""
    allocation = ResourceAllocation(
        job_id=request.job_id,
        depth=request.depth,
        worker_count=request.worker_count
    )
    db.add(allocation)
    db.commit()
    return AllocationResponse.model_validate(allocation)
```

### 3. POST /api/resources/release

Release allocated resources.

### 4. GET /api/resources/usage

Get current resource usage by depth.

**Response**:
```json
{
  "usage": [
    {"depth": 0, "allocated": 5, "available": 5},
    {"depth": 1, "allocated": 15, "available": 15},
    ...
  ]
}
```

---

## ✅ Success Criteria

- [ ] All 4 endpoints functional
- [ ] Resource quota validation working
- [ ] Integration tests pass
- [ ] NO TODO/FIXME/HACK
- [ ] Functions ≤50 lines

---

## 📚 References

**API Spec**: `tools/parallel-coding/docs/API_SPECIFICATION.yaml` (Resource section)
**Models**: `orchestrator/core/db_models.py:465-506` (ResourceAllocation)

---

Good luck, Task B Worker! 🚀
