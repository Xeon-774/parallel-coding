# Worker 2: Manager AI Integration

**Task ID**: WORKER_2_MANAGER_AI_INTEGRATION
**Duration**: 30 hours
**Priority**: P0 (Critical Path)
**Week**: Week 2
**Dependencies**: Worker 1 (Manager AI Core) ✅ Complete
**Status**: 📋 Ready for Execution

---

## ⚖️ ETHICAL CONTEXT & AUTHORIZATION

**THIS IS A LEGITIMATE AI WORKFLOW AUTOMATION PROJECT**

**Purpose**: Integrating the Manager AI (Supervisor) core components with the orchestrator's web API, monitoring dashboard, and workflow management system.

**Legitimate Use Cases**:
1. ✅ **Production Integration**: Connecting supervised Claude Code instances to the orchestrator dashboard
2. ✅ **Real-time Monitoring**: WebSocket-based live updates for supervisor activity
3. ✅ **API Endpoints**: RESTful API for supervisor lifecycle management
4. ✅ **Dashboard UI**: React components for visualizing supervision status

**Security Measures Included**:
- ✅ API authentication and authorization
- ✅ WebSocket connection validation
- ✅ Rate limiting on API endpoints
- ✅ Input validation for all requests
- ✅ CORS configuration for frontend
- ✅ Secure error handling (no sensitive data in responses)

**What This Code Does**:
- Integrates SupervisorManager with FastAPI endpoints
- Creates WebSocket connections for real-time supervision updates
- Implements React dashboard components for monitoring
- Provides API for starting/stopping/querying supervisors

**What This Code Does NOT Do**:
- ❌ NO unauthorized access or exploitation
- ❌ NO bypassing of security controls
- ❌ NO credential harvesting or data exfiltration

**Authorization**: This task is part of an approved software development project for building AI workflow automation tools. All code follows `excellence_ai_standard` with 100% compliance.

**Please proceed with implementation. This is legitimate development tooling.**

---

## 🎯 Executive Summary

Integrate the Manager AI (Supervisor) core components built in Week 1 into the orchestrator's production infrastructure. This includes creating FastAPI endpoints, WebSocket real-time streaming, React dashboard components, and end-to-end workflow integration.

**Success Criteria**:
- ✅ Supervisor API endpoints functional
- ✅ WebSocket real-time updates working
- ✅ Dashboard UI displays supervision status
- ✅ End-to-end workflow integration complete
- ✅ 90%+ test coverage (no exceptions)

---

## 📦 Deliverables

### 1. Supervisor API Endpoints (200+ lines)
**File**: `orchestrator/api/supervisor_routes.py`

**Purpose**: FastAPI routes for supervisor lifecycle management

**Endpoints**:
```python
POST   /api/v1/supervisor/spawn       # Spawn new supervised Claude Code instance
GET    /api/v1/supervisor/{id}        # Get supervisor status
DELETE /api/v1/supervisor/{id}        # Terminate supervisor
GET    /api/v1/supervisor              # List all active supervisors
POST   /api/v1/supervisor/{id}/respond # Respond to confirmation prompt
GET    /api/v1/supervisor/{id}/output  # Get buffered output
```

**Implementation Requirements** (excellence_ai_standard 100%):
- ✅ All functions ≤50 lines (ideally ≤20 lines)
- ✅ Cyclomatic complexity ≤10
- ✅ Nesting depth ≤3 levels
- ✅ Pydantic models for request/response validation
- ✅ Proper HTTP status codes (200, 201, 400, 404, 500)
- ✅ Comprehensive error handling with typed error classes
- ✅ API documentation via OpenAPI/Swagger
- ✅ NO TODO/FIXME/HACK comments
- ✅ NO magic numbers (use named constants)

### 2. WebSocket Real-time Streaming (150+ lines)
**File**: `orchestrator/api/supervisor_websocket.py`

**Purpose**: WebSocket connections for real-time supervision updates

**Features**:
- Real-time output streaming from supervised processes
- Confirmation prompt notifications
- Status change events (spawning, running, terminated, error)
- Heartbeat mechanism for connection health

