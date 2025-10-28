# Week 2: Manager AI Integration - MVP Specification

**Document Version**: 1.0
**Created**: 2025-10-28
**Status**: Active
**Based on**: Codex Review Feedback (2025-10-28)

---

## Executive Summary

This document defines the Minimum Viable Product (MVP) for Week 2, focusing on Manager AI Integration with realistic scope and timelines based on AI review feedback.

**Key Changes from Original Plan**:
- Timeline: 50h → 90-120h (2 weeks instead of 1)
- Scope: Split into Week 2 (core backend) + Week 3 (integration & polish)
- Coverage: 70-80% (Week 2) → 90% (Week 3)
- Architecture: Contract-first design with clear technical decisions

---

## 1. Scope Definition

### 1.1 Worker 2: Supervisor API (Week 2 - 50h)

**Goal**: Enable Manager AI to monitor and control Claude Code worker instances via REST API.

#### Components

**A. Supervisor REST API** (20h)
- Endpoints:
  - `GET /api/supervisor/workers` - List all workers with status
  - `GET /api/supervisor/workers/{id}` - Get worker details
  - `POST /api/supervisor/workers/{id}/pause` - Pause worker
  - `POST /api/supervisor/workers/{id}/resume` - Resume worker
  - `POST /api/supervisor/workers/{id}/terminate` - Terminate worker
  - `GET /api/supervisor/metrics` - Get aggregate metrics

**B. Worker State Management** (15h)
- State Machine:
  ```
  IDLE → RUNNING → PAUSED → RUNNING
       → RUNNING → COMPLETED
       → RUNNING → FAILED → RETRYING → RUNNING
       → RUNNING → TERMINATED
  ```
- Persistence: SQLite/Postgres (decision required)
- Idempotency: Use request IDs for all state-changing operations

**C. Authentication & Authorization** (8h)
- JWT Bearer tokens
- Scopes: `supervisor:read`, `supervisor:write`
- Multi-tenant isolation (workspace-level)

**D. Testing & Documentation** (7h)
- API contract tests (OpenAPI 3.0)
- Unit tests for state machine
- Integration tests for happy paths
- Target: 75% coverage minimum

#### Acceptance Criteria
- [ ] All 6 API endpoints functional
- [ ] State transitions validated with unit tests
- [ ] API documented with OpenAPI spec
- [ ] Authentication working with test tokens
- [ ] 75%+ test coverage
- [ ] Postman collection for manual testing

#### Out of Scope (Deferred to Week 3)
- WebSocket real-time streaming
- Advanced retry policies
- Multi-worker orchestration
- Performance optimization
- 90% test coverage

---

### 1.2 Worker 4: Hierarchical Resource Management (Week 2 - 40h)

**Goal**: Implement resource quotas and job orchestration for hierarchical AI execution.

#### Components

**A. Resource Manager API** (15h)
- Endpoints:
  - `GET /api/resources/quotas` - Get resource quotas by depth
  - `POST /api/resources/allocate` - Allocate resources for job
  - `POST /api/resources/release` - Release resources
  - `GET /api/resources/usage` - Current resource usage

**B. Job Orchestrator** (15h)
- Job lifecycle:
  ```
  SUBMITTED → PENDING → RUNNING → COMPLETED
           → PENDING → RUNNING → FAILED
           → PENDING → CANCELED
  ```
- Depth-based resource allocation (max depth: 5)
- Concurrent job limit per depth level
- Job dependency tracking

**C. Persistence Layer** (5h)
- Database: SQLite (development) / Postgres (production)
- Tables:
  - `jobs` - Job metadata and state
  - `resources` - Resource allocations
  - `job_hierarchy` - Parent-child relationships

**D. Testing** (5h)
- Unit tests for resource allocation logic
- Integration tests for job lifecycle
- Target: 70% coverage minimum

#### Acceptance Criteria
- [ ] Resource quotas enforced per depth
- [ ] Job state machine functional
- [ ] Database schema with migrations
- [ ] 70%+ test coverage
- [ ] Can execute 2-level hierarchical jobs

#### Out of Scope (Deferred to Week 3)
- Distributed job execution
- Job retry with exponential backoff
- Advanced scheduling algorithms
- Real-time job monitoring UI

---

## 2. Technical Architecture Decisions

### 2.1 WebSocket Architecture (Deferred to Week 3)

**Decision**: Defer real-time streaming to Week 3 after core APIs are stable.

