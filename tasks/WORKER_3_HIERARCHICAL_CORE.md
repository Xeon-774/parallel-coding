# Worker 3: Hierarchical System Core Implementation

**Task ID**: WORKER_3_HIERARCHICAL_CORE
**Duration**: 25 hours
**Priority**: P0 (Critical Path)
**Week**: Week 1
**Dependencies**: Existing REST API, Job Management System (✅ Already implemented)
**Status**: 📋 Ready for Execution

---

## 🎯 Executive Summary

Implement the core infrastructure for the Hierarchical AI System - a recursive orchestration framework that enables Worker AIs to spawn sub-orchestrators, creating enterprise-scale team structures (CTO → PM → Tech Lead → Engineer). This worker focuses on foundational components: recursion configuration, depth validation, and recursive orchestrator client.

**Success Criteria**:
- ✅ Worker AI can call orchestrator recursively
- ✅ Depth limit prevents infinite recursion
- ✅ RecursiveOrchestratorClient works correctly
- ✅ Basic 2-level recursion succeeds
- ✅ 90%+ test coverage (no exceptions)

---

## 📦 Deliverables

### 1. Enhanced Configuration Models (Recursion Fields)
**File**: `orchestrator/api/models.py` (Enhanced, not replaced)

**Purpose**: Add recursion-related fields to existing configuration models

**New Fields to Add**:
```python
from pydantic import BaseModel, Field, validator

class OrchestratorConfigRecursion(BaseModel):
    """Recursion configuration for hierarchical orchestration"""

    # Recursion control
    max_recursion_depth: int = Field(
        default=3,
        ge=0,
        le=5,
        description="Maximum recursion depth (0=no recursion, 5=max)"
    )
    current_depth: int = Field(
        default=0,
        ge=0,
        le=5,
        description="Current recursion depth"
    )

    # Orchestrator endpoint (for recursive calls)
    orchestrator_api_url: str | None = Field(
        default=None,
        description="URL of parent orchestrator API"
    )
    orchestrator_api_key: str | None = Field(
        default=None,
        description="API key for parent orchestrator"
    )

    # Worker allocation by depth
    workers_by_depth: dict[int, int] = Field(
        default_factory=lambda: {
            0: 10,  # Root: 10 workers
            1: 8,   # Level 1: 8 workers
            2: 5,   # Level 2: 5 workers
            3: 3,   # Level 3: 3 workers
            4: 2,   # Level 4: 2 workers
            5: 1,   # Level 5: 1 worker
        },
        description="Max workers per depth level"
    )

    @validator('current_depth')
    def validate_current_depth(cls, v, values):
        """Ensure current depth doesn't exceed max depth"""
        max_depth = values.get('max_recursion_depth', 3)
        if v > max_depth:
            raise ValueError(
                f"Current depth ({v}) exceeds max depth ({max_depth})"
            )
        return v

    @validator('orchestrator_api_url')
    def validate_api_url(cls, v):
        """Validate API URL format"""
        if v is not None:
            if not v.startswith(('http://', 'https://')):
                raise ValueError("API URL must start with http:// or https://")
        return v
```

