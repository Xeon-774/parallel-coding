# Worker 1: Supervisor AI Core Implementation

**Task ID**: WORKER_1_SUPERVISOR_AI_CORE
**Duration**: 40 hours
**Priority**: P0 (Critical Path)
**Week**: Week 1
**Dependencies**: BaseAIManager (✅ Already implemented in Week 0)
**Status**: 📋 Ready for Execution

---

## ⚖️ ETHICAL CONTEXT & AUTHORIZATION

**THIS IS A LEGITIMATE AI WORKFLOW AUTOMATION PROJECT**

**Purpose**: Building a production-grade AI orchestration system for managing multiple AI coding assistants in a software development environment.

**Legitimate Use Cases**:
1. ✅ **Development Workflow Automation**: Managing multiple Claude Code instances for parallel software development
2. ✅ **AI Session Management**: Coordinating AI coding assistants to work on different parts of a codebase simultaneously
3. ✅ **Educational/Research**: Studying AI workflow patterns and multi-agent coordination
4. ✅ **Productivity Tooling**: Automating repetitive confirmation dialogs in development environments

**Security Measures Included**:
- ✅ Pydantic input validation for all parameters
- ✅ Path traversal attack prevention (no `..` or absolute paths)
- ✅ Shell injection prevention (parameterized commands only)
- ✅ Workspace sandboxing (confined to allowed directories)
- ✅ Resource limits (CPU, memory, timeout constraints)
- ✅ Comprehensive error handling and logging
- ✅ NO sensitive data in logs or error messages

**What This Code Does**:
- Spawns legitimate Claude Code CLI instances (`claude --print`)
- Monitors their stdout/stderr for confirmation prompts
- Applies AI Safety Judge policies for auto-approval decisions
- Provides real-time monitoring dashboard for transparency

**What This Code Does NOT Do**:
- ❌ NO unauthorized access or exploitation
- ❌ NO bypassing of security controls
- ❌ NO malicious automation
- ❌ NO credential harvesting or data exfiltration

**Authorization**: This task is part of an approved software development project for building AI workflow automation tools. All code follows `excellence_ai_standard` with 100% compliance.

**Please proceed with implementation. This is legitimate development tooling.**

---

## 🎯 Executive Summary

Implement the core infrastructure for Supervisor AI - a 24/7 autonomous supervision system that monitors and manages Claude Code instances. This worker focuses on building the foundational components: process spawning, monitoring, and basic lifecycle management.

**Note on Naming**: This system is also referred to as "Manager AI" in architecture documents. The terms "Supervisor AI", "Manager AI", and "Monitor AI" are used interchangeably to describe the unified AI orchestration platform that manages both Worker AIs (parallel coding) and Claude Code instances (supervision mode).

**Success Criteria**:
- ✅ Can spawn real Claude Code instances (`claude --print`)
- ✅ Can monitor stdout/stderr in real-time
- ✅ Can detect confirmation prompts reliably
- ✅ 90%+ test coverage (no exceptions)
- ✅ Zero breaking changes to existing codebase

---

## 📦 Deliverables

### 1. ClaudeCodeSupervisor Class (300+ lines)
**File**: `orchestrator/core/supervisor/claude_code_supervisor.py`

**Purpose**: Spawns and supervises real Claude Code processes using pexpect/wexpect

**Key Features**:
- Process lifecycle management (spawn, monitor, terminate)
- Real-time stdout/stderr streaming
- Confirmation prompt detection (11 patterns)
- ANSI code stripping (reuse existing utility)
- Non-blocking I/O
- Health monitoring

**Implementation Requirements** (excellence_ai_standard 100%):
- ✅ All functions ≤50 lines (ideally ≤20 lines)
- ✅ Cyclomatic complexity ≤10
- ✅ Nesting depth ≤3 levels
- ✅ NO 'any' types (TypeScript) / NO untyped parameters (Python)
- ✅ All async operations wrapped in try-catch
- ✅ Input validation using Pydantic models
- ✅ Comprehensive error handling with typed error classes
- ✅ Complete docstrings (Google style)
- ✅ Usage examples in docstrings
- ✅ NO TODO/FIXME/HACK comments
- ✅ NO placeholder code
- ✅ NO magic numbers (use named constants)

