# Getting Started with Parallel-Coding

Complete guide to install and run parallel-coding in minutes.

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Start (5 Minutes)](#quick-start-5-minutes)
- [Detailed Installation](#detailed-installation)
- [Platform-Specific Setup](#platform-specific-setup)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

---

## System Requirements

### Supported Platforms

- ✅ Windows 10/11 with WSL2
- ✅ Linux (Ubuntu 20.04+, Debian, etc.)
- ✅ macOS (Intel and Apple Silicon)

### Required Software

1. **Python 3.10+**
   - Installation: [python.org/downloads](https://www.python.org/downloads/)
   - Verify: `python --version`

2. **Git**
   - Installation: [git-scm.com](https://git-scm.com/)
   - Verify: `git --version`

3. **AI CLI Tools** (at least one):
   - **Codex CLI**: `npm install -g @openai/codex` (Recommended)
   - **Claude CLI**: See [Claude Code Setup](https://docs.claude.com/en/docs/claude-code)

### Optional but Recommended

- **WSL2** (Windows only): For cross-platform compatibility
- **NVM**: For managing Node.js versions
- **Docker**: For isolated testing environments

---

## Quick Start (5 Minutes)

### Step 1: Clone Repository

```bash
# As a standalone tool
git clone https://github.com/Xeon-774/parallel-coding.git
cd parallel-coding

# Or as a Git submodule in your project
cd your-project
git submodule add https://github.com/Xeon-774/parallel-coding.git tools/parallel-coding
cd tools/parallel-coding
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Install AI CLI

**Choose one:**

**Option A: Codex (Recommended)**
```bash
npm install -g @openai/codex
export OPENAI_API_KEY=sk-...
```

**Option B: Claude**
```bash
# For Windows WSL:
wsl -d Ubuntu-24.04
pip install anthropic-claude-cli
export ANTHROPIC_API_KEY=sk-ant-...

# For Linux/macOS:
pip install anthropic-claude-cli
export ANTHROPIC_API_KEY=sk-ant-...
```

### Step 4: Verify Installation

```bash
python -c "from orchestrator.config import OrchestratorConfig; config = OrchestratorConfig.from_env(); print(f'✓ Config OK: {config.project_name}')"
```

### Step 5: Run Test Task

```bash
# Create test task
echo "Create a Python file that prints 'Hello, World!'" > test.md

# Execute
python scripts/execute_task_files.py test.md

# Check results
ls workspace/worker_1/
```

**Done!** You're ready to use parallel-coding. See [configuration.md](configuration.md) for customization.

---

## Detailed Installation

### Python Environment Setup

**Option A: System Python (Recommended)**
```bash
# Verify Python version
python --version  # Should be 3.10+

# Install dependencies
pip install -r requirements.txt
```

**Option B: Virtual Environment (Isolated)**
```bash
# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Option C: Conda Environment**
```bash
conda create -n parallel-coding python=3.11
conda activate parallel-coding
pip install -r requirements.txt
```

### AI CLI Installation

#### Codex CLI Setup

```bash
# Install via npm
npm install -g @openai/codex

# Verify
codex --version
which codex  # Should show path like /usr/local/bin/codex

# Set API key
export OPENAI_API_KEY=sk-...

# Persist (optional)
echo 'export OPENAI_API_KEY=sk-...' >> ~/.bashrc
source ~/.bashrc
```

#### Claude CLI Setup

**Windows WSL:**
```bash
# Enter WSL
wsl -d Ubuntu-24.04

# Install
pip install anthropic-claude-cli

# Verify
claude --version
which claude  # Should show /home/user/.local/bin/claude

# Set API key
export ANTHROPIC_API_KEY=sk-ant-...
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.bashrc
```

**Linux/macOS:**
```bash
# Install
pip install anthropic-claude-cli

# Verify
claude --version

# Set API key
export ANTHROPIC_API_KEY=sk-ant-...
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.bashrc
source ~/.bashrc
```

### Configuration (Optional)

**No configuration needed!** The tool auto-detects everything.

For customization, create `.env` file:

```bash
# Copy template
cp .env.template .env
```

Example `.env`:
```bash
# Custom workspace location
PARALLEL_CODING_WORKSPACE_ROOT=/tmp/my-workspace

# Force specific WSL distribution (Windows)
PARALLEL_CODING_WSL_DISTRIBUTION=Ubuntu-24.04

# Increase worker limit
PARALLEL_CODING_MAX_WORKERS=8

# Specify binary paths (auto-detected if not set)
PARALLEL_CODING_CODEX_PATH=/usr/local/bin/codex
PARALLEL_CODING_CLAUDE_PATH=/home/user/.local/bin/claude
```

See [configuration.md](configuration.md) for all options.

---

## Platform-Specific Setup

### Windows with WSL2

**1. Install WSL2:**
```powershell
# Run in PowerShell as Administrator
wsl --install -d Ubuntu-24.04
wsl --set-default-version 2
```

**2. Configure WSL:**
```bash
# Inside WSL
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential python3-pip git

# Install Node.js via NVM (for Codex)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 22
nvm use 22
```

**3. Install AI CLIs in WSL:**
```bash
# Codex CLI
npm install -g @openai/codex

# Claude CLI
pip install anthropic-claude-cli
```

**4. Verify WSL integration:**
```bash
# From Windows
python -c "from orchestrator.utils.binary_discovery import BinaryDiscovery; d = BinaryDiscovery(); print(f'Claude: {d.find_claude()}'); print(f'Codex: {d.find_codex()}')"
```

Expected output:
```
Claude: claude  ✓ (detected in WSL)
Codex: C:\Users\...\npm\codex.cmd  ✓
```

### Linux (Ubuntu/Debian)

```bash
# Install dependencies
sudo apt update
sudo apt install -y python3 python3-pip git nodejs npm

# Install Codex CLI
sudo npm install -g @openai/codex

# Install Claude CLI
pip install anthropic-claude-cli

# Add to PATH (if needed)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python node

# Install Codex CLI
npm install -g @openai/codex

# Install Claude CLI
pip3 install anthropic-claude-cli
```

---

## Verification

### Verification Checklist

After setup, verify everything works:

- [ ] Python 3.10+ installed: `python --version`
- [ ] Dependencies installed: `pip list | grep -E "(pydantic|fastapi)"`
- [ ] Codex or Claude CLI accessible: `codex --version` or `claude --version`
- [ ] API keys configured: `echo $OPENAI_API_KEY` or `echo $ANTHROPIC_API_KEY`
- [ ] Config loads: `python -c "from orchestrator.config import OrchestratorConfig; OrchestratorConfig.from_env()"`
- [ ] Test task runs: `python scripts/execute_task_files.py test.md`

### Test Execution

```bash
# Create test task
cat > hello_world.md <<EOF
# Task: Create Hello World Script
Create a Python file named hello.py that prints "Hello, World!"
EOF

# Execute with Codex
python scripts/execute_task_files.py --codex hello_world.md

# Or with Claude
python scripts/execute_task_files.py hello_world.md

# Check results
ls workspace/worker_1/  # Should contain hello.py
python workspace/worker_1/hello.py  # Should print "Hello, World!"
```

---

## Troubleshooting

### Common Issues

#### Issue 1: "Codex CLI not found"

```bash
# Check npm global path
npm config get prefix

# Add to PATH if needed
export PATH="$(npm config get prefix)/bin:$PATH"

# Or specify manually in .env
echo 'PARALLEL_CODING_CODEX_PATH=/path/to/codex' >> .env
```

#### Issue 2: "Claude CLI not found" (Windows)

```bash
# Install in WSL
wsl -d Ubuntu-24.04
pip install anthropic-claude-cli

# Verify PATH
which claude  # Should show: /home/user/.local/bin/claude

# Add to PATH if needed
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

#### Issue 3: "WSL distribution not found"

```bash
# List installed distributions
wsl -l -v

# Install Ubuntu if needed
wsl --install -d Ubuntu-24.04

# Set as default
wsl --set-default Ubuntu-24.04

# Or specify in .env
echo 'PARALLEL_CODING_WSL_DISTRIBUTION=Ubuntu-24.04' >> .env
```

#### Issue 4: "Permission denied"

```bash
# Fix workspace permissions
chmod -R u+rwx workspace/

# Or use custom workspace
echo 'PARALLEL_CODING_WORKSPACE_ROOT=/tmp/workspace' >> .env
```

#### Issue 5: Import errors

```bash
# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Getting Help

- **Documentation**: See [configuration.md](configuration.md) for detailed settings
- **Issues**: [GitHub Issues](https://github.com/Xeon-774/parallel-coding/issues)
- **Logs**: Check `workspace/worker_1/orchestrator_terminal.log`

---

## Next Steps

After successful setup:

### 1. Read Documentation

- [configuration.md](configuration.md) - Configuration reference
- [integration.md](integration.md) - Add to your project
- [../README.md](../README.md) - Usage examples

### 2. Try Examples

```bash
# Run example tasks
python scripts/execute_task_files.py examples/*.md
```

### 3. Integrate with Your Project

```bash
# As submodule
cd your-project
git submodule add https://github.com/Xeon-774/parallel-coding.git tools/parallel-coding

# Create project-specific .env
cp tools/parallel-coding/.env.template .env
nano .env
```

### 4. Customize Configuration

- Create project-specific `.env`
- Adjust worker count for your hardware
- Set preferred AI model

---

## Quick Reference

### Essential Commands

```bash
# Run single task with Codex
python scripts/execute_task_files.py --codex task.md

# Run with Claude
python scripts/execute_task_files.py task.md

# Run multiple tasks in parallel
python scripts/execute_task_files.py task1.md task2.md task3.md

# Check configuration
python -c "from orchestrator.config import OrchestratorConfig; print(OrchestratorConfig.from_env())"

# Check binary detection
python -c "from orchestrator.utils.binary_discovery import BinaryDiscovery; d = BinaryDiscovery(); print(f'Codex: {d.find_codex()}'); print(f'Claude: {d.find_claude()}')"
```

### Environment Variables

```bash
# API Keys
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# Optional overrides
export PARALLEL_CODING_MAX_WORKERS=8
export PARALLEL_CODING_WORKER_TIMEOUT=600
export PARALLEL_CODING_CODEX_MODEL=gpt-5
```

---

**Setup Time:** ~5 minutes
**Last Updated:** 2025-10-30
**Version:** 2.0.0-dev

For advanced configuration, see [configuration.md](configuration.md).

Happy parallel coding! 🚀