**Integration Requirements**:
- ✅ Extend existing `OrchestratorConfig` (don't replace)
- ✅ Backward compatible (all new fields have defaults)
- ✅ Zero breaking changes to existing code

### 2. Recursion Depth Validation
**File**: `orchestrator/core/recursion_validator.py` (NEW)

**Purpose**: Validate recursion depth and prevent infinite recursion

**Key Features**:
- Depth validation before spawning sub-orchestrator
- Circular reference detection
- Timeout adjustment based on depth
- Resource limit calculation by depth

**Implementation**:
```python
from typing import Result
from pydantic import BaseModel

class RecursionValidationResult(BaseModel):
    """Result of recursion validation"""
    is_valid: bool
    error_message: str | None = None
    adjusted_timeout: int | None = None
    max_workers: int | None = None

class RecursionValidator:
    """Validates recursion depth and calculates resource limits"""

    @staticmethod
    def validate_depth(
        current_depth: int,
        max_depth: int,
        workers_by_depth: dict[int, int]
    ) -> RecursionValidationResult:
        """
        Validate if recursion is allowed at current depth.

        Args:
            current_depth: Current recursion depth
            max_depth: Maximum allowed depth
            workers_by_depth: Worker limits per depth level

        Returns:
            Validation result with resource limits

        Raises:
            ValidationError: If inputs are invalid
        """
        # Validate inputs
        if current_depth < 0:
            return RecursionValidationResult(
                is_valid=False,
                error_message="Current depth cannot be negative"
            )

        if current_depth >= max_depth:
            return RecursionValidationResult(
                is_valid=False,
                error_message=f"Max recursion depth ({max_depth}) reached"
            )

        # Calculate resource limits
        max_workers = workers_by_depth.get(current_depth + 1, 1)

        # Adjust timeout based on depth (deeper = longer timeout)
        base_timeout = 300  # 5 minutes
        timeout_multiplier = 1.5 ** (current_depth + 1)
        adjusted_timeout = int(base_timeout * timeout_multiplier)

        return RecursionValidationResult(
            is_valid=True,
            error_message=None,
            adjusted_timeout=adjusted_timeout,
            max_workers=max_workers
        )

    @staticmethod
    def detect_circular_reference(
        parent_job_ids: list[str],
        current_job_id: str
    ) -> bool:
        """
        Detect if current job is creating a circular reference.

        Args:
            parent_job_ids: List of parent job IDs in hierarchy
            current_job_id: Current job ID

        Returns:
            True if circular reference detected, False otherwise
        """
        return current_job_id in parent_job_ids
```

**Implementation Requirements** (excellence_ai_standard 100%):
- ✅ All functions ≤50 lines
- ✅ Comprehensive input validation
- ✅ Typed error handling
- ✅ Complete docstrings with examples

### 3. RecursiveOrchestratorClient (300+ lines)
**File**: `orchestrator/recursive/recursive_client.py` (NEW)

**Purpose**: Async HTTP client for Worker AIs to call parent orchestrator recursively

**Key Features**:
- Async HTTP client (using `httpx`)
- Sync wrapper for ease of use
- Job submission and polling
- Result retrieval
- Comprehensive error handling
- Retry logic with exponential backoff

**Implementation**:
```python
import httpx
import asyncio
from typing import Any, AsyncGenerator
from pydantic import BaseModel

class OrchestrateRequest(BaseModel):
    """Request to orchestrator API"""
    request: str
    config: dict[str, Any] | None = None

class JobStatus(BaseModel):
    """Job status response"""
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: dict[str, Any]
    results: dict[str, Any] | None = None

class RecursiveOrchestratorClient:
    """
    Async client for calling orchestrator API recursively.

    This client allows Worker AIs to spawn sub-orchestrators,
    creating hierarchical team structures.

    Usage:
        async with RecursiveOrchestratorClient(
            api_url="http://localhost:8000",
            api_key="sk-orch-key"
        ) as client:
            job_id = await client.submit_job(
                request="Create authentication module",
                max_workers=3,
                current_depth=1
            )

            async for status in client.poll_job(job_id):
                print(f"Progress: {status.progress}")

            results = await client.get_results(job_id)
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        timeout: int = 300,
        max_retries: int = 3
    ):
        """
        Initialize recursive orchestrator client.

        Args:
            api_url: Orchestrator API URL
            api_key: API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts

        Raises:
            ValidationError: If inputs are invalid
        """
        # Input validation
        if not api_url.startswith(('http://', 'https://')):
            raise ValueError("Invalid API URL")

        if not api_key or len(api_key) < 10:
            raise ValueError("Invalid API key")

        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={"X-API-Key": self.api_key},
            timeout=self.timeout
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()

    async def submit_job(
        self,
        request: str,
        max_workers: int = 3,
        current_depth: int = 1,
        parent_job_id: str | None = None
    ) -> str:
        """
        Submit a new orchestration job.

        Args:
            request: Task description
            max_workers: Maximum parallel workers
            current_depth: Current recursion depth
            parent_job_id: Parent job ID (for tracking)

        Returns:
            Job ID

        Raises:
            APIError: If job submission fails
            ValidationError: If inputs are invalid
        """
        if not request or len(request) < 10:
            raise ValueError("Request must be at least 10 characters")

        if max_workers < 1 or max_workers > 10:
            raise ValueError("max_workers must be between 1 and 10")

        payload = OrchestrateRequest(
            request=request,
            config={
                "max_workers": max_workers,
                "current_depth": current_depth,
                "parent_job_id": parent_job_id,
                "enable_ai_analysis": True
            }
        )

        try:
            response = await self.client.post(
                "/api/v1/orchestrate",
                json=payload.model_dump()
            )
            response.raise_for_status()
            data = response.json()
            return data["job_id"]

        except httpx.HTTPStatusError as e:
            raise APIError(f"Job submission failed: {e.response.text}")
        except httpx.RequestError as e:
            raise APIError(f"Network error: {str(e)}")

    async def poll_job(
        self,
        job_id: str,
        poll_interval: int = 5
    ) -> AsyncGenerator[JobStatus, None]:
        """
        Poll job status until completion.

        Args:
            job_id: Job ID to poll
            poll_interval: Polling interval in seconds

        Yields:
            Job status updates

        Raises:
            APIError: If polling fails
        """
        while True:
            try:
                response = await self.client.get(
                    f"/api/v1/jobs/{job_id}/status"
                )
                response.raise_for_status()
                status = JobStatus(**response.json())

                yield status

                if status.status in ("completed", "failed"):
                    break

                await asyncio.sleep(poll_interval)

            except httpx.HTTPStatusError as e:
                raise APIError(f"Failed to poll job: {e.response.text}")

    async def get_results(self, job_id: str) -> dict[str, Any]:
        """
        Get job results.

        Args:
            job_id: Job ID

        Returns:
            Job results

        Raises:
            APIError: If retrieval fails
        """
        try:
            response = await self.client.get(
                f"/api/v1/jobs/{job_id}/results"
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise APIError(f"Failed to get results: {e.response.text}")

# Sync wrapper for ease of use
class RecursiveOrchestratorSyncClient:
    """
    Synchronous wrapper for RecursiveOrchestratorClient.

    Usage:
        client = RecursiveOrchestratorSyncClient(
            api_url="http://localhost:8000",
            api_key="sk-key"
        )
        job_id = client.submit_job("Create module")
        results = client.wait_for_completion(job_id)
    """

    def __init__(self, api_url: str, api_key: str):
        self.async_client = RecursiveOrchestratorClient(api_url, api_key)

    def submit_job(self, request: str, **kwargs) -> str:
        """Submit job synchronously"""
        async def _submit():
            async with self.async_client as client:
                return await client.submit_job(request, **kwargs)
        return asyncio.run(_submit())

    def wait_for_completion(self, job_id: str) -> dict[str, Any]:
        """Wait for job completion synchronously"""
        async def _wait():
            async with self.async_client as client:
                async for status in client.poll_job(job_id):
                    if status.status in ("completed", "failed"):
                        return await client.get_results(job_id)
        return asyncio.run(_wait())
```

**Implementation Requirements** (excellence_ai_standard 100%):
- ✅ Async/await pattern
- ✅ Context manager support
- ✅ Retry with exponential backoff
- ✅ Comprehensive error handling
- ✅ Connection pooling
- ✅ Timeout handling
- ✅ Resource cleanup

### 4. Basic Recursion Tests (8 hours)
**Files**:
- `tests/unit/recursive/test_recursion_validator.py`
- `tests/unit/recursive/test_recursive_client.py`
- `tests/integration/test_2_level_recursion.py`

**Test Coverage Requirements** (excellence_ai_standard 100%):
- ✅ Happy path tests
- ✅ Edge case tests (max depth, boundary conditions)
- ✅ Error scenario tests
- ✅ Security tests (API key validation, URL validation)
- ✅ Performance tests (client overhead <100ms)
- ✅ Integration test: 2-level recursion

**Example Integration Test**:
```python
import pytest
from orchestrator.recursive import RecursiveOrchestratorClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_2_level_recursion_success(orchestrator_api):
    """
    Test 2-level recursive orchestration.

    Hierarchy:
        Root Orchestrator (Depth 0)
            ├─ Worker 1: Submit sub-orchestration
            │   └─ Sub-Orchestrator (Depth 1)
            │       ├─ Worker 1.1: Task A
            │       └─ Worker 1.2: Task B
            └─ Worker 2: Direct task
    """
    # Arrange
    root_client = RecursiveOrchestratorClient(
        api_url="http://localhost:8000",
        api_key="test-key"
    )

    # Act: Root orchestrator submits job
    async with root_client as client:
        root_job_id = await client.submit_job(
            request="""
            Task: Create authentication module
            Sub-tasks:
            1. Database models (delegate to sub-orchestrator)
            2. API endpoints (direct task)
            """,
            max_workers=2,
            current_depth=0
        )

        # Wait for completion
        async for status in client.poll_job(root_job_id):
            if status.status == "completed":
                results = await client.get_results(root_job_id)
                break

    # Assert
    assert results["status"] == "completed"
    assert len(results["results"]["tasks"]) == 2

    # Verify sub-orchestration occurred
    sub_orchestration_task = next(
        t for t in results["results"]["tasks"]
        if "sub-orchestrator" in t["output"].lower()
    )
    assert sub_orchestration_task["success"] is True
```

---

## 📋 Detailed Task Breakdown

### Task 3.1: Config Model Extension (3 hours)

**Sub-tasks**:
1. **Add Recursion Fields** (1h)
   - Add fields to `OrchestratorConfigRecursion`
   - Ensure backward compatibility
   - Update model serialization

2. **Validation Logic** (1h)
   - Implement Pydantic validators
   - Test validation edge cases
   - Error message clarity

3. **Integration Testing** (1h)
   - Test with existing config loading
   - Verify zero breaking changes
   - Test default values

**Acceptance Criteria**:
- ✅ All new fields have defaults
- ✅ Validation works correctly
- ✅ Existing code unaffected
- ✅ Tests pass

### Task 3.2: Recursion Depth Validation (4 hours)

**Sub-tasks**:
1. **RecursionValidator Class** (2h)
   - Implement `validate_depth()` method
   - Implement `detect_circular_reference()` method
   - Resource limit calculation

2. **Timeout Adjustment Logic** (1h)
   - Exponential timeout calculation
   - Testing with various depths
   - Performance validation

3. **Unit Tests** (1h)
   - Happy path tests
   - Boundary condition tests
   - Error case tests

**Acceptance Criteria**:
- ✅ Prevents infinite recursion
- ✅ Timeout increases with depth
- ✅ Worker limits enforced
- ✅ Tests pass

### Task 3.3: RecursiveOrchestratorClient (10 hours)

**Sub-tasks**:
1. **Async Client Implementation** (4h)
   - HTTP client setup (httpx)
   - `submit_job()` method
   - `poll_job()` generator
   - `get_results()` method

2. **Error Handling & Retry** (2h)
   - Retry logic with exponential backoff
   - Typed exception classes
   - Connection error handling

3. **Sync Wrapper** (2h)
   - `RecursiveOrchestratorSyncClient`
   - Asyncio event loop management
   - Thread safety

4. **Unit Tests** (2h)
   - Mock httpx responses
   - Test error scenarios
   - Test retry logic

**Acceptance Criteria**:
- ✅ Async client works correctly
- ✅ Sync wrapper works correctly
- ✅ Retry logic functions
- ✅ Tests pass

### Task 3.4: Basic Tests (8 hours)

**Sub-tasks**:
1. **Unit Tests** (4h)
   - RecursionValidator tests
   - RecursiveOrchestratorClient tests
   - Mock HTTP responses

2. **Integration Test: 2-Level Recursion** (4h)
   - Setup test orchestrator
   - Implement 2-level scenario
   - Verify hierarchy correctness
   - Performance validation

**Acceptance Criteria**:
- ✅ All unit tests pass
- ✅ 2-level recursion succeeds
- ✅ Coverage ≥90%
- ✅ No flaky tests

---

## 🔒 Security Requirements (CRITICAL - excellence_ai_standard)

### API Security
```python
class APIKeyValidator:
    """Validate API keys for recursive calls"""

    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """
        Validate API key format and strength.

        Args:
            api_key: API key to validate

        Returns:
            True if valid, False otherwise

        Raises:
            ValueError: If API key is invalid
        """
        if not api_key:
            raise ValueError("API key cannot be empty")

        if len(api_key) < 32:
            raise ValueError("API key must be at least 32 characters")

        if not api_key.startswith("sk-orch-"):
            raise ValueError("Invalid API key prefix")

        return True
```

### Recursion Security
- ✅ Max depth enforcement (hard limit: 5)
- ✅ Circular reference detection
- ✅ Resource limit enforcement
- ✅ Timeout enforcement
- ✅ No API key logging

### Input Validation
- ✅ URL validation (no file://, javascript:)
- ✅ Request size limits
- ✅ Worker count limits (1-10)
- ✅ Depth validation (0-5)

---

## 🧪 Testing Strategy

### Test Pyramid
```
        /\
       /  \      E2E Tests (10%)
      /____\     2-level recursion
     /      \    Integration Tests (20%)
    /________\   API integration
   /          \  Unit Tests (70%)
  /__________  \ Validator, Client
```

### Coverage Requirements
- **Unit Tests**: ≥90% line coverage
- **Integration Tests**: Critical paths
- **E2E Tests**: 2-level recursion (manual + automated)

### Test Execution
```bash
# Unit tests
pytest tests/unit/recursive/ -v --cov

# Integration tests (requires running orchestrator)
pytest tests/integration/test_2_level_recursion.py -v -s

# Expected: All tests pass, coverage ≥90%
```

---

## 📊 Quality Gates (MUST PASS BEFORE COMPLETION)

### Code Quality
- [ ] ✅ All functions ≤50 lines
- [ ] ✅ Cyclomatic complexity ≤10
- [ ] ✅ NO untyped parameters
- [ ] ✅ NO TODO/FIXME comments
- [ ] ✅ NO magic numbers
- [ ] ✅ Proper error handling

### Testing
- [ ] ✅ Test coverage ≥90%
- [ ] ✅ All tests pass
- [ ] ✅ 2-level recursion works
- [ ] ✅ No flaky tests

### Documentation
- [ ] ✅ All public APIs documented
- [ ] ✅ Usage examples included
- [ ] ✅ Architecture diagram created

### Security
- [ ] ✅ Depth limit enforced
- [ ] ✅ Circular reference prevented
- [ ] ✅ API keys validated
- [ ] ✅ No sensitive data logged

### Performance
- [ ] ✅ Client overhead <100ms
- [ ] ✅ Recursive call latency <500ms
- [ ] ✅ Memory usage <50MB per client

---

## 🔗 Dependencies

### Already Implemented (✅)
- `orchestrator/api/main.py` - REST API server
- `orchestrator/core/job_manager.py` - Job management

### External Dependencies
```python
# requirements.txt additions
httpx>=0.25.0         # Async HTTP client
asyncio              # Standard library
```

---

## 📁 File Structure (After Completion)

```
orchestrator/
├── api/
│   └── models.py                              # ENHANCED (add recursion fields)
├── recursive/
│   ├── __init__.py                            # NEW
│   ├── recursive_client.py                    # NEW (400+ lines)
│   └── recursion_validator.py                 # NEW (200+ lines)
tests/
├── unit/
│   └── recursive/
│       ├── test_recursion_validator.py        # NEW (200+ lines)
│       └── test_recursive_client.py           # NEW (300+ lines)
└── integration/
    └── test_2_level_recursion.py              # NEW (200+ lines)
```

**Total New Code**: ~1,500 lines (including tests)

---

## 🎯 Success Metrics

### Functional Metrics
- ✅ 2-level recursion success rate: 100%
- ✅ Depth validation accuracy: 100%
- ✅ Circular reference detection: 100%

### Quality Metrics
- ✅ Test coverage: ≥90%
- ✅ All tests pass: YES/NO
- ✅ Linter errors: 0

### Performance Metrics
- ✅ Client overhead: <100ms
- ✅ Recursive call latency: <500ms
- ✅ Memory usage: <50MB

---

## 🚨 Risk Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| API endpoint changes | Low | Medium | Version pinning, compatibility layer |
| Network failures | Medium | Medium | Retry logic, timeout handling |
| Infinite recursion bug | Low | High | Hard depth limit, testing |

### Process Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Integration delays | Low | Low | Clear interface contracts |
| Testing complexity | Medium | Low | Incremental testing |

---

## 📝 Handoff to Worker 4

### Interface Contract
```python
from orchestrator.recursive import RecursiveOrchestratorClient

# Worker 4 will use this to implement enterprise features
client = RecursiveOrchestratorClient(
    api_url="http://localhost:8000",
    api_key="sk-orch-key"
)

# Submit hierarchical job
job_id = await client.submit_job(
    request="Create authentication system",
    max_workers=5,
    current_depth=1,
    parent_job_id="root_job_123"
)
```

### Integration Points
- Worker 4 will add hierarchy level naming (CTO, PM, Tech Lead, Engineer)
- Worker 4 will implement organization chart generation
- Worker 4 will add resource optimization logic

---

## ✅ Definition of Done

This task is considered **DONE** when:

1. **Code Complete**
   - [ ] Config models enhanced
   - [ ] RecursionValidator implemented
   - [ ] RecursiveOrchestratorClient implemented
   - [ ] All code follows excellence_ai_standard 100%

2. **Tests Complete**
   - [ ] All unit tests pass
   - [ ] 2-level recursion test passes
   - [ ] Coverage ≥90%

3. **Documentation Complete**
   - [ ] All docstrings written
   - [ ] Usage examples included
   - [ ] Integration guide created

4. **Integration Ready**
   - [ ] Zero breaking changes
   - [ ] Interface contract defined
   - [ ] Manual 2-level test successful

5. **Performance Validated**
   - [ ] All metrics met
   - [ ] No memory leaks
   - [ ] Resource cleanup verified

---

**Task Owner**: Worker AI 3
**Reviewer**: Orchestrator AI
**Created**: 2025-10-25
**Excellence AI Standard**: 100% Applied
**Estimated Completion**: Week 1, Day 3