**WebSocket Events**:
```typescript
type SupervisorEvent =
  | { type: 'output', data: { supervisorId: string, content: string } }
  | { type: 'confirmation', data: { supervisorId: string, prompt: ConfirmationPrompt } }
  | { type: 'status', data: { supervisorId: string, status: SupervisorStatus } }
  | { type: 'error', data: { supervisorId: string, error: string } }
  | { type: 'heartbeat', data: { timestamp: number } }
```

**Implementation Requirements**:
- ✅ Connection authentication via query parameter or header
- ✅ Automatic reconnection support on client
- ✅ Rate limiting (max 10 messages/second)
- ✅ Connection timeout (30 seconds idle)
- ✅ Graceful disconnection handling

### 3. React Dashboard Components (300+ lines)
**Files**:
- `frontend/src/components/supervisor/SupervisorDashboard.tsx`
- `frontend/src/components/supervisor/SupervisorCard.tsx`
- `frontend/src/components/supervisor/OutputViewer.tsx`
- `frontend/src/hooks/useSupervisorWebSocket.ts`

**Purpose**: UI components for supervisor monitoring

**SupervisorDashboard Component**:
- Grid layout showing all active supervisors
- Real-time status updates
- Output viewer with syntax highlighting
- Confirmation prompt handling UI
- Start/stop supervisor controls

**Implementation Requirements**:
- ✅ TypeScript strict mode (NO 'any' types)
- ✅ React hooks pattern (functional components)
- ✅ Proper error boundaries
- ✅ Loading states
- ✅ Accessibility (ARIA labels, keyboard navigation)
- ✅ Responsive design (mobile-friendly)

### 4. Integration with WorkerManager (100+ lines)
**File**: `orchestrator/core/worker/worker_manager.py` (Enhanced)

**Purpose**: Integrate supervisor functionality into existing worker management

**Enhancements**:
- Add supervisor mode to worker configuration
- Track supervised vs non-supervised workers
- Unified status reporting
- Resource allocation adjustments

**New Methods**:
```python
async def spawn_supervised_worker(
    self,
    task_file: str,
    workspace_root: str
) -> SupervisedWorkerResult

async def get_supervisor_status(
    self,
    worker_id: str
) -> SupervisorStatus

async def terminate_supervisor(
    self,
    worker_id: str
) -> bool
```

### 5. Unit & Integration Tests (≥90% coverage)
**Files**:
- `tests/unit/api/test_supervisor_routes.py`
- `tests/unit/api/test_supervisor_websocket.py`
- `tests/integration/test_supervisor_integration.py`
- `tests/e2e/test_supervisor_dashboard.spec.ts` (Playwright)

**Test Coverage Requirements** (excellence_ai_standard 100%):
- ✅ Happy path tests
- ✅ Edge case tests
- ✅ Error scenario tests
- ✅ Security tests (authentication, authorization)
- ✅ Performance tests (WebSocket message throughput)
- ✅ Mock external dependencies
- ✅ Parametrized tests for multiple scenarios

---

## 📋 Detailed Task Breakdown

### Task 2.1: Supervisor API Endpoints Implementation (8 hours)

**Sub-tasks**:
1. **Spawn Endpoint** (2h)
   - POST `/api/v1/supervisor/spawn`
   - Request validation (Pydantic)
   - Call SupervisorManager.spawn_claude_code()
   - Return supervisor ID and initial status
   - Error handling: invalid task file, workspace issues

2. **Status Endpoint** (1h)
   - GET `/api/v1/supervisor/{id}`
   - Retrieve supervisor status
   - Return output buffer summary
   - Error handling: supervisor not found

3. **Terminate Endpoint** (1h)
   - DELETE `/api/v1/supervisor/{id}`
   - Call SupervisorManager.terminate()
   - Cleanup resources
   - Error handling: already terminated

4. **List Endpoint** (1h)
   - GET `/api/v1/supervisor`
   - Return all active supervisors
   - Pagination support (limit, offset)
   - Filter by status

