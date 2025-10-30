# Parallel-Coding Configuration Reference

Complete configuration reference for the parallel-coding tool.

## Table of Contents

- [Overview](#overview)
- [Configuration Sources](#configuration-sources)
- [Environment Variables](#environment-variables)
- [Configuration File (.env)](#configuration-file-env)
- [Auto-Detection](#auto-detection)
- [Configuration Examples](#configuration-examples)
- [Advanced Configuration](#advanced-configuration)

---

## Overview

The parallel-coding tool uses a **hierarchical configuration system** with automatic detection and sensible defaults.

### Configuration Priority (Highest to Lowest)

1. **Environment Variables** - `PARALLEL_CODING_*`
2. **`.env` File** - Project-specific overrides
3. **Auto-Detection** - System scanning
4. **Defaults** - Built-in fallback values

---

## Configuration Sources

### 1. Environment Variables

Set in your shell or system environment:

```bash
# Bash/Zsh
export PARALLEL_CODING_WORKSPACE_ROOT=./workspace
export PARALLEL_CODING_CODEX_PATH=/usr/local/bin/codex

# Windows PowerShell
$env:PARALLEL_CODING_WORKSPACE_ROOT="./workspace"
$env:PARALLEL_CODING_CODEX_PATH="C:\Program Files\Codex\codex.exe"

# Windows CMD
set PARALLEL_CODING_WORKSPACE_ROOT=./workspace
set PARALLEL_CODING_CODEX_PATH=C:\Program Files\Codex\codex.exe
```

### 2. `.env` File

Create a `.env` file in your project root:

```bash
# Copy template
cp .env.template .env

# Edit configuration
nano .env
```

### 3. Auto-Detection

The tool automatically detects:
- ✅ Project name from directory
- ✅ Project root via git
- ✅ WSL distribution (Windows)
- ✅ Codex CLI location
- ✅ Claude CLI location (including WSL)
- ✅ NVM path
- ✅ Python installation

### 4. Defaults

Built-in fallback values:
- Project name: Current directory name
- Workspace: `{project_root}/workspace`
- Max workers: 4
- Worker timeout: 300 seconds
- Codex model: "gpt-5"

---

## Environment Variables

### Core Paths

#### `PARALLEL_CODING_PROJECT_NAME`
**Description:** Project identifier
**Default:** Current directory name
**Example:** `PARALLEL_CODING_PROJECT_NAME=my-awesome-project`

#### `PARALLEL_CODING_WORKSPACE_ROOT`
**Description:** Root directory for worker workspaces
**Default:** `{project_root}/workspace`
**Example:** `PARALLEL_CODING_WORKSPACE_ROOT=/tmp/parallel-workspace`

**Note:** Can be absolute or relative path. Relative paths are resolved from project root.

### Binary Paths

#### `PARALLEL_CODING_CODEX_PATH`
**Description:** Path to Codex CLI executable
**Default:** Auto-detected from PATH and npm global
**Example:**
```bash
# Linux/macOS
PARALLEL_CODING_CODEX_PATH=/usr/local/bin/codex

# Windows
PARALLEL_CODING_CODEX_PATH=C:\Users\user\AppData\Roaming\npm\codex.cmd
```

#### `PARALLEL_CODING_CLAUDE_PATH`
**Description:** Path to Claude CLI executable
**Default:** Auto-detected from PATH, pip locations, and WSL
**Example:**
```bash
# Linux/macOS
PARALLEL_CODING_CLAUDE_PATH=/home/user/.local/bin/claude

# Windows (WSL detected automatically)
# No need to set - auto-detected in WSL
```

#### `PARALLEL_CODING_PYTHON_PATH`
**Description:** Path to Python interpreter
**Default:** Auto-detected from PATH
**Example:** `PARALLEL_CODING_PYTHON_PATH=/usr/bin/python3.11`

#### `PARALLEL_CODING_GIT_BASH_PATH`
**Description:** Path to Git Bash (Windows only)
**Default:** Auto-detected from common locations
**Example:** `PARALLEL_CODING_GIT_BASH_PATH=C:\Program Files\Git\bin\bash.exe`

### WSL Configuration (Windows Only)

#### `PARALLEL_CODING_WSL_DISTRIBUTION`
**Description:** WSL distribution name
**Default:** Auto-detected via `wsl -l -v`, fallback to "Ubuntu-24.04"
**Example:** `PARALLEL_CODING_WSL_DISTRIBUTION=Ubuntu-24.04`

**Valid values:**
- `Ubuntu-24.04`
- `Ubuntu-22.04`
- `Ubuntu-20.04`
- `Debian`
- Any installed WSL distribution

#### `PARALLEL_CODING_NVM_PATH`
**Description:** NVM bin directory path (for Node.js/Codex)
**Default:** Auto-detected from `$NVM_DIR` or common locations
**Example:** `PARALLEL_CODING_NVM_PATH=/home/user/.nvm/versions/node/v22.21.0/bin`

### Worker Settings

#### `PARALLEL_CODING_MAX_WORKERS`
**Description:** Maximum concurrent workers
**Default:** 4
**Range:** 1-16
**Example:** `PARALLEL_CODING_MAX_WORKERS=8`

**Recommendations:**
- **2-4 workers:** Standard development (4GB+ RAM)
- **4-8 workers:** High-performance (16GB+ RAM)
- **8-16 workers:** Server/CI environments (32GB+ RAM)

#### `PARALLEL_CODING_WORKER_TIMEOUT`
**Description:** Worker execution timeout in seconds
**Default:** 300 (5 minutes)
**Range:** 60-3600
**Example:** `PARALLEL_CODING_WORKER_TIMEOUT=600`

#### `PARALLEL_CODING_CODEX_MODEL`
**Description:** Default Codex model to use
**Default:** "gpt-5"
**Valid values:** "gpt-4", "gpt-5", "o1-preview"
**Example:** `PARALLEL_CODING_CODEX_MODEL=gpt-5`

### Execution Mode

#### `PARALLEL_CODING_EXECUTION_MODE`
**Description:** How to execute workers
**Default:** Auto-detected based on platform
**Valid values:**
- `wsl` - Windows Subsystem for Linux (Windows)
- `windows` - Native Windows (Windows)
- `unix` - Native Unix/Linux (Linux/macOS)

**Example:** `PARALLEL_CODING_EXECUTION_MODE=wsl`

**Auto-detection logic:**
```python
if platform == "Windows":
    if wsl_available:
        mode = "wsl"  # Preferred on Windows
    else:
        mode = "windows"
else:
    mode = "unix"
```

### Logging & Debugging

#### `PARALLEL_CODING_LOG_LEVEL`
**Description:** Logging verbosity
**Default:** "INFO"
**Valid values:** "DEBUG", "INFO", "WARNING", "ERROR"
**Example:** `PARALLEL_CODING_LOG_LEVEL=DEBUG`

#### `PARALLEL_CODING_VERBOSE`
**Description:** Enable verbose output
**Default:** False
**Example:** `PARALLEL_CODING_VERBOSE=true`

---

## Configuration File (.env)

### Template

Copy and customize `.env.template`:

```bash
# =============================================================================
# Parallel-Coding Configuration
# =============================================================================
# Copy this file to .env and customize for your project.
# Environment variables take precedence over .env settings.

# -----------------------------------------------------------------------------
# Core Paths
# -----------------------------------------------------------------------------

# Project workspace (optional - defaults to ./workspace)
# PARALLEL_CODING_WORKSPACE_ROOT=./workspace

# Binary paths (optional - auto-detected if not set)
# PARALLEL_CODING_CODEX_PATH=/usr/local/bin/codex
# PARALLEL_CODING_CLAUDE_PATH=/home/user/.local/bin/claude

# -----------------------------------------------------------------------------
# WSL Configuration (Windows only)
# -----------------------------------------------------------------------------

# WSL distribution (optional - auto-detected if not set)
# PARALLEL_CODING_WSL_DISTRIBUTION=Ubuntu-24.04

# NVM path (optional - auto-detected if not set)
# PARALLEL_CODING_NVM_PATH=/home/user/.nvm/versions/node/v22.21.0/bin

# -----------------------------------------------------------------------------
# Worker Settings
# -----------------------------------------------------------------------------

# Maximum concurrent workers (default: 4)
# PARALLEL_CODING_MAX_WORKERS=4

# Worker timeout in seconds (default: 300)
# PARALLEL_CODING_WORKER_TIMEOUT=300

# Default Codex model (default: gpt-5)
# PARALLEL_CODING_CODEX_MODEL=gpt-5

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

# Log level: DEBUG, INFO, WARNING, ERROR (default: INFO)
# PARALLEL_CODING_LOG_LEVEL=INFO

# Verbose output (default: false)
# PARALLEL_CODING_VERBOSE=false
```

### Loading Priority

When you have both environment variables and `.env`:

```bash
# .env file
PARALLEL_CODING_MAX_WORKERS=8

# Environment variable (this wins!)
export PARALLEL_CODING_MAX_WORKERS=16

# Result: 16 workers
```

---

## Auto-Detection

### Detection Process

The tool automatically scans for configuration in this order:

#### 1. Project Detection
```python
# Try git root
git_root = subprocess.run(["git", "rev-parse", "--show-toplevel"])

# Fallback to current directory
project_root = Path.cwd()
```

#### 2. Binary Detection

**Codex CLI:**
1. Check `PARALLEL_CODING_CODEX_PATH`
2. Check `PATH` (shutil.which)
3. Check npm global paths:
   - Windows: `%APPDATA%\npm\codex.cmd`
   - Linux/macOS: `/usr/local/bin/codex`
4. Check WSL-mounted Windows npm (if on WSL)

**Claude CLI:**
1. Check `PARALLEL_CODING_CLAUDE_PATH`
2. **Check WSL** (Windows only - NEW!)
   - Test `$HOME/.local/bin/claude`
   - Test `/usr/local/bin/claude`
   - Test `/usr/bin/claude`
3. Check `PATH` (shutil.which)
4. Check pip install locations:
   - Linux/macOS: `~/.local/bin/claude`
   - Windows: `%APPDATA%\Python\Scripts\claude.exe`

#### 3. WSL Detection (Windows Only)

```bash
# Parse wsl -l -v output
wsl -l -v
#   NAME            STATE           VERSION
# * Ubuntu-24.04    Running         2

# Extract default distribution
wsl_distribution = "Ubuntu-24.04"

# Fallback if detection fails
wsl_distribution = "Ubuntu-24.04"  # Safe default
```

#### 4. NVM Detection

```bash
# Check $NVM_DIR environment variable
nvm_path = os.getenv("NVM_DIR") + "/versions/node/*/bin"

# Check common locations
# - ~/.nvm/versions/node/*/bin
# - /usr/local/nvm/versions/node/*/bin
```

---

## Configuration Examples

### Example 1: Minimal Setup (Recommended)

Let auto-detection do everything:

```bash
# No .env file needed!
# Just install Codex or Claude:
npm install -g @openai/codex

# Run
python scripts/execute_task_files.py task.md
```

### Example 2: Custom Workspace

Keep workspace outside project:

```bash
# .env
PARALLEL_CODING_WORKSPACE_ROOT=/tmp/my-workspace
```

### Example 3: Specific Binary Versions

Use specific binary locations:

```bash
# .env
PARALLEL_CODING_CODEX_PATH=/usr/local/bin/codex-v2
PARALLEL_CODING_PYTHON_PATH=/usr/bin/python3.11
```

### Example 4: Multiple Projects

Different configs per project:

```bash
# Project A (.env)
PARALLEL_CODING_MAX_WORKERS=8
PARALLEL_CODING_CODEX_MODEL=gpt-5

# Project B (.env)
PARALLEL_CODING_MAX_WORKERS=4
PARALLEL_CODING_CODEX_MODEL=o1-preview
```

### Example 5: WSL Specific (Windows)

Force specific WSL distribution:

```bash
# .env
PARALLEL_CODING_WSL_DISTRIBUTION=Ubuntu-22.04
PARALLEL_CODING_NVM_PATH=/home/user/.nvm/versions/node/v20.0.0/bin
```

### Example 6: High-Performance Server

Maximize throughput:

```bash
# .env
PARALLEL_CODING_MAX_WORKERS=16
PARALLEL_CODING_WORKER_TIMEOUT=600
PARALLEL_CODING_CODEX_MODEL=gpt-5
```

### Example 7: Debug Mode

Enable detailed logging:

```bash
# .env
PARALLEL_CODING_LOG_LEVEL=DEBUG
PARALLEL_CODING_VERBOSE=true
```

---

## Advanced Configuration

### Dynamic Configuration via Python

```python
from orchestrator.config import OrchestratorConfig

# Load from environment
config = OrchestratorConfig.from_env()

# Customize at runtime
config.max_workers = 8
config.worker_timeout = 600

# Use custom config
from orchestrator.core.worker.worker_manager import WorkerManager
manager = WorkerManager(config, logger)
```

### Per-Task Configuration

```python
# Custom timeout for long-running task
config = OrchestratorConfig.from_env()
config.worker_timeout = 1800  # 30 minutes

executor = TaskFileExecutor(config, logger)
await executor.execute_tasks_parallel(["long_task.md"])
```

### Validation

```python
from orchestrator.config import OrchestratorConfig

config = OrchestratorConfig.from_env()

# Check what was detected
print(f"Project: {config.project_name}")
print(f"Codex: {config.codex_command_path}")
print(f"Claude: {config.claude_command_path}")
print(f"WSL: {config.wsl_distribution}")
print(f"NVM: {config.nvm_path}")
```

### Config Cache

Binary discovery is cached for performance:

```python
from orchestrator.utils.binary_discovery import BinaryDiscovery

discovery = BinaryDiscovery()

# First call: scans system (slow)
codex = discovery.find_codex()

# Second call: uses cache (fast)
codex = discovery.find_codex()

# Cache expires after 5 minutes
```

---

## Troubleshooting Configuration

### Check Current Configuration

```bash
# View all detected settings
python -c "from orchestrator.config import OrchestratorConfig; config = OrchestratorConfig.from_env(); print(config)"
```

### Verify Binary Detection

```bash
# Test Codex detection
python -c "from orchestrator.utils.binary_discovery import BinaryDiscovery; d = BinaryDiscovery(); print(f'Codex: {d.find_codex()}')"

# Test Claude detection
python -c "from orchestrator.utils.binary_discovery import BinaryDiscovery; d = BinaryDiscovery(); print(f'Claude: {d.find_claude()}')"
```

### Debug WSL Detection (Windows)

```bash
# Check WSL distributions
wsl -l -v

# Test WSL Claude
wsl -d Ubuntu-24.04 bash -c "which claude"

# Verify PATH
wsl -d Ubuntu-24.04 bash -c "echo \$PATH"
```

### Override Auto-Detection

If auto-detection fails, force specific values:

```bash
# .env
# Force specific values (skip auto-detection)
PARALLEL_CODING_CODEX_PATH=/custom/path/to/codex
PARALLEL_CODING_CLAUDE_PATH=claude
PARALLEL_CODING_WSL_DISTRIBUTION=Ubuntu-24.04
PARALLEL_CODING_NVM_PATH=/home/user/.nvm/versions/node/v22.21.0/bin
```

---

## Best Practices

### 1. Use Auto-Detection When Possible
✅ **Recommended:** Let the tool detect binaries automatically
❌ **Avoid:** Hardcoding paths unless necessary

### 2. Project-Specific `.env`
✅ **Recommended:** One `.env` per project
❌ **Avoid:** Global environment variables (unless shared across all projects)

### 3. Version Control
✅ **Commit:** `.env.template`
❌ **Don't commit:** `.env` (add to `.gitignore`)

### 4. Document Custom Settings
✅ **Recommended:** Comment why you override defaults
```bash
# .env
# Using older Node version for compatibility with legacy dependencies
PARALLEL_CODING_NVM_PATH=/home/user/.nvm/versions/node/v18.0.0/bin
```

### 5. Validate After Changes
```bash
# After updating .env
python -c "from orchestrator.config import OrchestratorConfig; config = OrchestratorConfig.from_env(); print(config)"
```

---

## Related Documentation

- [INSTALLATION.md](INSTALLATION.md) - Installation guide
- [README.md](README.md) - Quick start and usage
- [.env.template](.env.template) - Configuration template

---

**Last Updated:** 2025-10-30
**Version:** 2.0.0-dev
