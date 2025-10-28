# Task C: Job Orchestrator API Implementation

**Task ID**: Task C
**Module**: Job Orchestrator API
**Endpoints**: 4 endpoints
**Estimated Time**: 6h
**Worker Type**: Codex Worker (use `--use-codex` flag)

---

## 🎯 Mission

Implement Job Orchestrator API for job submission and lifecycle management.

---

## 📋 Prerequisites (Already Complete)

✅ Database models: `orchestrator/core/db_models.py`
✅ State machine: `orchestrator/core/state_machine.py`
✅ Dependencies: `orchestrator/api/dependencies.py` (Task A creates this)

---

## 📁 Files to Create

```
orchestrator/api/
└── jobs_api.py              ← Create: 4 job endpoints

tests/integration/
└── test_jobs_api.py         ← Create: Integration tests
```

---

## 🔨 Endpoints to Implement

### 1. POST /api/jobs/submit

Submit new job.

**Request**:
```json
{
  "task_description": "Implement Week 2 MVP",
  "worker_count": 3,
  "depth": 0,
  "parent_job_id": null
}
```

**Pattern**:
```python
from orchestrator.core.db_models import Job, JobStatus
from orchestrator.core.state_machine import JobStateMachine

@router.post("/submit")
async def submit_job(
    request: JobSubmitRequest,
    db: Session = Depends(get_db),
    user: TokenData = Depends(require_scope("jobs:write"))
):
    """Submit new job"""
    job = Job(
        depth=request.depth,
        worker_count=request.worker_count,
        task_description=request.task_description,
        parent_job_id=request.parent_job_id,
        status=JobStatus.SUBMITTED
    )
    db.add(job)
    db.commit()

    # Transition to PENDING
    sm = JobStateMachine(db)
    job = sm.transition_job(job.id, JobStatus.PENDING)

    return JobResponse.model_validate(job)
```

### 2. GET /api/jobs/{job_id}

Get job details.

### 3. POST /api/jobs/{job_id}/cancel

Cancel job (use JobStateMachine).

### 4. GET /api/jobs

List jobs with filters.

**Query Params**:
- depth (optional)
- status (optional)
- parent_job_id (optional)
- limit / offset

---

## ✅ Success Criteria

- [ ] All 4 endpoints functional
- [ ] Job state machine working
- [ ] Hierarchical job relationships supported
- [ ] Integration tests pass
- [ ] NO TODO/FIXME/HACK
- [ ] Functions ≤50 lines

---

## 📚 References

**API Spec**: `tools/parallel-coding/docs/API_SPECIFICATION.yaml` (Jobs section)
**Models**: `orchestrator/core/db_models.py:265-398` (Job)
**State Machine**: `orchestrator/core/state_machine.py:231-334` (JobStateMachine)

---

Good luck, Task C Worker! 🚀