**Week 3 Decisions Required**:
- Library: Socket.IO vs native WebSocket
- Authentication: Token validation on connect
- Scaling: Sticky sessions vs Redis pub/sub
- Reconnection: Exponential backoff policy
- Message schema: JSON event format

**Rationale**: Focus Week 2 on stable REST APIs before adding streaming complexity.

---

### 2.2 Authentication Strategy

**Decision**: JWT Bearer tokens with scope-based authorization

**Implementation**:
```python
# Token format
{
  "sub": "user_id",
  "scopes": ["supervisor:read", "supervisor:write"],
  "workspace_id": "ws_123",
  "exp": 1234567890
}
```

**Validation**:
- Use `pyjwt` library
- Verify signature with secret key
- Check expiration and scopes
- Extract workspace_id for tenant isolation

---

### 2.3 Database Strategy

**Development**: SQLite (file-based, simple setup)
**Production**: PostgreSQL (recommended for multi-worker scenarios)

**Migration Tool**: Alembic

**Schema Design**:
```sql
-- Supervisor schema
CREATE TABLE workers (
    id VARCHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(36) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    metadata JSONB
);

CREATE TABLE state_transitions (
    id SERIAL PRIMARY KEY,
    worker_id VARCHAR(36) NOT NULL,
    from_state VARCHAR(20),
    to_state VARCHAR(20) NOT NULL,
    reason TEXT,
    timestamp TIMESTAMP NOT NULL
);

-- Resource management schema
CREATE TABLE jobs (
    id VARCHAR(36) PRIMARY KEY,
    parent_job_id VARCHAR(36),
    depth INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP
);

CREATE TABLE resource_allocations (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL,
    depth INTEGER NOT NULL,
    worker_count INTEGER NOT NULL,
    allocated_at TIMESTAMP NOT NULL,
    released_at TIMESTAMP
);
```

---

### 2.4 Error Handling Strategy

**Principle**: Fail fast with clear error messages

**HTTP Status Codes**:
- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing/invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - State transition conflict
- `500 Internal Server Error` - Unexpected error

**Error Response Format**:
```json
{
  "error": {
    "code": "INVALID_STATE_TRANSITION",
    "message": "Cannot pause worker in COMPLETED state",
    "details": {
      "worker_id": "w_123",
      "current_state": "COMPLETED",
      "requested_state": "PAUSED"
    }
  }
}
```

---

## 3. Use Cases

### 3.1 Supervisor API Use Cases

#### UC-1: Monitor All Workers
```
Actor: Manager AI
Precondition: Authenticated with supervisor:read scope
Flow:
1. GET /api/supervisor/workers
2. System returns list of all workers with status
3. Manager AI displays worker dashboard
Postcondition: Worker statuses displayed
```

#### UC-2: Pause Runaway Worker
```
Actor: Manager AI
Precondition: Worker w_123 is RUNNING and consuming excessive resources
Flow:
1. POST /api/supervisor/workers/w_123/pause
2. System validates state transition (RUNNING → PAUSED)
3. System sends pause signal to worker
4. System updates worker state to PAUSED
5. System logs state transition
Postcondition: Worker paused, resources released
```

#### UC-3: Resume Paused Worker
```
Actor: Manager AI
Precondition: Worker w_123 is PAUSED
Flow:
1. POST /api/supervisor/workers/w_123/resume
2. System validates state transition (PAUSED → RUNNING)
3. System sends resume signal to worker
4. System updates worker state to RUNNING
Postcondition: Worker resumed
```

---

### 3.2 Resource Management Use Cases

#### UC-4: Submit Hierarchical Job
```
Actor: Client
Precondition: Resources available at depth 0
Flow:
1. POST /api/jobs with task definition
2. System checks resource quota at depth 0
3. System allocates resources (1 worker at depth 0)
4. System creates job record with status=PENDING
5. System transitions job to RUNNING
6. System executes job (may spawn sub-jobs)
Postcondition: Job running with resources allocated
```

#### UC-5: Spawn Sub-Job
```
Actor: Running Job (depth 0)
Precondition: Parent job needs to spawn child task
Flow:
1. POST /api/jobs with parent_job_id and depth=1
2. System validates depth < max_depth (5)
3. System checks resource quota at depth 1
4. System allocates resources (1 worker at depth 1)
5. System creates job record with parent relationship
6. System executes sub-job
Postcondition: Sub-job running at depth 1
```