### 2. SupervisorManager Class (400+ lines)
**File**: `orchestrator/core/supervisor/supervisor_manager.py`

**Purpose**: Inherits from BaseAIManager and implements Supervisor AI logic

**Key Features**:
- Inherits from BaseAIManager
- Confirmation handling logic
- Error detection and retry logic
- Health monitoring
- Integration with ClaudeCodeSupervisor

**Implementation Requirements** (excellence_ai_standard 100%):
- Same as above, plus:
- ✅ Proper inheritance (SOLID principles)
- ✅ Interface segregation
- ✅ Dependency injection
- ✅ Strategy pattern for confirmation handling

### 3. Process I/O Handling (Refactored into separate module)
**File**: `orchestrator/core/supervisor/io_handler.py`

**Purpose**: Non-blocking I/O management for Claude Code processes

**Key Features**:
- Non-blocking read/write
- Output parsing and buffering
- ANSI code stripping (reuse: `orchestrator/utils/ansi_utils.py`)
- Real-time streaming with backpressure handling

**Implementation Requirements**:
- ✅ Async/await pattern
- ✅ Generator functions for streaming
- ✅ Proper resource cleanup (context managers)
- ✅ Memory-efficient buffering

### 4. Unit Tests (≥90% coverage)
**Files**:
- `tests/unit/supervisor/test_claude_code_supervisor.py`
- `tests/unit/supervisor/test_supervisor_manager.py`
- `tests/unit/supervisor/test_io_handler.py`

**Test Coverage Requirements** (excellence_ai_standard 100%):
- ✅ Happy path tests
- ✅ Edge case tests
- ✅ Error scenario tests
- ✅ Security tests
- ✅ Performance tests
- ✅ Mock external dependencies (pexpect, subprocess)
- ✅ Parametrized tests for multiple scenarios

**Example Test Structure**:
```python
import pytest
from orchestrator.core.supervisor import ClaudeCodeSupervisor

class TestClaudeCodeSupervisor:
    """Test suite for ClaudeCodeSupervisor"""

    @pytest.fixture
    def supervisor(self):
        """Create a supervisor instance for testing"""
        return ClaudeCodeSupervisor(workspace_root="./test_workspace")

    # Happy path
    def test_spawn_claude_code_success(self, supervisor, mocker):
        """Should spawn Claude Code process successfully"""
        # Arrange
        mock_spawn = mocker.patch('wexpect.spawn')

        # Act
        result = supervisor.spawn_claude_code(task_file="test_task.txt")

        # Assert
        assert result.success is True
        assert result.process_id is not None
        mock_spawn.assert_called_once()

    # Edge cases
    def test_spawn_with_empty_task_file(self, supervisor):
        """Should reject empty task file"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            supervisor.spawn_claude_code(task_file="")

        assert "task_file cannot be empty" in str(exc_info.value)

    # Error scenarios
    def test_spawn_when_claude_not_found(self, supervisor, mocker):
        """Should handle missing Claude Code gracefully"""
        # Arrange
        mocker.patch('wexpect.spawn', side_effect=FileNotFoundError)

        # Act
        result = supervisor.spawn_claude_code(task_file="test.txt")

        # Assert
        assert result.success is False
        assert "Claude Code CLI not found" in result.error_message

    # Security tests
    def test_spawn_with_malicious_task_file_path(self, supervisor):
        """Should reject path traversal attempts"""
        # Act & Assert
        with pytest.raises(SecurityError):
            supervisor.spawn_claude_code(task_file="../../../etc/passwd")

    # Performance tests
    def test_supervisor_performance_under_load(self, supervisor):
        """Should handle high-frequency output efficiently"""
        # Test that supervision doesn't consume excessive CPU/memory
        pass
```

---

## 📋 Detailed Task Breakdown

### Task 1.1: ClaudeCodeSupervisor Implementation (10 hours)

