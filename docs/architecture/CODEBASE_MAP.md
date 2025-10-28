# Codebase Navigation Map

**Version:** v10.1.0
**Purpose:** Help AI assistants quickly find and understand code
**Last Updated:** 2025-10-21

---

## 🗺️ Quick Navigation

**Jump to:**
- [Directory Structure](#directory-structure)
- [Core Modules](#core-modules-orchestratorcore)
- [API Layer](#api-layer-orchestratorapi)
- [Configuration & Setup](#configuration--setup)
- [Tests](#tests-tests)
- [Finding Specific Features](#finding-specific-features)

---

## 📁 Directory Structure

```
parallel_ai_test_project/
│
├── orchestrator/                    # Main application code
│   ├── core/                       # ⭐ Domain layer (v9+)
│   │   ├── exceptions.py           # Custom exception types
│   │   ├── observability.py        # Metrics, monitoring, health
│   │   ├── resilience.py           # Circuit breaker, retry, bulkhead
│   │   ├── structured_logging.py   # JSON logging system
│   │   ├── validated_config.py     # Configuration validation
│   │   ├── ai_safety_judge.py      # Safety controls
│   │   ├── enhanced_interactive_worker_manager.py  # Interactive workers
│   │   ├── worker_manager.py       # Worker process management
│   │   ├── task_analyzer_service.py  # Task analysis service
│   │   └── ...
│   │
│   ├── api/                        # ⭐ REST API layer
│   │   ├── app.py                  # FastAPI application
│   │   ├── models.py               # Pydantic request/response models
│   │   ├── auth.py                 # API key authentication
│   │   └── jobs.py                 # Job management endpoints
│   │
│   ├── window_strategies/          # Window management (WSL/Windows)
│   │   ├── base.py                 # Abstract base
│   │   ├── windows_strategy.py     # Windows implementation
│   │   └── wsl_strategy.py         # WSL implementation
│   │
│   ├── config.py                   # ⭐ Configuration management
│   ├── interfaces.py               # ⭐ Abstract interfaces (Protocol/ABC)
│   ├── task_splitter.py            # Task splitting logic
│   ├── ai_task_analyzer.py         # AI-driven task analysis
│   ├── ai_task_decomposer.py       # AI-driven task decomposition
│   ├── validators.py               # Input validation
│   ├── utils.py                    # Utility functions
│   └── ...
│
├── web_ui/                         # Web dashboard
│   ├── app.py                      # Dashboard server
│   ├── orchestrator_runner.py      # Bridge to orchestrator
│   ├── static/                     # Frontend assets
│   └── ...
│
├── tests/                          # ⭐ Comprehensive test suite
│   ├── test_api_integration.py     # API endpoint tests
│   ├── test_integration_v9.py      # V9 features integration tests
│   ├── test_enhanced_interactive_worker_manager.py  # Interactive mode tests
│   ├── test_exceptions.py          # Exception handling tests
│   ├── test_api_models.py          # Pydantic model tests
│   ├── test_orchestrator.py        # ⚠️ SKIPPED (v10 removed old code)
│   └── conftest.py                 # Pytest configuration
│
├── docs/                           # Documentation
│   ├── api_reference.md
│   ├── user_guide.md
│   └── VISIBLE_WORKERS.md
│
├── examples/                       # Usage examples
│   ├── basic_usage.py
│   ├── advanced_dashboard.py
│   └── interactive_mode_demo.py
│
├── scripts/                        # Utility scripts
│   ├── demo_*.py                   # Demo scripts
│   ├── test_*.py                   # Test utilities
│   └── mock_claude_cli.py          # Mock for testing
│
├── data/samples/                   # Sample data for testing
│
├── workspace/                      # Working directory
│   └── screenshots/                # Worker screenshots
│
├── AI_DEVELOPMENT_GUIDE.md         # ⭐ AI development guide
├── ARCHITECTURE.md                 # ⭐ Architecture documentation
├── CODEBASE_MAP.md                 # ⭐ This file
├── README.md                       # Project overview
├── CHANGELOG.md                    # Version history
├── mypy.ini                        # Type checking configuration
├── pytest.ini                      # Test configuration
└── requirements.txt                # Dependencies
```

---

## 🎯 Core Modules (`orchestrator/core/`)

### 📊 `exceptions.py` - Exception System
**Purpose:** Comprehensive custom exception types
**Lines:** ~525
**Key Components:**
```python
OrchestratorException (Base)
├── ConfigurationError
│   ├── InvalidWorkspaceError
│   └── MissingDependencyError
├── WorkerError (Worker-related)
│   ├── WorkerTimeoutError
│   ├── WorkerCrashError
│   └── WorkerSpawnError
├── TaskError (Task execution)
│   ├── TaskExecutionError
│   └── TaskValidationError
├── APIError (API-related)
│   ├── AuthenticationError
│   └── RateLimitError
└── SafetyError (Safety controls)
    ├── DangerousOperationError
    └── UserDeniedError
```

**When to use:** Always use these instead of generic exceptions
**Example:**
```python
from orchestrator.core.exceptions import TaskExecutionError

raise TaskExecutionError(
    "Task failed",
    task_name="data_processing",
    worker_id="worker_1",
    context={"retry_count": 3}
)
```

---

### 📈 `observability.py` - Metrics & Monitoring
**Purpose:** Metrics collection, performance monitoring, health checks
**Lines:** ~450
**Key Classes:**
```python
MetricsCollector
├── record(metric, value, labels)
├── get_summary()
└── export_prometheus()

PerformanceMonitor
├── track_operation(name, duration, success, labels)
├── get_operation_stats(name)
└── get_all_stats()

ResourceMonitor
├── get_system_metrics()
├── get_memory_usage()
└── get_cpu_usage()

HealthChecker
├── check_health()
├── register_check(name, func)
└── get_status()
```

**When to modify:** Adding new metrics, monitoring capabilities
**Example:**
```python
from orchestrator.core.observability import PerformanceMonitor, MetricsCollector

collector = MetricsCollector()
monitor = PerformanceMonitor(collector)

monitor.track_operation(
    "api_call",
    duration=0.125,
    success=True,
    labels={"endpoint": "/users"}
)
```

**Dependencies:** None (standalone)

---

### 🔄 `resilience.py` - Resilience Patterns
**Purpose:** Circuit breaker, retry, bulkhead patterns
**Lines:** ~400
**Key Classes:**
```python
CircuitBreaker
├── States: CLOSED → OPEN → HALF_OPEN
├── __call__(func)  # Execute with protection
└── get_state()

RetryStrategy
├── Exponential backoff
├── execute(func)
└── configure(max_attempts, base_delay)

BulkheadIsolation
├── Limit concurrent operations
├── acquire()
└── release()

ResilientOperation
└── Combine multiple patterns
```

**When to modify:** Adding new resilience patterns
**Example:**
```python
from orchestrator.core.resilience import CircuitBreaker, RetryStrategy

breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
retry = RetryStrategy(max_attempts=3, base_delay=1.0)

with breaker:
    result = retry.execute(lambda: risky_operation())
```

**Dependencies:** `exceptions.py`, `structured_logging.py`

---

### 📝 `structured_logging.py` - Logging System
**Purpose:** JSON-based structured logging
**Lines:** ~350
**Key Components:**
```python
StructuredLogger
├── Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
├── Categories: SYSTEM, WORKER, TASK, API, SECURITY
├── info(message, **context)
├── error(message, **context)
├── track_operation(name)  # Context manager
└── set_context(key, value)

LogLevel (Enum)
LogCategory (Enum)
JSONFormatter
```

**When to modify:** Adding new log categories, custom formatting
**Example:**
```python
from orchestrator.core.structured_logging import StructuredLogger, LogLevel, LogCategory

logger = StructuredLogger(
    name="my_service",
    category=LogCategory.SYSTEM,
    level=LogLevel.INFO
)

logger.info("Processing task", task_id="task_1", duration=1.25)

with logger.track_operation("database_query") as op:
    result = db.query()
    op.labels = {"query_type": "select"}
```

**Dependencies:** Python `logging` module

---

### ✅ `validated_config.py` - Configuration Validation
**Purpose:** Pydantic-based configuration validation
**Lines:** ~300
**Key Classes:**
```python
ValidatedConfig (Pydantic BaseModel)
├── max_workers: int (1-100)
├── default_timeout: int (1-3600)
├── execution_mode: ExecutionMode
└── validate_*() methods

ConfigurationPreset (Enum)
├── DEVELOPMENT
├── PRODUCTION
└── HIGH_PERFORMANCE
```

**When to modify:** Adding new configuration options, validation rules
**Example:**
```python
from orchestrator.core.validated_config import ValidatedConfig

config = ValidatedConfig(
    max_workers=10,
    default_timeout=120,
    execution_mode="windows"
)

# Validation happens automatically
# Raises ValidationError if invalid
```

**Dependencies:** `pydantic`, `config.py`

---

### 🛡️ `ai_safety_judge.py` - Safety Controls
**Purpose:** Detect and control dangerous operations
**Lines:** ~250
**Key Classes:**
```python
AISafetyJudge
├── evaluate_operation(operation_type, details)
├── is_dangerous(operation)
└── request_approval(operation)

SafetyRule
DangerLevel (Enum)
```

**When to modify:** Adding new safety rules, danger detection
**Example:**
```python
from orchestrator.core.ai_safety_judge import AISafetyJudge

judge = AISafetyJudge()

# Evaluate operation
if judge.is_dangerous("FILE_DELETE", {"path": "/important/data.db"}):
    approval = judge.request_approval(...)
    if not approval:
        raise DangerousOperationError(...)
```

**Dependencies:** `exceptions.py`

---

### 👷 `enhanced_interactive_worker_manager.py` - Interactive Workers
**Purpose:** Manage interactive worker processes with confirmation handling
**Lines:** ~600
**Key Classes:**
```python
EnhancedInteractiveWorkerManager
├── Platform detection (Windows/Unix)
├── spawn_interactive_worker(task)
├── handle_confirmation_request(request)
├── detect_confirmation_pattern(output)
└── auto_respond(confirmation)

ConfirmationRequest
ConfirmationPattern
```

**When to modify:** Adding new confirmation patterns, worker behaviors
**Example:**
```python
from orchestrator.core.enhanced_interactive_worker_manager import (
    EnhancedInteractiveWorkerManager
)

manager = EnhancedInteractiveWorkerManager(config)
worker = manager.spawn_interactive_worker(task)

# Automatic confirmation handling
if manager.detect_confirmation_pattern(output):
    response = manager.handle_confirmation_request(...)
```

**Dependencies:** `pexpect`/`wexpect`, `config.py`, `ai_safety_judge.py`

---

### 🔧 `worker_manager.py` - Worker Process Management
**Purpose:** Base worker process management
**Lines:** ~400
**Key Classes:**
```python
WorkerManager
├── spawn_worker(task_id, task)
├── monitor_worker(worker_id)
├── collect_result(worker_id)
└── cleanup_worker(worker_id)

WorkerInfo
WorkerStatus (Enum)
```

**When to modify:** Core worker lifecycle management
**Dependencies:** `config.py`, `exceptions.py`

---

### 🎯 `task_analyzer_service.py` - Task Analysis Service
**Purpose:** Application service for task analysis and splitting
**Lines:** ~200
**Key Classes:**
```python
TaskAnalyzerService
├── analyze_and_split(request)
├── _advanced_split(request)
├── _basic_split(request)
└── execute_tasks(tasks)
```

**When to modify:** Task analysis logic, splitting strategies
**Dependencies:** `task_splitter.py`, `ai_task_analyzer.py`

---

## 🌐 API Layer (`orchestrator/api/`)

### 🚀 `app.py` - FastAPI Application
**Purpose:** Main API application with endpoints
**Lines:** ~350
**Key Components:**
```python
create_app() → FastAPI
    ├── CORS middleware
    ├── Exception handlers
    ├── Rate limiting
    └── Routes:
        ├── GET  /
        ├── GET  /health
        ├── POST /api/v1/orchestrate
        ├── GET  /api/v1/jobs/{job_id}
        ├── POST /api/v1/jobs/{job_id}/cancel
        └── GET  /api/v1/system/status
```

**When to modify:** Adding new endpoints, middleware
**Example of adding endpoint:**
```python
@app.post("/api/v1/new-feature", response_model=SuccessResponse)
async def new_feature(request: NewFeatureRequest):
    # Implementation
    return SuccessResponse(message="Success", data=result)
```

**Dependencies:** `fastapi`, `models.py`, `auth.py`

---

### 📋 `models.py` - Pydantic Models
**Purpose:** Request/response models for API
**Lines:** ~400
**Key Models:**
```python
# Requests
OrchestrateRequest
OrchestratorConfigModel
CancelJobRequest

# Responses
JobResponse
JobStatusResponse
SystemStatusResponse
ErrorResponse
SuccessResponse

# Internal
JobProgress
TaskResultModel
```

**When to modify:** Adding new API models
**IMPORTANT:** Use `.model_dump(mode='json')` for datetime serialization!

**Example:**
```python
from pydantic import BaseModel, Field

class NewFeatureRequest(BaseModel):
    param: str = Field(..., description="Parameter description")

    class Config:
        json_schema_extra = {
            "example": {"param": "value"}
        }
```

**Dependencies:** `pydantic`

---

### 🔐 `auth.py` - Authentication
**Purpose:** API key authentication
**Lines:** ~100
**Key Components:**
```python
verify_api_key(api_key: str = Header(...))
check_rate_limit(api_key: str)
```

**When to modify:** Authentication logic, rate limiting
**Dependencies:** `fastapi`, `exceptions.py`

---

### 📊 `jobs.py` - Job Management
**Purpose:** Job lifecycle management
**Lines:** ~200
**Key Components:**
```python
JobManager
├── create_job(request)
├── get_job_status(job_id)
├── cancel_job(job_id)
└── cleanup_old_jobs()

JobStatus (Enum)
```

**When to modify:** Job management logic
**Dependencies:** `models.py`

---

## ⚙️ Configuration & Setup

### `config.py` - Configuration Management
**Purpose:** Main configuration dataclass
**Lines:** ~250
**Key Classes:**
```python
OrchestratorConfig
├── execution_mode: "wsl" | "windows"
├── max_workers: int
├── default_timeout: int
├── workspace_root: str
├── git_bash_path: Optional[str]
└── Methods:
    ├── get_claude_command(input, output)
    ├── from_env() → classmethod
    └── __post_init__()

TaskConfig
find_git_bash() → Optional[str]
```

**When to modify:** Adding configuration options
**Example:**
```python
from orchestrator.config import OrchestratorConfig

config = OrchestratorConfig(
    execution_mode="windows",
    max_workers=10
)

# Or from environment
config = OrchestratorConfig.from_env()
```

---

### `interfaces.py` - Abstract Interfaces
**Purpose:** Protocol and ABC definitions for dependency inversion
**Lines:** ~110
**Key Interfaces:**
```python
IScreenshotCapture (Protocol)
IWindowManager (Protocol)
IConfigValidator (ABC)
IResourceManager (Protocol)
ILogger (Protocol)
```

**When to modify:** Adding new abstract interfaces
**Example:**
```python
from orchestrator.interfaces import ILogger

class MyService:
    def __init__(self, logger: ILogger):
        self.logger = logger  # Any logger implementing ILogger
```

---

## 🧪 Tests (`tests/`)

### Test File Organization

| File | Purpose | Tests |
|------|---------|-------|
| `test_api_integration.py` | API endpoint tests | 12 tests |
| `test_api_models.py` | Pydantic model tests | 13 tests |
| `test_enhanced_interactive_worker_manager.py` | Interactive mode | 20 tests |
| `test_exceptions.py` | Exception handling | 4 tests |
| `test_integration_v9.py` | V9 features integration | 37 tests |
| `test_orchestrator.py` | ⚠️ **SKIPPED** (v10 removed code) | 15 skipped |

### Running Tests

```bash
# All tests
python -m pytest tests/ -v --tb=short --no-cov

# Specific file
python -m pytest tests/test_api_integration.py -v

# Specific test
python -m pytest tests/test_exceptions.py::TestOrchestratorError::test_basic_error -v
```

---

## 🔍 Finding Specific Features

### "I need to work with exceptions"
→ `orchestrator/core/exceptions.py`
→ Tests: `tests/test_exceptions.py`

### "I need to add an API endpoint"
→ `orchestrator/api/app.py` (add endpoint)
→ `orchestrator/api/models.py` (add models)
→ Tests: `tests/test_api_integration.py`

### "I need to add metrics/monitoring"
→ `orchestrator/core/observability.py`
→ Tests: `tests/test_integration_v9.py::TestObservability`

### "I need to add resilience (circuit breaker, retry)"
→ `orchestrator/core/resilience.py`
→ Tests: `tests/test_integration_v9.py::TestResiliencePatterns`

### "I need to modify logging"
→ `orchestrator/core/structured_logging.py`
→ Tests: `tests/test_integration_v9.py::TestStructuredLogging`

### "I need to add configuration options"
→ `orchestrator/config.py` (base config)
→ `orchestrator/core/validated_config.py` (validated config)
→ Tests: `tests/test_integration_v9.py::TestValidatedConfiguration`

### "I need to modify worker management"
→ `orchestrator/core/worker_manager.py` (base)
→ `orchestrator/core/enhanced_interactive_worker_manager.py` (interactive)
→ Tests: `tests/test_enhanced_interactive_worker_manager.py`

### "I need to modify task analysis/splitting"
→ `orchestrator/task_splitter.py` (basic)
→ `orchestrator/ai_task_analyzer.py` (AI-driven analysis)
→ `orchestrator/ai_task_decomposer.py` (AI-driven decomposition)
→ `orchestrator/core/task_analyzer_service.py` (service layer)

### "I need to add safety controls"
→ `orchestrator/core/ai_safety_judge.py`

---

## 📊 Module Dependencies

### Dependency Graph

```
Presentation Layer (API)
    ↓ depends on
Application Layer (Services)
    ↓ depends on
Domain Layer (Core)
    ↓ depends on
Infrastructure Layer (Config, Workers)
```

### Core Module Dependencies

```
exceptions.py
    ↓
structured_logging.py
    ↓
observability.py
    ↓
resilience.py

config.py
    ↓
validated_config.py

interfaces.py (no dependencies)
```

---

## 🎯 Common Code Patterns

### Pattern 1: Exception Handling
```python
from orchestrator.core.exceptions import TaskExecutionError

try:
    result = execute_task(task)
except Exception as e:
    raise TaskExecutionError(
        "Task failed",
        task_name=task.name,
        context={"error": str(e)}
    ) from e
```

### Pattern 2: Logging
```python
from orchestrator.core.structured_logging import StructuredLogger, LogLevel

logger = StructuredLogger("my_module", level=LogLevel.INFO)
logger.info("Operation completed", operation="task_exec", duration=1.25)
```

### Pattern 3: Metrics
```python
from orchestrator.core.observability import MetricsCollector, PerformanceMonitor

collector = MetricsCollector()
monitor = PerformanceMonitor(collector)

monitor.track_operation("api_call", duration=0.15, success=True, labels={"endpoint": "/api/v1/orchestrate"})
```

### Pattern 4: Configuration
```python
from orchestrator.config import OrchestratorConfig

config = OrchestratorConfig.from_env()
command = config.get_claude_command(input_file, output_file)
```

### Pattern 5: API Models
```python
from pydantic import BaseModel, Field

class MyRequest(BaseModel):
    param: str = Field(..., min_length=1)

# Return response (IMPORTANT: use mode='json' for datetime!)
return response.model_dump(mode='json')
```

---

## 📝 File Naming Conventions

- `*_service.py` - Application services
- `*_manager.py` - Infrastructure managers
- `*_strategy.py` - Strategy pattern implementations
- `test_*.py` - Test files
- `*_config.py` - Configuration files
- `*.py` (no prefix) - Domain entities, utilities

---

## 🚀 Quick Start Checklist

**For AI assistants working on this codebase:**

- [ ] Read `AI_DEVELOPMENT_GUIDE.md` first
- [ ] Understand architecture from `ARCHITECTURE.md`
- [ ] Use this file to navigate code
- [ ] Always run tests after changes
- [ ] Check `mypy` for type errors
- [ ] Follow existing patterns
- [ ] Update documentation if needed

---

## 📚 Related Documentation

- **AI_DEVELOPMENT_GUIDE.md** - Development guide for AI assistants
- **ARCHITECTURE.md** - System architecture details
- **AI_PROMPTS.md** - Effective prompts for this codebase
- **README.md** - Project overview
- **CHANGELOG.md** - Version history

---

**Last Updated:** 2025-10-21
**Version:** v10.1.0
**Maintenance:** Update when adding/moving files
