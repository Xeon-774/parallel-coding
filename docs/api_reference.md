# API Reference - Parallel AI Test Project

Complete API documentation for all classes and methods.

## Table of Contents

- [orchestrator.Orchestrator](#orchestratororchestrator)
- [orchestrator.ai_task_decomposer.AITaskDecomposer](#orchestratorai_task_decomposeraitaskdecomposer)
- [orchestrator.worker.Worker](#orchestratorworkerworker)
- [orchestrator.monitoring.Monitor](#orchestratormonitoringmonitor)
- [orchestrator.config.Config](#orchestratorconfigconfig)
- [orchestrator.logger.Logger](#orchestratorloggerlogger)
- [orchestrator.exceptions](#orchestratorexceptions)

---

## orchestrator.Orchestrator

Main orchestrator class for managing parallel task execution.

### Class Definition

```python
class Orchestrator:
    def __init__(
        self,
        max_workers: int = 10,
        mode: str = "subprocess",
        timeout: int = 120,
        workspace_dir: str = "./workspace",
        config: Optional[Config] = None
    )
```

### Parameters

- **max_workers** (`int`, default=10): Maximum number of parallel workers
- **mode** (`str`, default="subprocess"): Execution mode (`subprocess`, `worktree`, `docker`)
- **timeout** (`int`, default=120): Task timeout in seconds
- **workspace_dir** (`str`, default="./workspace"): Working directory path
- **config** (`Optional[Config]`, default=None): Custom configuration object

### Methods

#### execute()

Execute a task with automatic decomposition and parallel processing.

```python
def execute(
    self,
    task: str,
    monitor: bool = False,
    retry_on_failure: bool = True
) -> Dict[str, Any]
```

**Parameters:**
- **task** (`str`): Task description or request
- **monitor** (`bool`, default=False): Enable real-time monitoring
- **retry_on_failure** (`bool`, default=True): Retry failed subtasks

**Returns:**
- `Dict[str, Any]`: Execution results containing:
  - `status` (str): Overall status ("success", "partial", "failed")
  - `total_tasks` (int): Total number of subtasks
  - `completed_tasks` (int): Number of completed subtasks
  - `failed_tasks` (int): Number of failed subtasks
  - `subtask_results` (List[Dict]): Individual subtask results
  - `aggregated_output` (str): Combined output
  - `duration` (float): Total execution time in seconds

**Example:**
```python
orch = Orchestrator(max_workers=3)
result = orch.execute("Create a todo application")

if result['status'] == 'success':
    print(f"Completed in {result['duration']:.2f}s")
```

#### execute_subtasks()

Execute a list of predefined subtasks.

```python
def execute_subtasks(
    self,
    subtasks: List[str],
    monitor: bool = False
) -> Dict[str, Any]
```

**Parameters:**
- **subtasks** (`List[str]`): List of subtask descriptions
- **monitor** (`bool`, default=False): Enable monitoring

**Returns:**
- `Dict[str, Any]`: Same structure as `execute()`

**Example:**
```python
subtasks = [
    "Create user authentication module",
    "Create database schema",
    "Create REST API endpoints"
]
result = orch.execute_subtasks(subtasks)
```

#### get_status()

Get current orchestrator status.

```python
def get_status() -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: Status information
  - `active_workers` (int): Number of running workers
  - `queued_tasks` (int): Tasks waiting for execution
  - `completed_tasks` (int): Finished tasks
  - `failed_tasks` (int): Failed tasks

#### cleanup()

Clean up resources and temporary files.

```python
def cleanup(force: bool = False) -> None
```

**Parameters:**
- **force** (`bool`, default=False): Force cleanup even if tasks are running

---

## orchestrator.ai_task_decomposer.AITaskDecomposer

AI-powered task decomposition engine.

### Class Definition

```python
class AITaskDecomposer:
    def __init__(
        self,
        model: str = "claude-sonnet-4-5",
        temperature: float = 0.7,
        max_tokens: int = 4000
    )
```

### Parameters

- **model** (`str`, default="claude-sonnet-4-5"): AI model identifier
- **temperature** (`float`, default=0.7): Sampling temperature (0.0-1.0)
- **max_tokens** (`int`, default=4000): Maximum tokens in response

### Methods

#### decompose()

Decompose a complex task into subtasks.

```python
def decompose(
    self,
    task: str,
    max_subtasks: int = 10
) -> List[Dict[str, Any]]
```

**Parameters:**
- **task** (`str`): Task description to decompose
- **max_subtasks** (`int`, default=10): Maximum number of subtasks

**Returns:**
- `List[Dict[str, Any]]`: List of subtask definitions
  - `id` (int): Subtask identifier
  - `description` (str): Subtask description
  - `dependencies` (List[int]): IDs of dependent subtasks
  - `estimated_duration` (int): Estimated time in seconds
  - `priority` (int): Priority level (1-5)

**Example:**
```python
decomposer = AITaskDecomposer(temperature=0.5)
subtasks = decomposer.decompose(
    "Create a full-stack web application with authentication"
)

for subtask in subtasks:
    print(f"{subtask['id']}: {subtask['description']}")
```

#### analyze_complexity()

Analyze task complexity.

```python
def analyze_complexity(task: str) -> Dict[str, Any]
```

**Parameters:**
- **task** (`str`): Task to analyze

**Returns:**
- `Dict[str, Any]`: Complexity analysis
  - `complexity_score` (float): 0.0-1.0 complexity rating
  - `estimated_subtasks` (int): Estimated number of subtasks
  - `recommended_workers` (int): Recommended worker count
  - `estimated_duration` (int): Estimated total duration (seconds)

---

## orchestrator.worker.Worker

Worker class for executing individual subtasks.

### Class Definition

```python
class Worker:
    def __init__(
        self,
        worker_id: int,
        workspace_dir: str,
        mode: str = "subprocess",
        timeout: int = 120
    )
```

### Parameters

- **worker_id** (`int`): Unique worker identifier
- **workspace_dir** (`str`): Worker workspace directory
- **mode** (`str`, default="subprocess"): Execution mode
- **timeout** (`int`, default=120): Execution timeout

### Methods

#### execute()

Execute a subtask.

```python
def execute(task: str) -> Dict[str, Any]
```

**Parameters:**
- **task** (`str`): Task description

**Returns:**
- `Dict[str, Any]`: Execution result
  - `status` (str): "success" or "failed"
  - `output` (str): Task output
  - `error` (Optional[str]): Error message if failed
  - `duration` (float): Execution time
  - `worker_id` (int): Worker identifier

#### get_status()

Get worker status.

```python
def get_status() -> str
```

**Returns:**
- `str`: Worker status ("idle", "running", "completed", "failed")

#### cleanup()

Clean up worker resources.

```python
def cleanup() -> None
```

---

## orchestrator.monitoring.Monitor

Real-time monitoring for task execution.

### Class Definition

```python
class Monitor:
    def __init__(
        self,
        orchestrator: Optional[Orchestrator] = None,
        update_interval: int = 5
    )
```

### Parameters

- **orchestrator** (`Optional[Orchestrator]`, default=None): Orchestrator to monitor
- **update_interval** (`int`, default=5): Update interval in seconds

### Methods

#### start()

Start monitoring.

```python
def start() -> None
```

#### stop()

Stop monitoring.

```python
def stop() -> None
```

#### get_metrics()

Get current metrics.

```python
def get_metrics() -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: Current metrics
  - `active_workers` (int): Active worker count
  - `cpu_percent` (float): CPU usage percentage
  - `memory_mb` (float): Memory usage in MB
  - `completed_tasks` (int): Completed task count
  - `elapsed_time` (float): Elapsed time in seconds

**Example:**
```python
monitor = Monitor(orchestrator=orch, update_interval=5)
monitor.start()

# Run tasks...

metrics = monitor.get_metrics()
print(f"CPU: {metrics['cpu_percent']}%")
print(f"Memory: {metrics['memory_mb']} MB")

monitor.stop()
```

---

## orchestrator.config.Config

Configuration management.

### Class Definition

```python
class Config:
    def __init__(
        self,
        max_workers: int = 10,
        mode: str = "subprocess",
        timeout: int = 120,
        workspace_dir: str = "./workspace",
        log_level: str = "INFO",
        **kwargs
    )
```

### Parameters

- **max_workers** (`int`, default=10): Maximum workers
- **mode** (`str`, default="subprocess"): Execution mode
- **timeout** (`int`, default=120): Timeout in seconds
- **workspace_dir** (`str`, default="./workspace"): Workspace path
- **log_level** (`str`, default="INFO"): Logging level
- **kwargs**: Additional configuration options

### Class Methods

#### from_yaml()

Load configuration from YAML file.

```python
@classmethod
def from_yaml(cls, file_path: str) -> Config
```

**Parameters:**
- **file_path** (`str`): Path to YAML configuration file

**Returns:**
- `Config`: Configuration instance

**Example:**
```python
config = Config.from_yaml('config.yaml')
orch = Orchestrator(config=config)
```

#### from_env()

Load configuration from environment variables.

```python
@classmethod
def from_env(cls) -> Config
```

**Returns:**
- `Config`: Configuration instance

**Example:**
```python
# Set environment variables
# ORCHESTRATOR_MAX_WORKERS=5
# ORCHESTRATOR_MODE=worktree

config = Config.from_env()
```

### Methods

#### to_dict()

Convert configuration to dictionary.

```python
def to_dict() -> Dict[str, Any]
```

#### update()

Update configuration values.

```python
def update(**kwargs) -> None
```

**Example:**
```python
config = Config()
config.update(max_workers=8, timeout=300)
```

#### validate()

Validate configuration values.

```python
def validate() -> bool
```

**Returns:**
- `bool`: True if valid

**Raises:**
- `ValueError`: If configuration is invalid

---

## orchestrator.logger.Logger

Structured logging system.

### Class Definition

```python
class Logger:
    def __init__(
        self,
        name: str,
        log_dir: str = "./workspace/logs",
        level: str = "INFO",
        structured: bool = True
    )
```

### Parameters

- **name** (`str`): Logger name
- **log_dir** (`str`, default="./workspace/logs"): Log directory
- **level** (`str`, default="INFO"): Log level
- **structured** (`bool`, default=True): Use structured JSON logging

### Methods

#### info()

Log info message.

```python
def info(message: str, **kwargs) -> None
```

#### debug()

Log debug message.

```python
def debug(message: str, **kwargs) -> None
```

#### warning()

Log warning message.

```python
def warning(message: str, **kwargs) -> None
```

#### error()

Log error message.

```python
def error(message: str, **kwargs) -> None
```

**Example:**
```python
logger = Logger("orchestrator", level="DEBUG")
logger.info("Task started", task_id=1, worker_id=3)
logger.error("Task failed", task_id=1, error="Timeout")
```

---

## orchestrator.exceptions

Custom exception classes.

### TaskDecompositionError

Raised when task decomposition fails.

```python
class TaskDecompositionError(Exception):
    def __init__(self, message: str, task: str)
```

**Attributes:**
- `message` (str): Error message
- `task` (str): Original task description

**Example:**
```python
try:
    subtasks = decomposer.decompose(task)
except TaskDecompositionError as e:
    print(f"Failed to decompose: {e.task}")
```

### WorkerExecutionError

Raised when worker execution fails.

```python
class WorkerExecutionError(Exception):
    def __init__(
        self,
        message: str,
        worker_id: int,
        task: str,
        error_details: Optional[str] = None
    )
```

**Attributes:**
- `message` (str): Error message
- `worker_id` (int): Worker identifier
- `task` (str): Failed task
- `error_details` (Optional[str]): Detailed error information

### TimeoutError

Raised when task execution times out.

```python
class TimeoutError(Exception):
    def __init__(
        self,
        message: str,
        task: str,
        timeout: int
    )
```

**Attributes:**
- `message` (str): Error message
- `task` (str): Timed out task
- `timeout` (int): Timeout duration in seconds

### ConfigurationError

Raised when configuration is invalid.

```python
class ConfigurationError(Exception):
    def __init__(self, message: str, config_key: str)
```

**Attributes:**
- `message` (str): Error message
- `config_key` (str): Invalid configuration key

---

## Type Definitions

### TaskResult

```python
from typing import TypedDict, Optional, List

class TaskResult(TypedDict):
    status: str  # "success", "failed"
    output: str
    error: Optional[str]
    duration: float
    worker_id: int
    task: str
```

### ExecutionResult

```python
class ExecutionResult(TypedDict):
    status: str  # "success", "partial", "failed"
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    subtask_results: List[TaskResult]
    aggregated_output: str
    duration: float
```

### SubtaskDefinition

```python
class SubtaskDefinition(TypedDict):
    id: int
    description: str
    dependencies: List[int]
    estimated_duration: int
    priority: int
```

---

## Usage Examples

### Complete Workflow

```python
from orchestrator import Orchestrator
from orchestrator.config import Config
from orchestrator.monitoring import Monitor
from orchestrator.logger import Logger

# Setup logging
logger = Logger("my_app", level="INFO")

# Load configuration
config = Config.from_yaml('config.yaml')
config.update(max_workers=5)

# Create orchestrator
orch = Orchestrator(config=config)

# Setup monitoring
monitor = Monitor(orch, update_interval=5)
monitor.start()

# Execute task
try:
    result = orch.execute(
        "Create a data visualization dashboard",
        monitor=True
    )

    if result['status'] == 'success':
        logger.info("Task completed successfully",
                   duration=result['duration'])
    else:
        logger.warning("Task partially completed",
                      failed=result['failed_tasks'])

except Exception as e:
    logger.error("Task execution failed", error=str(e))

finally:
    monitor.stop()
    orch.cleanup()
```

### Advanced Task Decomposition

```python
from orchestrator.ai_task_decomposer import AITaskDecomposer

decomposer = AITaskDecomposer(
    model="claude-sonnet-4-5",
    temperature=0.5
)

# Analyze complexity
complexity = decomposer.analyze_complexity(
    "Build a full-stack e-commerce platform"
)

print(f"Complexity: {complexity['complexity_score']}")
print(f"Recommended workers: {complexity['recommended_workers']}")

# Decompose with constraints
subtasks = decomposer.decompose(
    "Build a full-stack e-commerce platform",
    max_subtasks=complexity['recommended_workers']
)

# Execute with dependencies
orch = Orchestrator(max_workers=complexity['recommended_workers'])
result = orch.execute_subtasks([s['description'] for s in subtasks])
```

---

## Version Information

- **API Version**: 3.0.0
- **Last Updated**: 2025-10-20
- **Compatibility**: Python 3.8+

## See Also

- [User Guide](user_guide.md) - Detailed usage instructions
- [Examples](../examples/) - Code examples
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development guide
