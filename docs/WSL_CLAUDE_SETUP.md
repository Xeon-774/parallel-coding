# WSL Claude CLI Setup Guide

**Orchestrator Authentication Method**: WSL Claude CLI Login

---

## Overview

並列AIツール (Claude Orchestrator) は、WSL環境にインストールされたClaude CLIを使用します。

**重要**: APIトークン認証は廃止されました。代わりにWSL Claude CLIのログイン機能を使用します。

---

## Prerequisites

### 1. WSL (Windows Subsystem for Linux)

Windowsで実行する場合、WSLが必要です：

```powershell
# Windows PowerShell (管理者権限)
wsl --install Ubuntu-24.04
```

**インストール後、Windowsを再起動してください。**

---

## Setup Steps

### Step 1: Install WSL (if not already installed)

```powershell
# Check WSL version
wsl --version

# List installed distributions
wsl -l -v

# Install Ubuntu-24.04 (recommended)
wsl --install Ubuntu-24.04
```

### Step 2: Open WSL Terminal

```powershell
# Launch WSL
wsl -d Ubuntu-24.04
```

### Step 3: Claude CLI Login

WSL内でClaudeコマンドを実行してログイン：

```bash
# WSL terminal内で実行
claude

# 初回実行時、ログインプロンプトが表示されます
# ブラウザが開き、Anthropicアカウントでログイン
# ログイン後、WSL内のClaude CLIが使用可能になります
```

**Expected Output**:
```
Welcome to Claude CLI!

Please login to continue:
  1. Browser will open automatically
  2. Login with your Anthropic account
  3. Authorize Claude CLI

Waiting for authentication...

[SUCCESS] Logged in as: your-email@example.com
```

### Step 4: Verify Claude CLI

```bash
# WSL terminal内で実行
claude --version

# Claude CLIが正常にインストールされているか確認
# Expected output: Claude CLI v1.x.x
```

### Step 5: Verify Orchestrator Environment

Windowsに戻って環境確認：

```bash
# Windows PowerShell
cd D:\user\ai_coding\AI_Investor\tools\parallel-coding
python scripts/setup_environment.py
```

**Expected Output**:
```
============================================================
[SUCCESS] Environment setup complete!
============================================================

Environment variables set:
  CLAUDE_CODE_GIT_BASH_PATH=C:\opt\Git.Git\usr\bin\bash.exe
  MAX_WORKERS=8
  MAX_DEPTH=3

============================================================
Claude Authentication: WSL Claude CLI
============================================================

[INFO] API token authentication is deprecated.
      Please use WSL Claude CLI login instead:

  1. Install WSL (Ubuntu-24.04 or similar)
  2. Open WSL terminal
  3. Run: claude
  4. Follow login prompts

  After login, orchestrator will use WSL Claude automatically.

[OK] You can now run tests: pytest tests/ -v
```

---

## How Orchestrator Uses WSL Claude

### Architecture:

```
[Windows] Orchestrator (Python)
    ↓ spawn process via wexpect/pexpect
[WSL] Claude CLI (authenticated)
    ↓ execute commands
[WSL] Git worktrees (isolated)
```

### Workflow:

1. **Orchestrator starts** (Windows)
2. **Spawns WSL process** via `wsl -d Ubuntu-24.04 claude ...`
3. **Claude CLI executes** (already authenticated from Step 3)
4. **Git operations** happen in WSL isolated worktrees
5. **Results aggregated** back to Windows orchestrator

---

## Troubleshooting

### Problem: "claude: command not found"

**Solution**:
```bash
# WSL terminal内で実行
# Claude CLIが自動インストールされていない場合、手動インストール

# Option 1: Install via npm (if Node.js installed)
npm install -g @anthropic-ai/claude-cli

# Option 2: Install via official installer
curl -fsSL https://claude.ai/install.sh | sh

# Verify installation
which claude
claude --version
```

### Problem: "Not logged in"

**Solution**:
```bash
# WSL terminal内で実行
claude logout
claude  # Login again
```

### Problem: WSL not installed

**Solution**:
```powershell
# Windows PowerShell (管理者権限)
wsl --install
# Restart Windows
wsl --install Ubuntu-24.04
```

---

## Testing Claude CLI

### Simple Test:

```bash
# WSL terminal内で実行
claude "What is 2+2?"

# Expected: Claude responds with the answer
# Output: "2 + 2 equals 4."
```

### Verify Orchestrator Can Use WSL Claude:

```bash
# Windows PowerShell
cd D:\user\ai_coding\AI_Investor\tools\parallel-coding
pytest tests/test_simple_worker_wsl.py -v

# This test spawns a WSL Claude instance and verifies communication
```

---

## Why WSL Claude CLI Instead of API Token?

### Advantages:

1. ✅ **Simpler authentication**: One-time login via browser
2. ✅ **No token management**: No .env file token configuration
3. ✅ **Secure**: Token stored in WSL, not exposed in environment variables
4. ✅ **Standard workflow**: Same as using Claude Code normally
5. ✅ **Auto-updates**: Claude CLI updates automatically

### Migration from API Token (Deprecated):

```diff
# Old method (DEPRECATED):
- export CLAUDE_API_TOKEN=sk-ant-api03-...
- python orchestrator.py

# New method (CURRENT):
+ wsl -d Ubuntu-24.04
+ claude  # Login once
+ exit
+ python orchestrator.py  # Uses WSL Claude automatically
```

---

## Summary

| Step | Action | Status |
|------|--------|--------|
| 1 | Install WSL | ✅ `wsl --install Ubuntu-24.04` |
| 2 | Open WSL | ✅ `wsl -d Ubuntu-24.04` |
| 3 | Login to Claude CLI | ✅ `claude` (browser login) |
| 4 | Verify Claude | ✅ `claude --version` |
| 5 | Verify Environment | ✅ `python scripts/setup_environment.py` |

**After completing these steps, you are ready for Phase 1 validation!**

---

## Future: API Key Authentication

**Status**: 🟡 Planned for future implementation (low priority)

WSL Claude CLI is currently the only supported authentication method. API Key and Subscribe Token authentication may be added in the future when time allows.

See `docs/FUTURE_ENHANCEMENTS.md` for details.

---

**Last Updated**: 2025-10-22
**Authentication Method**: WSL Claude CLI Login (Browser-based)
**Deprecated Method**: ~~API Token~~ (Removed, may be re-implemented later)
**Future Methods**: API Key, Subscribe Token (See FUTURE_ENHANCEMENTS.md)