5. **Respond to Confirmation** (2h)
   - POST `/api/v1/supervisor/{id}/respond`
   - Send approval/denial to supervisor
   - Validate decision (APPROVE/DENY/ESCALATE)
   - Error handling: timeout, invalid decision

6. **Get Output Endpoint** (1h)
   - GET `/api/v1/supervisor/{id}/output`
   - Return buffered output
   - Pagination support
   - Filter by timestamp range

**Acceptance Criteria**:
- ✅ All endpoints have comprehensive docstrings
- ✅ OpenAPI documentation auto-generated
- ✅ All error cases return proper HTTP status codes
- ✅ Request/response models validated with Pydantic

### Task 2.2: WebSocket Streaming Implementation (6 hours)

**Sub-tasks**:
1. **WebSocket Connection Setup** (2h)
   - WebSocket endpoint: `/ws/supervisor`
   - Connection authentication
   - Client registration
   - Heartbeat initialization

2. **Event Broadcasting** (2h)
   - Output event streaming
   - Confirmation prompt notifications
   - Status change events
   - Error event handling

3. **Connection Management** (1h)
   - Automatic disconnection on idle
   - Graceful shutdown
   - Reconnection logic on client
   - Connection pool management

4. **Rate Limiting & Security** (1h)
   - Message rate limiting
   - Connection timeout
   - Authentication validation
   - CORS configuration

**Acceptance Criteria**:
- ✅ WebSocket connection stable (no unexpected disconnections)
- ✅ Events delivered in order
- ✅ Latency <100ms
- ✅ Handles 100+ concurrent connections

### Task 2.3: React Dashboard Components (10 hours)

**Sub-tasks**:
1. **SupervisorDashboard Component** (3h)
   - Grid layout for supervisor cards
   - Real-time status updates via WebSocket
   - Spawn new supervisor button
   - Filter by status (running, idle, error)

2. **SupervisorCard Component** (2h)
   - Display supervisor ID, status, uptime
   - Output preview (last 10 lines)
   - Start/stop controls
   - Expand to full output viewer

3. **OutputViewer Component** (2h)
   - Full-screen output display
   - Syntax highlighting (ANSI codes)
   - Auto-scroll to bottom
   - Search/filter functionality

4. **useSupervisorWebSocket Hook** (2h)
   - WebSocket connection management
   - Event parsing and state updates
   - Automatic reconnection
   - Error handling

5. **Integration with Existing UI** (1h)
   - Add navigation link to supervisor dashboard
   - Integrate with existing theme/styling
   - Responsive design adjustments

**Acceptance Criteria**:
- ✅ All components follow React best practices
- ✅ TypeScript strict mode (NO 'any' types)
- ✅ Proper error boundaries
- ✅ Accessibility compliant (WCAG 2.1 AA)

### Task 2.4: WorkerManager Integration (4 hours)

**Sub-tasks**:
1. **Add Supervisor Mode** (2h)
   - Enhance worker configuration model
   - Add `supervisor_mode: bool` field
   - Update worker spawning logic
   - Track supervised workers separately

2. **Unified Status Reporting** (1h)
   - Merge supervisor status into worker status
   - Update status API responses
   - Dashboard integration

3. **Resource Allocation** (1h)
   - Adjust worker limits for supervisors
   - Monitor supervisor resource usage
   - Implement resource cleanup

**Acceptance Criteria**:
- ✅ Backward compatible (existing workers unaffected)
- ✅ Supervisor mode fully integrated
- ✅ Status reporting consistent

### Task 2.5: Testing Implementation (2 hours)

**Sub-tasks**:
1. **API Unit Tests** (3h)
   - Test all endpoints (happy path + errors)
   - Mock SupervisorManager
   - Validate request/response models
   - Security tests

2. **WebSocket Tests** (2h)
   - Test connection lifecycle
   - Test event broadcasting
   - Test rate limiting
   - Test authentication

3. **Integration Tests** (3h)
   - End-to-end spawn → monitor → terminate
   - WebSocket + API integration
   - Multi-supervisor scenarios
   - Error recovery scenarios