**Sub-tasks**:
1. **Process Spawning** (3h)
   - Implement `spawn_claude_code()` method
   - Platform detection (Windows vs Linux/WSL)
   - Use wexpect (Windows) or pexpect (Linux)
   - Command: `claude --print < task_file.txt`
   - Error handling: FileNotFoundError, PermissionError
   - Input validation: task file path

2. **Output Monitoring** (4h)
   - Implement `monitor_output()` async method
   - Real-time stdout/stderr reading
   - Non-blocking I/O with asyncio
   - Output buffering with size limits
   - ANSI code stripping integration

3. **Confirmation Detection** (2h)
   - Implement `detect_confirmation_prompt()` method
   - 11 confirmation patterns (reuse existing regex)
   - Pattern matching with compiled regex
   - Confidence scoring
   - False positive prevention

4. **Lifecycle Management** (1h)
   - Implement `terminate()` method
   - Graceful shutdown (SIGTERM)
   - Forceful shutdown (SIGKILL) after timeout
   - Resource cleanup
   - Process state tracking

**Acceptance Criteria**:
- ✅ All methods have ≤50 lines
- ✅ All methods have comprehensive docstrings
- ✅ All edge cases handled
- ✅ Manual testing: Can spawn real Claude Code
- ✅ Manual testing: Can detect confirmation prompts

### Task 1.2: SupervisorManager Implementation (10 hours)

**Sub-tasks**:
1. **Class Structure** (2h)
   - Inherit from BaseAIManager
   - Override abstract methods
   - Implement ISupervisor interface
   - Dependency injection setup

2. **Confirmation Handling** (4h)
   - Implement `handle_confirmation()` method
   - Strategy pattern: SafeApprovalStrategy, EscalationStrategy
   - Integration with AI Safety Judge
   - Decision logging
   - Audit trail

3. **Error Detection & Retry** (3h)
   - Implement `detect_error()` method
   - Implement `retry_with_backoff()` method
   - Exponential backoff calculation
   - Max retries configuration
   - Error categorization (retryable vs fatal)

4. **Health Monitoring** (1h)
   - Implement `check_health()` method
   - Process health checks
   - Resource usage monitoring
   - Heartbeat mechanism

**Acceptance Criteria**:
- ✅ Proper inheritance hierarchy
- ✅ SOLID principles applied
- ✅ Strategy pattern implemented correctly
- ✅ All methods tested

### Task 1.3: Process I/O Handling Implementation (8 hours)

**Sub-tasks**:
1. **Non-blocking Read** (3h)
   - Implement `read_async()` generator
   - Asyncio integration
   - Buffer management
   - Backpressure handling

2. **Output Parsing** (2h)
   - Implement `parse_output()` method
   - Line buffering
   - UTF-8 decoding with error handling
   - Partial line handling

3. **ANSI Stripping Integration** (1h)
   - Integrate existing `ansi_utils.py`
   - Performance optimization
   - Caching stripped output

4. **Resource Cleanup** (2h)
   - Implement context managers
   - Proper file descriptor cleanup
   - Memory leak prevention
   - Exception safety

**Acceptance Criteria**:
- ✅ No blocking I/O operations
- ✅ Memory usage stays bounded
- ✅ Proper resource cleanup verified
- ✅ Performance benchmarks met (<1ms per line)

### Task 1.4: Unit Tests Implementation (12 hours)

**Sub-tasks**:
1. **ClaudeCodeSupervisor Tests** (5h)
   - Happy path: 5 tests
   - Edge cases: 5 tests
   - Error scenarios: 5 tests
   - Security tests: 3 tests
   - Performance tests: 2 tests
   - Coverage: ≥90%

2. **SupervisorManager Tests** (5h)
   - Happy path: 5 tests
   - Edge cases: 5 tests
   - Error scenarios: 5 tests
   - Integration tests: 3 tests
   - Mock AI Safety Judge
   - Coverage: ≥90%

3. **IOHandler Tests** (2h)
   - Async tests: 5 tests
   - Resource cleanup tests: 3 tests
   - Performance tests: 2 tests
   - Coverage: ≥90%

**Acceptance Criteria**:
- ✅ All tests pass
- ✅ Coverage ≥90% (no exceptions)
- ✅ No flaky tests
- ✅ Tests run in <30 seconds total

