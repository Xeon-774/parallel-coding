# Parallel-Coding Setup Guide

Quick setup guide to get parallel-coding running in minutes.

## Quick Setup (5 Minutes)

### Step 1: Clone Repository

```bash
git clone https://github.com/Xeon-774/parallel-coding.git
cd parallel-coding
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
python scripts/execute_task_files.py --codex test.md

# Check results
ls workspace/worker_1/
```

---

## Platform-Specific Setup

### Windows with WSL2

**Recommended configuration for best compatibility:**

```powershell
# 1. Install WSL2 (if not already installed)
wsl --install -d Ubuntu-24.04

# 2. Inside WSL, install Claude CLI
wsl -d Ubuntu-24.04
pip install anthropic-claude-cli
export ANTHROPIC_API_KEY=sk-ant-...
exit

# 3. Install Codex on Windows (for Codex workers)
npm install -g @openai/codex

# 4. Verify
python -c "from orchestrator.utils.binary_discovery import BinaryDiscovery; d = BinaryDiscovery(); print(f'Claude: {d.find_claude()}'); print(f'Codex: {d.find_codex()}')"
```

**Expected output:**
```
Claude: claude  ✓ (detected in WSL)
Codex: C:\Users\...\npm\codex.cmd  ✓
```

### Linux/macOS

```bash
# Install Node.js (for Codex)
# Ubuntu/Debian:
sudo apt install nodejs npm

# macOS:
brew install node

# Install Codex
npm install -g @openai/codex

# Install Claude
pip install anthropic-claude-cli

# Set API keys
echo 'export OPENAI_API_KEY=sk-...' >> ~/.bashrc
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.bashrc
source ~/.bashrc
```

---

## Configuration (Optional)

**No configuration needed!** The tool auto-detects everything.

### Optional: Custom Configuration

Create `.env` file for project-specific settings:

```bash
cp .env.template .env
nano .env
```

Example `.env`:
```bash
# Custom workspace location
PARALLEL_CODING_WORKSPACE_ROOT=/tmp/my-workspace

# Force specific WSL distribution (Windows)
PARALLEL_CODING_WSL_DISTRIBUTION=Ubuntu-24.04

# Increase worker limit
PARALLEL_CODING_MAX_WORKERS=8
```

See [CONFIGURATION.md](CONFIGURATION.md) for all options.

---

## Setup Scripts

### Automated Setup Helpers

The repository includes helper scripts for common setup tasks:

#### 1. Environment Setup
```bash
python scripts/setup_environment.py
```
Checks and validates your environment setup.

#### 2. WSL Claude Setup (Windows)
```bash
python setup_wsl_claude.py
```
Helps install and configure Claude CLI in WSL.

#### 3. Claude Token Setup
```bash
python setup_claude_token.py
```
Securely configures Claude API token.

---

## Verification Checklist

After setup, verify everything works:

- [ ] Python 3.10+ installed: `python --version`
- [ ] Dependencies installed: `pip list | grep -E "(pydantic|fastapi)"`
- [ ] Codex or Claude CLI accessible: `codex --version` or `claude --version`
- [ ] API keys configured: `echo $OPENAI_API_KEY` or `echo $ANTHROPIC_API_KEY`
- [ ] Config loads: `python -c "from orchestrator.config import OrchestratorConfig; OrchestratorConfig.from_env()"`
- [ ] Test task runs: `python scripts/execute_task_files.py test.md`

---

## Troubleshooting

### Common Issues

#### Issue: "Codex CLI not found"
```bash
# Check npm global path
npm config get prefix

# Add to PATH if needed
export PATH="$(npm config get prefix)/bin:$PATH"

# Or specify manually
echo 'PARALLEL_CODING_CODEX_PATH=/path/to/codex' >> .env
```

#### Issue: "Claude CLI not found" (Windows)
```bash
# Install in WSL
wsl -d Ubuntu-24.04
pip install anthropic-claude-cli

# Verify PATH
which claude  # Should show: /home/user/.local/bin/claude

# Add to PATH if needed
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

#### Issue: "WSL distribution not found"
```bash
# List installed distributions
wsl -l -v

# Install Ubuntu if needed
wsl --install -d Ubuntu-24.04

# Set as default
wsl --set-default Ubuntu-24.04
```

#### Issue: "Permission denied"
```bash
# Fix workspace permissions
chmod -R u+rwx workspace/

# Or use custom workspace
echo 'PARALLEL_CODING_WORKSPACE_ROOT=/tmp/workspace' >> .env
```

---

## Next Steps

After successful setup:

1. **Read Documentation**
   - [INSTALLATION.md](INSTALLATION.md) - Detailed installation guide
   - [CONFIGURATION.md](CONFIGURATION.md) - Configuration reference
   - [README.md](README.md) - Usage examples

2. **Try Examples**
   ```bash
   # Run example tasks
   python scripts/execute_task_files.py examples/*.md
   ```

3. **Integrate with Your Project**
   ```bash
   # As submodule
   cd your-project
   git submodule add https://github.com/Xeon-774/parallel-coding.git tools/parallel-coding
   ```

4. **Customize Configuration**
   - Create project-specific `.env`
   - Adjust worker count for your hardware
   - Set preferred AI model

---

## Getting Help

- **Documentation**: See [INSTALLATION.md](INSTALLATION.md) and [CONFIGURATION.md](CONFIGURATION.md)
- **Issues**: [GitHub Issues](https://github.com/Xeon-774/parallel-coding/issues)
- **Logs**: Check `workspace/worker_1/orchestrator_terminal.log`

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