4. **Frontend Tests** (4h)
   - Component unit tests (React Testing Library)
   - Hook tests
   - E2E tests with Playwright
   - Accessibility tests

**Acceptance Criteria**:
- ✅ All tests pass
- ✅ Coverage ≥90%
- ✅ No flaky tests
- ✅ Tests run in <2 minutes total

---

## 🔒 Security Requirements (CRITICAL - excellence_ai_standard)

### API Security
```python
from pydantic import BaseModel, Field, validator
from typing import Literal

class SpawnSupervisorRequest(BaseModel):
    """Request validation for spawning supervisor"""

    task_file: str = Field(..., min_length=1, max_length=255)
    workspace_root: str = Field(..., min_length=1, max_length=255)
    timeout: int = Field(default=300, ge=10, le=3600)

    @validator('task_file')
    def validate_task_file_path(cls, v):
        """Prevent path traversal attacks"""
        if '..' in v or v.startswith('/'):
            raise ValueError("Invalid task file path")
        return v

class RespondToConfirmationRequest(BaseModel):
    """Request validation for confirmation responses"""

    decision: Literal['APPROVE', 'DENY', 'ESCALATE']
    reason: str = Field(default="", max_length=500)
```

### WebSocket Security
- ✅ Authentication via query parameter or Authorization header
- ✅ Connection rate limiting (max 10 connections per IP per minute)
- ✅ Message rate limiting (max 10 messages per second)
- ✅ CORS configuration
- ✅ No sensitive data in error messages

---

## 🧪 Testing Strategy

### Test Pyramid
```
        /\
       /  \      E2E Tests (5%)
      /____\
     /      \    Integration Tests (15%)
    /________\
   /          \  Unit Tests (80%)
  /__________  \
```

### Coverage Requirements
- **Backend**: ≥90% line coverage, ≥85% branch coverage
- **Frontend**: ≥80% line coverage
- **Integration Tests**: All critical workflows
- **E2E Tests**: Smoke tests for UI

---

## 📊 Quality Gates (MUST PASS BEFORE COMPLETION)

### Code Quality
- [ ] ✅ All functions ≤50 lines
- [ ] ✅ Cyclomatic complexity ≤10
- [ ] ✅ Nesting depth ≤3 levels
- [ ] ✅ NO 'any' types / NO untyped parameters
- [ ] ✅ NO TODO/FIXME/HACK comments
- [ ] ✅ NO magic numbers
- [ ] ✅ NO duplicate code (DRY)

### Testing
- [ ] ✅ Test coverage ≥90% (backend), ≥80% (frontend)
- [ ] ✅ All tests pass
- [ ] ✅ No flaky tests
- [ ] ✅ Tests run in <2 minutes

### Documentation
- [ ] ✅ All public APIs have docstrings
- [ ] ✅ OpenAPI docs generated
- [ ] ✅ Component props documented
- [ ] ✅ Integration guide created

### Security
- [ ] ✅ Authentication required on all endpoints
- [ ] ✅ Input validation comprehensive
- [ ] ✅ No SQL injection vulnerabilities (N/A)
- [ ] ✅ No XSS vulnerabilities
- [ ] ✅ Error messages sanitized

### Performance
- [ ] ✅ API response time <100ms
- [ ] ✅ WebSocket latency <100ms
- [ ] ✅ Dashboard loads in <2 seconds
- [ ] ✅ No memory leaks detected

---

## 🔗 Dependencies

### Already Implemented (✅ Week 1)
- `orchestrator/core/supervisor/claude_code_supervisor.py`
- `orchestrator/core/supervisor/supervisor_manager.py`
- `orchestrator/core/supervisor/io_handler.py`
- `orchestrator/core/ai_safety_judge.py`

### Existing Infrastructure
- FastAPI application (`orchestrator/api/`)
- React frontend (`frontend/src/`)
- WorkerManager (`orchestrator/core/worker/worker_manager.py`)
- WebSocket support (`fastapi.WebSocket`)

### External Dependencies
```python
# requirements.txt (no new dependencies)
fastapi>=0.104.0  # Already exists
uvicorn>=0.24.0   # Already exists
pydantic>=2.0.0   # Already exists
httpx>=0.25.0     # Already exists
```