---

## 🔒 Security Requirements (CRITICAL - excellence_ai_standard)

### Input Validation
```python
from pydantic import BaseModel, validator, Field

class SpawnClaudeCodeInput(BaseModel):
    """Input validation for spawning Claude Code"""

    task_file: str = Field(..., min_length=1, max_length=255)
    workspace_root: str = Field(..., min_length=1, max_length=255)
    timeout: int = Field(default=300, ge=10, le=3600)

    @validator('task_file')
    def validate_task_file_path(cls, v):
        """Prevent path traversal attacks"""
        if '..' in v or v.startswith('/'):
            raise ValueError("Invalid task file path")
        return v

    @validator('workspace_root')
    def validate_workspace_root(cls, v):
        """Ensure workspace is within allowed directories"""
        from pathlib import Path
        workspace = Path(v).resolve()
        # Add additional checks here
        return str(workspace)

# Usage
input_data = SpawnClaudeCodeInput(
    task_file="task_001.txt",
    workspace_root="./workspace",
    timeout=600
)
```

### Process Security
- ✅ No shell injection vulnerabilities
- ✅ Process isolation
- ✅ Resource limits (CPU, memory)
- ✅ Proper signal handling
- ✅ No sensitive data in logs

### Error Messages
- ✅ NO sensitive information in error messages
- ✅ NO stack traces in production logs
- ✅ Sanitized error details for users

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
- **Unit Tests**: ≥90% line coverage, ≥85% branch coverage
- **Integration Tests**: Critical paths only
- **E2E Tests**: Smoke tests for core functionality

### Test Execution
```bash
# Run all tests
pytest tests/unit/supervisor/ -v --cov=orchestrator.core.supervisor --cov-report=html

# Expected output:
# ===================== test session starts ======================
# collected 45 items
#
# tests/unit/supervisor/test_claude_code_supervisor.py ........ [ 35%]
# tests/unit/supervisor/test_supervisor_manager.py ........ [ 70%]
# tests/unit/supervisor/test_io_handler.py ........ [100%]
#
# ===================== 45 passed in 28.5s ======================
# Coverage: 92%
```

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
- [ ] ✅ Test coverage ≥90%
- [ ] ✅ All tests pass
- [ ] ✅ No flaky tests
- [ ] ✅ Tests run in <30s

### Documentation
- [ ] ✅ All public APIs have docstrings
- [ ] ✅ Usage examples included
- [ ] ✅ Architecture diagram created
- [ ] ✅ README updated

### Security
- [ ] ✅ No SQL injection vulnerabilities (N/A for this worker)
- [ ] ✅ No path traversal vulnerabilities
- [ ] ✅ No shell injection vulnerabilities
- [ ] ✅ Input validation comprehensive
- [ ] ✅ Error messages sanitized

### Performance
- [ ] ✅ Process spawn time <500ms
- [ ] ✅ Output parsing <1ms per line
- [ ] ✅ Memory usage <100MB per monitor
- [ ] ✅ No memory leaks detected

---

## 🔗 Dependencies

### Already Implemented (✅ Week 0)
- `orchestrator/core/base_ai_manager.py` - BaseAIManager class
- `orchestrator/utils/ansi_utils.py` - ANSI code stripping
- `orchestrator/core/ai_safety_judge.py` - AI Safety Judge

### External Dependencies
```python
# requirements.txt additions (if any)
pexpect>=4.8.0  # Already exists
wexpect>=4.0.0  # Already exists
pydantic>=2.0.0  # Already exists
asyncio  # Standard library
```

### Platform Requirements
- Python 3.9+
- Claude Code CLI installed
- Windows: wexpect
- Linux/WSL: pexpect

---

## 📁 File Structure (After Completion)

