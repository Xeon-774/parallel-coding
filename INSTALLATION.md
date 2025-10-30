# Parallel-Coding Installation Guide

Complete installation guide for the parallel-coding tool with cross-project compatibility.

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Detailed Installation](#detailed-installation)
- [Platform-Specific Setup](#platform-specific-setup)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

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

## Quick Start

### 1. Clone the Repository

```bash
# As a standalone tool
git clone https://github.com/Xeon-774/parallel-coding.git
cd parallel-coding

# Or as a Git submodule in your project
cd your-project
git submodule add https://github.com/Xeon-774/parallel-coding.git dev-tools/parallel-coding
git submodule update --init --recursive
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install AI CLI Tools

**Option A: Codex CLI (Recommended)**
```bash
npm install -g @openai/codex
```

**Option B: Claude CLI**
```bash
# Follow installation guide at https://docs.claude.com/en/docs/claude-code
# For Windows WSL:
wsl -d Ubuntu-24.04
# Inside WSL:
pip install anthropic-claude-cli
```

### 4. Verify Installation

```bash
python scripts/verify_installation.py
```

Expected output:
```
✅ Python 3.11.0 found
✅ Git 2.42.0 found
✅ Codex CLI found at /usr/local/bin/codex
✅ Configuration system working
✅ All dependencies satisfied!
```

### 5. Run Hello World Test

```bash
# Create a simple test task
echo "Create a Python file that prints 'Hello, World!'" > test_task.md

# Execute with Codex
python scripts/execute_task_files.py --codex test_task.md

# Or with Claude
python scripts/execute_task_files.py test_task.md
```

---

## Detailed Installation

### Step 1: Python Environment Setup

**Option A: System Python (Recommended for most users)**
```bash
# Verify Python version
python --version  # Should be 3.10+

# Install pip if not available
python -m ensurepip --upgrade

# Install dependencies
pip install -r requirements.txt
```

**Option B: Virtual Environment (Isolated installation)**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Option C: Conda Environment**
```bash
# Create conda environment
conda create -n parallel-coding python=3.11
conda activate parallel-coding

# Install dependencies
pip install -r requirements.txt
```

### Step 2: AI CLI Installation

#### Codex CLI Setup

**Installation:**
```bash
# Install via npm
npm install -g @openai/codex

# Verify installation
codex --version
which codex  # Should show path like /usr/local/bin/codex
```

**Configuration:**
```bash
# Set OpenAI API key
export OPENAI_API_KEY=sk-...

# Or add to ~/.bashrc or ~/.zshrc for persistence
echo 'export OPENAI_API_KEY=sk-...' >> ~/.bashrc
source ~/.bashrc
```

#### Claude CLI Setup

**Windows WSL Installation:**
```bash
# Enter WSL
wsl -d Ubuntu-24.04

# Install Claude CLI
pip install anthropic-claude-cli

# Verify installation
claude --version
which claude  # Should show path like /home/user/.local/bin/claude
```

**Linux/macOS Installation:**
```bash
# Install via pip
pip install anthropic-claude-cli

# Verify installation
claude --version
```

**Configuration:**
```bash
# Set Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...

# Or add to profile for persistence
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.bashrc
source ~/.bashrc
```

### Step 3: Configuration (Optional)

The tool uses auto-detection for most settings, but you can customize via `.env` file:

```bash
# Copy template
cp .env.template .env

# Edit configuration
nano .env  # or your preferred editor
```

Example `.env`:
```bash
# Core paths (auto-detected if not set)
PARALLEL_CODING_WORKSPACE_ROOT=./workspace
PARALLEL_CODING_CODEX_PATH=/usr/local/bin/codex
PARALLEL_CODING_CLAUDE_PATH=/home/user/.local/bin/claude

# WSL configuration (Windows only - auto-detected if not set)
PARALLEL_CODING_WSL_DISTRIBUTION=Ubuntu-24.04
PARALLEL_CODING_NVM_PATH=/home/user/.nvm/versions/node/v22.21.0/bin

# Worker settings
PARALLEL_CODING_MAX_WORKERS=4
PARALLEL_CODING_WORKER_TIMEOUT=300
```

See [CONFIGURATION.md](CONFIGURATION.md) for complete reference.

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
# Update packages
sudo apt update && sudo apt upgrade -y

# Install build essentials
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
# From Windows PowerShell
python scripts/verify_installation.py --check-wsl
```

### Linux (Ubuntu/Debian)

**1. Install dependencies:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip git nodejs npm

# Install Codex CLI
sudo npm install -g @openai/codex

# Install Claude CLI
pip install anthropic-claude-cli
```

**2. Add to PATH (if needed):**
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### macOS

**1. Install Homebrew (if not installed):**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**2. Install dependencies:**
```bash
# Install Python
brew install python

# Install Node.js
brew install node

# Install Codex CLI
npm install -g @openai/codex

# Install Claude CLI
pip3 install anthropic-claude-cli
```

---

## Verification

### Basic Verification

```bash
# Run verification script
python scripts/verify_installation.py
```

### Comprehensive Verification

```bash
# Test auto-detection
python -c "from orchestrator.config import OrchestratorConfig; config = OrchestratorConfig.from_env(); print(config)"

# Expected output:
# OrchestratorConfig(
#   project_name='parallel-coding',
#   project_root=PosixPath('/path/to/parallel-coding'),
#   codex_command_path=PosixPath('/usr/local/bin/codex'),
#   ...
# )
```

### Test Execution

```bash
# Create test task
cat > hello_world.md <<EOF
# Task: Create Hello World Script
Create a Python file named hello.py that prints "Hello, World!"
EOF

# Execute with Codex
python scripts/execute_task_files.py --codex hello_world.md

# Check results
ls workspace/worker_1/  # Should contain hello.py
```

---

## Troubleshooting

### Common Issues

#### Issue 1: "Codex CLI not found"

**Symptoms:**
```
Error: Codex CLI not found. Install with: npm install -g @openai/codex
```

**Solutions:**
```bash
# Solution 1: Install Codex globally
npm install -g @openai/codex

# Solution 2: Verify npm global path
npm config get prefix  # Should be in your PATH

# Solution 3: Add npm global bin to PATH
export PATH="$(npm config get prefix)/bin:$PATH"

# Solution 4: Specify path manually in .env
echo "PARALLEL_CODING_CODEX_PATH=/path/to/codex" >> .env
```

#### Issue 2: "WSL distribution not found" (Windows)

**Symptoms:**
```
Error: 指定された名前のディストリビューションはありません
Error code: Wsl/Service/WSL_E_DISTRO_NOT_FOUND
```

**Solutions:**
```bash
# Solution 1: List installed distributions
wsl -l -v

# Solution 2: Install Ubuntu-24.04
wsl --install -d Ubuntu-24.04

# Solution 3: Set default distribution
wsl --set-default Ubuntu-24.04

# Solution 4: Specify distribution in .env
echo "PARALLEL_CODING_WSL_DISTRIBUTION=Ubuntu-24.04" >> .env
```

#### Issue 3: "Claude command not found" (WSL mode)

**Symptoms:**
```
bash: line 1: claude: command not found
```

**Solutions:**
```bash
# Solution 1: Install Claude CLI in WSL
wsl -d Ubuntu-24.04
pip install anthropic-claude-cli

# Solution 2: Verify PATH includes Claude
which claude
echo $PATH

# Solution 3: Add .local/bin to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Solution 4: Use Codex instead
python scripts/execute_task_files.py --codex task.md
```

#### Issue 4: "Permission denied" errors

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/path/to/file'
```

**Solutions:**
```bash
# Solution 1: Fix workspace permissions
chmod -R u+rwx workspace/

# Solution 2: Run without sudo (recommended)
# Don't use sudo unless absolutely necessary

# Solution 3: Change workspace location
mkdir -p ~/parallel-coding-workspace
echo "PARALLEL_CODING_WORKSPACE_ROOT=~/parallel-coding-workspace" >> .env
```

#### Issue 5: Import errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'orchestrator'
```

**Solutions:**
```bash
# Solution 1: Install dependencies
pip install -r requirements.txt

# Solution 2: Verify Python path
python -c "import sys; print(sys.path)"

# Solution 3: Install in development mode
pip install -e .

# Solution 4: Add project to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Getting Help

If you encounter issues not covered here:

1. **Check logs:** `workspace/worker_1/orchestrator_terminal.log`
2. **Run diagnostics:** `python scripts/verify_installation.py --verbose`
3. **Report issues:** [GitHub Issues](https://github.com/Xeon-774/parallel-coding/issues)
4. **Documentation:** See [CONFIGURATION.md](CONFIGURATION.md) for detailed settings

---

## Next Steps

After successful installation:

1. Read [CONFIGURATION.md](CONFIGURATION.md) for advanced configuration
2. Read [README.md](README.md) for usage examples
3. Try the example tasks in `examples/` directory
4. Integrate into your project workflow

**Happy parallel coding!** 🚀