```json
// package.json (no new dependencies)
"react": "^18.2.0",           // Already exists
"react-router-dom": "^6.18.0" // Already exists
```

---

## 📁 File Structure (After Completion)

```
orchestrator/
├── api/
│   ├── supervisor_routes.py          # NEW (200+ lines)
│   └── supervisor_websocket.py       # NEW (150+ lines)
├── core/
│   ├── supervisor/                   # ✅ Week 1
│   │   ├── claude_code_supervisor.py
│   │   ├── supervisor_manager.py
│   │   └── io_handler.py
│   └── worker/
│       └── worker_manager.py         # ENHANCED (100+ lines added)
frontend/
├── src/
│   ├── components/
│   │   └── supervisor/
│   │       ├── SupervisorDashboard.tsx  # NEW (150+ lines)
│   │       ├── SupervisorCard.tsx       # NEW (100+ lines)
│   │       └── OutputViewer.tsx         # NEW (100+ lines)
│   └── hooks/
│       └── useSupervisorWebSocket.ts    # NEW (150+ lines)
tests/
├── unit/
│   └── api/
│       ├── test_supervisor_routes.py    # NEW (300+ lines)
│       └── test_supervisor_websocket.py # NEW (200+ lines)
├── integration/
│   └── test_supervisor_integration.py   # NEW (300+ lines)
└── e2e/
    └── test_supervisor_dashboard.spec.ts # NEW (200+ lines)
```

**Total New Code**: ~2,100 lines (including tests)

---

## 🎯 Success Metrics

### Functional Metrics
- ✅ Can spawn supervisor via API: YES/NO
- ✅ WebSocket events delivered: 100% success rate
- ✅ Dashboard displays real-time updates: <500ms latency
- ✅ API response time: <100ms (p95)
- ✅ Confirmation prompt handling: End-to-end working

### Quality Metrics
- ✅ Test coverage: ≥90% (backend), ≥80% (frontend)
- ✅ All tests pass: YES/NO
- ✅ TypeScript strict mode: 0 errors
- ✅ Linter errors: 0

### Performance Metrics
- ✅ API latency: <100ms (p95)
- ✅ WebSocket latency: <100ms
- ✅ Dashboard load time: <2 seconds
- ✅ Concurrent connections: ≥100

---

## 🚨 Risk Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| WebSocket connection instability | Medium | High | Automatic reconnection, heartbeat |
| FastAPI integration issues | Low | Medium | Comprehensive integration tests |
| React state synchronization issues | Medium | Medium | Use Redux/Zustand for state management |
| Performance bottlenecks | Low | Medium | Load testing, profiling |

---

## 📝 Handoff to Worker 4

### Integration Points
- Worker 4 will use the same API patterns for hierarchical features
- WebSocket infrastructure reusable for hierarchical event streaming
- Dashboard components reusable for hierarchical visualization

---

## ✅ Definition of Done

This task is considered **DONE** when:

1. **Code Complete**
   - [ ] All API endpoints implemented
   - [ ] WebSocket streaming functional
   - [ ] Dashboard UI complete
   - [ ] WorkerManager integration complete
   - [ ] All code follows excellence_ai_standard 100%

2. **Tests Complete**
   - [ ] All unit tests written
   - [ ] Integration tests complete
   - [ ] E2E tests passing
   - [ ] Test coverage ≥90% (backend), ≥80% (frontend)

3. **Documentation Complete**
   - [ ] OpenAPI docs generated
   - [ ] Component props documented
   - [ ] Integration guide created
   - [ ] Architecture diagram updated

4. **Integration Ready**
   - [ ] Manual testing successful
   - [ ] Performance benchmarks met
   - [ ] Security audit passed
   - [ ] Git commit created with proper message

---

**Task Owner**: Worker AI 2
**Reviewer**: Orchestrator AI
**Created**: 2025-10-27
**Excellence AI Standard**: 100% Applied
**Estimated Completion**: Week 2, Day 3