```
orchestrator/
├── core/
│   ├── supervisor/
│   │   ├── __init__.py
│   │   ├── claude_code_supervisor.py     # NEW (300+ lines)
│   │   ├── supervisor_manager.py         # NEW (400+ lines)
│   │   └── io_handler.py                 # NEW (200+ lines)
│   ├── base_ai_manager.py                # ✅ Existing
│   └── ai_safety_judge.py                # ✅ Existing
├── utils/
│   └── ansi_utils.py                     # ✅ Existing
tests/
├── unit/
│   └── supervisor/
│       ├── test_claude_code_supervisor.py # NEW (400+ lines)
│       ├── test_supervisor_manager.py    # NEW (400+ lines)
│       └── test_io_handler.py            # NEW (200+ lines)
```

**Total New Code**: ~2,100 lines (including tests)

---

## 🎯 Success Metrics

### Functional Metrics
- ✅ Can spawn Claude Code instance: YES/NO
- ✅ Can monitor output in real-time: YES/NO
- ✅ Can detect confirmation prompts: Accuracy ≥95%
- ✅ False positive rate: <5%
- ✅ False negative rate: <2%

### Quality Metrics
- ✅ Test coverage: ≥90% (ACTUAL: __%)
- ✅ All tests pass: YES/NO
- ✅ TypeScript/Python strict mode: 0 errors
- ✅ Linter errors: 0
- ✅ Code review: PASSED/FAILED

### Performance Metrics
- ✅ Process spawn time: <500ms (ACTUAL: __ms)
- ✅ Output parsing: <1ms per line (ACTUAL: __ms)
- ✅ Memory usage: <100MB (ACTUAL: __MB)
- ✅ No memory leaks: YES/NO

---

## 🚨 Risk Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Claude Code API changes | Low | High | Version pinning, compatibility layer |
| wexpect/pexpect compatibility issues | Medium | Medium | Platform detection, fallback mechanisms |
| Memory leaks in I/O handling | Medium | High | Comprehensive resource cleanup, monitoring |
| Race conditions in async code | Medium | High | Proper locks, atomic operations, testing |

### Process Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Integration delays with Worker 2 | Low | Medium | Clear interface contracts, mocking |
| Testing takes longer than expected | Medium | Low | Parallel test execution, incremental testing |
| Scope creep | Low | Medium | Strict adherence to task definition |

---

## 📝 Handoff to Worker 2

### Interface Contract
```python
from typing import Protocol
from orchestrator.core.base_ai_manager import BaseAIManager

class ISupervisor(Protocol):
    """Interface that Worker 2 will consume"""

    async def spawn_claude_code(self, task_file: str) -> ProcessResult:
        """Spawn a new Claude Code instance"""
        ...

    async def monitor_output(self) -> AsyncGenerator[str, None]:
        """Stream Claude Code output"""
        ...

    async def detect_confirmation_prompt(self, output: str) -> ConfirmationPrompt | None:
        """Detect if output contains a confirmation prompt"""
        ...

    async def terminate(self) -> bool:
        """Terminate the Claude Code process"""
        ...
```

### Integration Points
- Worker 2 will connect `SupervisorManager` to `AISafetyJudge`
- Worker 2 will implement auto-approval logic
- Worker 2 will create WebSocket endpoints for real-time monitoring

---

## ✅ Definition of Done

This task is considered **DONE** when:

1. **Code Complete**
   - [ ] All 3 main files implemented
   - [ ] All code follows excellence_ai_standard 100%
   - [ ] Code review passed
   - [ ] All quality gates passed

2. **Tests Complete**
   - [ ] All unit tests written
   - [ ] Test coverage ≥90%
   - [ ] All tests passing
   - [ ] No flaky tests

3. **Documentation Complete**
   - [ ] All docstrings written
   - [ ] Usage examples included
   - [ ] Architecture diagram created
   - [ ] Integration guide for Worker 2

4. **Integration Ready**
   - [ ] Interface contract defined
   - [ ] Manual testing successful
   - [ ] No breaking changes to existing code
   - [ ] Git commit created with proper message

5. **Performance Validated**
   - [ ] All performance metrics met
   - [ ] No memory leaks
   - [ ] Resource cleanup verified

---

**Task Owner**: Worker AI 1
**Reviewer**: Orchestrator AI
**Created**: 2025-10-25
**Excellence AI Standard**: 100% Applied
**Estimated Completion**: Week 1, Day 3