---

## 4. API Contracts (OpenAPI 3.0)

### 4.1 Supervisor API Contract

```yaml
openapi: 3.0.0
info:
  title: Supervisor API
  version: 1.0.0
  description: Manager AI supervision and control API

paths:
  /api/supervisor/workers:
    get:
      summary: List all workers
      security:
        - bearerAuth: [supervisor:read]
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
                properties:
                  workers:
                    type: array
                    items:
                      $ref: '#/components/schemas/Worker'

  /api/supervisor/workers/{id}/pause:
    post:
      summary: Pause worker
      security:
        - bearerAuth: [supervisor:write]
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Worker paused
        '409':
          description: Invalid state transition

components:
  schemas:
    Worker:
      type: object
      required:
        - id
        - status
        - workspace_id
      properties:
        id:
          type: string
          example: "w_abc123"
        status:
          type: string
          enum: [IDLE, RUNNING, PAUSED, COMPLETED, FAILED, TERMINATED]
        workspace_id:
          type: string
        created_at:
          type: string
          format: date-time
        metadata:
          type: object

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

---

## 5. Timeline & Milestones

### Week 2 Schedule (90h total, split 2 developers)

**Day 1-2: Design & Contracts** (16h)
- [ ] Complete MVP spec review
- [ ] Design database schema
- [ ] Write OpenAPI contracts
- [ ] Set up project structure
- [ ] Create integration test harness

**Day 3-5: Core Implementation** (40h)
- [ ] Supervisor API endpoints (Worker 2)
- [ ] Worker state machine (Worker 2)
- [ ] Resource Manager API (Worker 4)
- [ ] Job Orchestrator (Worker 4)
- [ ] Database layer with migrations

**Day 6-7: Authentication & Testing** (24h)
- [ ] JWT authentication
- [ ] Unit tests (target: 75% coverage)
- [ ] Integration tests (happy paths)
- [ ] API documentation

**Day 8: Integration & Stabilization** (10h)
- [ ] WorkerManager integration
- [ ] End-to-end testing
- [ ] Bug fixes
- [ ] Deployment prep

### Week 3 Schedule (30h, deferred features)
- [ ] WebSocket streaming
- [ ] Advanced retry policies
- [ ] Performance optimization
- [ ] Test coverage to 90%
- [ ] Documentation polish

---

## 6. Success Criteria

### Week 2 (MVP)
- [x] MVP specification approved
- [ ] All core API endpoints functional
- [ ] State machines validated with tests
- [ ] Database schema deployed
- [ ] Authentication working
- [ ] 75%+ test coverage
- [ ] OpenAPI documentation complete
- [ ] Can execute 2-level hierarchical job

### Week 3 (Complete)
- [ ] WebSocket streaming functional
- [ ] 90%+ test coverage
- [ ] Performance validated (load testing)
- [ ] Production deployment ready
- [ ] Comprehensive documentation

---

## 7. Risk Mitigation

### High Risks
1. **State transition bugs**: Mitigate with comprehensive state machine tests
2. **Database schema changes**: Use Alembic migrations, test rollbacks
3. **Authentication bypass**: Security audit, penetration testing
4. **Resource leaks**: Add resource cleanup on job failure

### Medium Risks
1. **Integration delays**: Daily sync meetings between workers
2. **Test coverage gaps**: Automated coverage reporting in CI
3. **API contract drift**: Contract-first development, generated stubs

---

## 8. Dependencies

**External**:
- PostgreSQL (or SQLite for development)
- JWT library (pyjwt)
- OpenAPI tools (swagger-ui)

**Internal**:
- WorkerManager (existing)
- HierarchicalResourceManager (existing)
- JobOrchestrator (existing, needs integration)

---

## 9. Out of Scope (Future Work)

**Deferred to Week 3+**:
- WebSocket real-time streaming
- Advanced scheduling algorithms
- Distributed job execution
- Job retry with exponential backoff
- Multi-workspace load balancing
- Grafana dashboards
- React UI components (beyond minimal dashboard)

**Deferred to Later Phases**:
- Machine learning-based worker allocation
- Auto-scaling based on load
- Job result caching
- Workflow templates
- Visual job editor

---

## 10. References

- Codex Review Feedback (2025-10-28)
- Excellence AI Standard
- OpenAPI 3.0 Specification
- JWT RFC 7519

---

**Approval Status**: Pending review
**Next Review**: 2025-10-28 End of Day
