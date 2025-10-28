# User Guide - Parallel AI Test Project

Complete guide for using the Parallel AI Test Project orchestration system.

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Command Line Interface](#command-line-interface)
- [Python API](#python-api)
- [Configuration](#configuration)
- [Execution Modes](#execution-modes)
- [Monitoring](#monitoring)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Introduction

The Parallel AI Test Project is an orchestration system that enables you to execute complex tasks in parallel using multiple AI workers. This guide covers all aspects of using the system effectively.

### Key Concepts

- **Orchestrator**: The main controller that manages task distribution and result aggregation
- **Worker**: Individual execution units that process subtasks
- **Task Decomposer**: AI-powered component that breaks down complex requests
- **Execution Modes**: Different isolation strategies (subprocess, worktree, docker)

## Getting Started

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/parallel_ai_test_project.git
cd parallel_ai_test_project

# Install dependencies
pip install -r requirements.txt
```

### First Run

```bash
# Simple task execution
python orchestrator/main.py "Create a simple calculator app"
```

Expected output:
```
[INFO] Task decomposed into 1 subtask(s)
[INFO] Starting worker 1/1
[INFO] Worker 1 completed successfully
[SUCCESS] All tasks completed
```

## Command Line Interface

### Basic Syntax

```bash
python orchestrator/main.py [OPTIONS] "TASK_DESCRIPTION"
```

### Options

#### `--max-workers N`
Set maximum number of parallel workers (default: 10)

```bash
python orchestrator/main.py --max-workers 5 "Create three web apps"
```

#### `--mode {subprocess|worktree|docker}`
Set execution mode (default: subprocess)

```bash
python orchestrator/main.py --mode worktree "Generate code for multiple services"
```

#### `--timeout SECONDS`
Set task timeout in seconds (default: 120)

```bash
python orchestrator/main.py --timeout 300 "Complex data analysis task"
```

#### `--config PATH`
Specify custom configuration file

```bash
python orchestrator/main.py --config my_config.yaml "Task description"
```

#### `--monitor`
Enable real-time monitoring

```bash
python orchestrator/main.py --monitor "Long running task"
```

#### `--log-level {DEBUG|INFO|WARNING|ERROR}`
Set logging verbosity

```bash
python orchestrator/main.py --log-level DEBUG "Task with detailed logging"
```

#### `--workspace PATH`
Custom workspace directory

```bash
python orchestrator/main.py --workspace /tmp/my_workspace "Task"
```

### Examples

#### Single Task
```bash
python orchestrator/main.py "Create a password generator in Python"
```

#### Multiple Tasks
```bash
python orchestrator/main.py "Create: 1) Todo app 2) Weather dashboard 3) File converter"
```

#### With Custom Settings
```bash
python orchestrator/main.py \
  --max-workers 3 \
  --mode worktree \
  --timeout 600 \
  --monitor \
  "Analyze sales data and create visualizations"
```

#### Interactive Mode
```bash
python orchestrator/main.py
# You will be prompted to enter your task
```

## Python API

### Basic Usage

```python
from orchestrator import Orchestrator

# Create orchestrator instance
orch = Orchestrator(
    max_workers=3,
    mode="subprocess",
    timeout=120
)

# Execute task
result = orch.execute("Create a todo application")

# Check results
if result['status'] == 'success':
    print(f"Completed {result['completed_tasks']} tasks")
    for subtask in result['subtask_results']:
        print(f"- {subtask['task']}: {subtask['status']}")
```

### Advanced Configuration

```python
from orchestrator import Orchestrator
from orchestrator.config import Config

# Custom configuration
config = Config(
    max_workers=5,
    mode="worktree",
    timeout=300,
    workspace_dir="./my_workspace",
    log_level="DEBUG"
)

# Create orchestrator with custom config
orch = Orchestrator(config=config)

# Execute with monitoring
result = orch.execute(
    task="Complex multi-step task",
    monitor=True,
    retry_on_failure=True
)
```

### Accessing Results

```python
result = orch.execute("Create three applications")

# Overall status
print(f"Status: {result['status']}")
print(f"Total tasks: {result['total_tasks']}")
print(f"Completed: {result['completed_tasks']}")
print(f"Failed: {result['failed_tasks']}")

# Individual subtask results
for i, subtask in enumerate(result['subtask_results'], 1):
    print(f"\nSubtask {i}:")
    print(f"  Task: {subtask['task']}")
    print(f"  Status: {subtask['status']}")
    print(f"  Worker ID: {subtask['worker_id']}")
    print(f"  Duration: {subtask['duration']}s")
    print(f"  Output: {subtask['output'][:200]}...")

    if subtask['status'] == 'failed':
        print(f"  Error: {subtask['error']}")

# Aggregated output
print("\n" + "="*50)
print(result.get('aggregated_output', ''))
```

### Error Handling

```python
from orchestrator import Orchestrator
from orchestrator.exceptions import (
    TaskDecompositionError,
    WorkerExecutionError,
    TimeoutError
)

orch = Orchestrator(max_workers=3)

try:
    result = orch.execute("Complex task")

except TaskDecompositionError as e:
    print(f"Failed to decompose task: {e}")

except WorkerExecutionError as e:
    print(f"Worker execution failed: {e}")
    print(f"Worker ID: {e.worker_id}")
    print(f"Task: {e.task}")

except TimeoutError as e:
    print(f"Task timed out after {e.timeout}s")

except Exception as e:
    print(f"Unexpected error: {e}")
```

## Configuration

### Configuration File (config.yaml)

```yaml
# Orchestrator settings
orchestrator:
  max_workers: 5
  mode: subprocess  # subprocess, worktree, or docker
  timeout: 120
  max_retries: 2
  retry_delay: 5

# AI settings
ai:
  model: claude-sonnet-4-5
  temperature: 0.7
  max_tokens: 4000

# Monitoring settings
monitoring:
  enabled: true
  interval: 5  # seconds
  log_level: INFO

# Paths
paths:
  workspace: ./workspace
  logs: ./workspace/logs
  output: ./workspace/output

# Resource limits
resources:
  max_memory_per_worker: 2048  # MB
  max_cpu_percent: 80
```

### Environment Variables

Set via shell or `.env` file:

```bash
# Execution mode
export ORCHESTRATOR_MODE=worktree

# Workspace directory
export ORCHESTRATOR_WORKSPACE=/tmp/workspace

# Timeout (seconds)
export ORCHESTRATOR_TIMEOUT=300

# Max workers
export ORCHESTRATOR_MAX_WORKERS=8

# Retry settings
export ORCHESTRATOR_MAX_RETRIES=3

# Logging
export ORCHESTRATOR_LOG_LEVEL=DEBUG

# WSL settings (if applicable)
export WSL_DISTRIBUTION=Ubuntu
export NVM_PATH=/home/user/.nvm/versions/node/v22.20.0/bin
```

### Loading Configuration in Python

```python
from orchestrator.config import Config

# Load from YAML file
config = Config.from_yaml('config.yaml')

# Load from environment variables
config = Config.from_env()

# Combine: YAML + env overrides
config = Config.from_yaml('config.yaml')
config.update_from_env()

# Manual configuration
config = Config(
    max_workers=5,
    mode='worktree',
    timeout=300
)
```

## Execution Modes

### Subprocess Mode (Default)

Fast and lightweight execution using Python subprocesses.

**Pros:**
- Fast startup
- Low overhead
- Shared file system

**Cons:**
- No file isolation
- Potential conflicts

**Usage:**
```python
orch = Orchestrator(mode="subprocess")
```

### Worktree Mode

Uses Git worktrees for isolated execution environments.

**Pros:**
- File isolation
- Prevents conflicts
- Good for code generation

**Cons:**
- Requires Git repository
- Slower startup
- More disk space

**Usage:**
```python
orch = Orchestrator(mode="worktree")
```

**Requirements:**
- Must be in a Git repository
- Git worktree support

### Docker Mode

Full containerization for maximum isolation.

**Pros:**
- Complete isolation
- Resource limits
- Reproducible environment

**Cons:**
- Slowest startup
- Requires Docker
- Higher overhead

**Usage:**
```python
orch = Orchestrator(mode="docker")
```

**Requirements:**
- Docker installed and running
- Dockerfile in project root

## Monitoring

### Real-time Monitoring

Enable monitoring to track progress:

```python
from orchestrator import Orchestrator
from orchestrator.monitoring import Monitor

# With orchestrator
orch = Orchestrator(max_workers=5)
result = orch.execute("Complex task", monitor=True)

# Standalone monitor
monitor = Monitor()
monitor.start()

# Run tasks...
# Monitor displays:
# - Active workers
# - Completed/Failed tasks
# - Resource usage (CPU, Memory)
# - Estimated time remaining

monitor.stop()
```

### Monitoring Output Example

```
=== Task Execution Monitor ===
Time: 00:02:15 | Workers: 3/5 active
Progress: [████████████░░░░░░░░] 60% (3/5 completed)

Worker 1: ✓ Completed (45s)
Worker 2: ⚙ In Progress (1m 30s)
Worker 3: ✓ Completed (52s)
Worker 4: ⚙ In Progress (0m 15s)
Worker 5: ⏳ Queued

Resources:
  CPU: 45.2%
  Memory: 1.2 GB / 8.0 GB

ETA: ~1m 20s
```

### Command Line Monitoring

```bash
python orchestrator/main.py --monitor "Your task here"
```

### Accessing Logs

```python
# View structured logs
import json

with open('workspace/logs/orchestrator_20251020_120000.jsonl') as f:
    for line in f:
        log_entry = json.loads(line)
        print(f"{log_entry['timestamp']}: {log_entry['message']}")
```

Log format:
```json
{
  "timestamp": "2025-10-20T12:00:00.123Z",
  "level": "INFO",
  "message": "Worker 1 started",
  "worker_id": 1,
  "task": "Create calculator app"
}
```

## Advanced Usage

### Custom Task Decomposition

```python
from orchestrator import Orchestrator
from orchestrator.ai_task_decomposer import AITaskDecomposer

# Custom decomposer
decomposer = AITaskDecomposer(
    model="claude-sonnet-4-5",
    temperature=0.5
)

# Manually decompose
subtasks = decomposer.decompose(
    "Create three applications: todo, calculator, notes"
)

# Use with orchestrator
orch = Orchestrator(task_decomposer=decomposer)
result = orch.execute("Your task")
```

### Parallel Data Processing

```python
import pandas as pd
from orchestrator import Orchestrator

# Load large dataset
df = pd.read_csv('large_dataset.csv')

# Split data into chunks
chunks = [df[i:i+1000] for i in range(0, len(df), 1000)]

# Process in parallel
orch = Orchestrator(max_workers=len(chunks))

results = []
for i, chunk in enumerate(chunks):
    chunk.to_csv(f'workspace/worker_{i}/input.csv', index=False)

result = orch.execute(
    f"Analyze data in workspace/worker_*/input.csv and generate summary statistics"
)
```

### Custom Worker Implementation

```python
from orchestrator.worker import BaseWorker

class CustomWorker(BaseWorker):
    def execute(self, task):
        # Custom execution logic
        result = self.custom_processing(task)
        return result

    def custom_processing(self, task):
        # Your implementation
        pass

# Use custom worker
orch = Orchestrator(worker_class=CustomWorker)
```

### Chaining Tasks

```python
orch = Orchestrator(max_workers=3)

# Phase 1: Data preparation
result1 = orch.execute("Prepare and clean dataset")

# Phase 2: Analysis (using Phase 1 output)
result2 = orch.execute(f"Analyze cleaned data from {result1['output_dir']}")

# Phase 3: Visualization
result3 = orch.execute(f"Create dashboard from {result2['output_dir']}")
```

## Troubleshooting

### Common Issues

#### Workers Timeout

**Problem:** Tasks exceed timeout limit

**Solution:**
```python
# Increase timeout
orch = Orchestrator(timeout=600)  # 10 minutes
```

Or via environment:
```bash
export ORCHESTRATOR_TIMEOUT=600
```

#### Git Worktree Conflicts

**Problem:** `fatal: 'worktree_worker_1' is already checked out`

**Solution:**
```bash
# Clean up worktrees
git worktree prune

# Or remove manually
rm -rf workspace/worktree_*
git worktree list
git worktree remove <path>
```

#### Claude CLI Not Found

**Problem:** `claude: command not found`

**Solution:**
```bash
# Add to PATH
export PATH="$HOME/.nvm/versions/node/vXX.XX.X/bin:$PATH"

# Or specify full path in config
WINDOWS_CLAUDE_PATH=/full/path/to/claude
```

#### Memory Issues

**Problem:** High memory usage with many workers

**Solution:**
```python
# Reduce max workers
orch = Orchestrator(max_workers=3)

# Or set memory limits (Docker mode)
config = Config(
    mode='docker',
    resources={'max_memory_per_worker': 1024}  # 1GB
)
```

#### Empty Output

**Problem:** Workers complete but produce no output

**Solution:**
1. Check worker logs: `workspace/worker_*/output.txt`
2. Verify permissions: `--dangerously-skip-permissions` flag
3. Enable debug logging: `--log-level DEBUG`

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

orch = Orchestrator(max_workers=3)
result = orch.execute("Your task")

# Check detailed logs
print(result.get('debug_info', {}))
```

### Getting Help

```bash
# Show help
python orchestrator/main.py --help

# Check version
python -c "from orchestrator import __version__; print(__version__)"

# Verify installation
python scripts/verify_modes.py
```

## Best Practices

1. **Start Small**: Test with 1-2 workers before scaling up
2. **Monitor Resources**: Use `--monitor` for long-running tasks
3. **Choose Right Mode**: Subprocess for speed, worktree for isolation
4. **Set Timeouts**: Always configure appropriate timeouts
5. **Check Logs**: Review logs for optimization opportunities
6. **Error Handling**: Implement proper try-catch blocks
7. **Resource Limits**: Don't exceed system capabilities
8. **Clean Workspace**: Periodically clean old workspaces

## Performance Tips

- Use subprocess mode for maximum speed
- Limit workers to `CPU_count - 1`
- Enable monitoring only when needed
- Clean workspace regularly
- Use SSD for workspace directory
- Adjust timeout based on task complexity

## Next Steps

- Read [API Reference](api_reference.md) for detailed class documentation
- See [examples/](../examples/) for code samples
- Check [CONTRIBUTING.md](../CONTRIBUTING.md) for development guide
