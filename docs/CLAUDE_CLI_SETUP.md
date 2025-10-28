# Claude CLI セットアップガイド

このガイドでは、Claude Orchestrator で使用する Claude CLI のインストールと認証設定手順を説明します。

---

## 📋 目次

1. [システム要件](#システム要件)
2. [Claude CLI インストール](#claude-cli-インストール)
3. [認証設定](#認証設定)
4. [トラブルシューティング](#トラブルシューティング)

---

## システム要件

### サポート対象OS

- **Linux**: Ubuntu 20.04+ / Debian 10+
- **macOS**: 10.15+
- **Windows**: Windows 10+ (WSL2 または Git Bash 経由)

### 推奨スペック

- RAM: 4GB以上
- インターネット接続
- Claude Pro または Team サブスクリプション（Long-Lived Session Token 作成用）

---

## Claude CLI インストール

### Linux / WSL (Ubuntu/Debian)

公式インストールスクリプトを使用：

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

インストール後、PATHを確認：

```bash
~/.local/bin/claude --version
```

**出力例:**
```
2.0.25 (Claude Code)
```

### Windows (PowerShell)

管理者権限でPowerShellを開き、以下を実行：

```powershell
irm https://claude.ai/install.ps1 | iex
```

### Windows (CMD)

コマンドプロンプトで以下を実行：

```cmd
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

### macOS

Linux と同じ手順：

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

### NPM経由（代替方法）

Node.jsがインストールされている場合：

```bash
npm install -g @anthropic-ai/claude-code
```

**注意:** `sudo` は使用しないでください。

---

## 認証設定

Claude CLI を使用するには、認証トークンが必要です。

### 方法1: GUIヘルパーを使用（推奨）

Claude Orchestrator には、トークン設定用の GUI ヘルパーが含まれています：

```bash
# プロジェクトルートで実行
python orchestrator/utils/auth_helper.py
```

**手順:**

1. 実行モードを選択（`wsl` または `windows`）
2. GUIダイアログが表示される
3. https://claude.ai/settings/developer にアクセス
4. "Create Long-Lived Session Token" をクリック
5. 生成されたトークンをコピー
6. ダイアログのテキストボックスに貼り付け
7. "保存" ボタンをクリック

### 方法2: 手動設定

#### WSL / Linux

```bash
# 設定ディレクトリを作成
mkdir -p ~/.config/claude

# トークンを保存
echo "your-long-lived-session-token-here" > ~/.config/claude/token.txt
```

#### Windows

```cmd
# 設定ディレクトリを作成
mkdir %USERPROFILE%\.config\claude

# トークンを保存
echo your-long-lived-session-token-here > %USERPROFILE%\.config\claude\token.txt
```

### 方法3: 対話型セットアップ

Claude CLI の対話型コマンドを使用：

```bash
claude setup-token
```

**注意:** このコマンドは対話型セッションが必要で、バックグラウンドでは実行できません。

---

## トークンの取得方法

### ステップ1: Claude.ai にアクセス

1. https://claude.ai/settings/developer にアクセス
2. Claude Pro または Team アカウントでログイン

### ステップ2: トークンを生成

1. "Create Long-Lived Session Token" ボタンをクリック
2. トークン名を入力（例: "Orchestrator Development"）
3. "Create" をクリック

### ステップ3: トークンをコピー

生成されたトークンをコピーします。このトークンは**一度しか表示されません**。

**トークン形式例:**
```
sk-ant-sid01-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 認証確認

トークンが正しく設定されているか確認：

### WSL / Linux

```bash
~/.local/bin/claude --print <<< "Hello Claude!"
```

### Windows

```cmd
claude --print < echo "Hello Claude!"
```

**成功時の出力:**
```
Hello! How can I help you today?
```

**失敗時の出力:**
```
Invalid API key  Please run /login
```

---

## トラブルシューティング

### 問題1: `claude: command not found`

**原因:** PATH に Claude CLI が含まれていない

**解決策:**

```bash
# ~/.bashrc または ~/.zshrc に追加
export PATH="$HOME/.local/bin:$PATH"

# 設定を再読み込み
source ~/.bashrc  # または source ~/.zshrc
```

### 問題2: `Invalid API key`

**原因:** トークンが設定されていないか、無効

**解決策:**

1. トークンファイルが存在するか確認：
   ```bash
   cat ~/.config/claude/token.txt
   ```

2. トークンが正しいか確認（https://claude.ai/settings/developer）

3. 新しいトークンを生成して再設定

### 問題3: WSL で `bash: line 1: D:\...: No such file or directory`

**原因:** Windows パスが WSL パスに変換されていない

**解決策:**

Claude Orchestrator の WorkerManager は自動的にパス変換を行います。直接 `claude` コマンドを実行する場合は、WSL パス形式を使用：

```bash
# Windows パス: D:\user\file.txt
# WSL パス: /mnt/d/user/file.txt
```

### 問題4: Windows で git-bash エラー

**原因:** git-bash が見つからない、または Cygwin fork 問題

**解決策:**

WSL モードを使用（推奨）：

```python
config.execution_mode = "wsl"
config.wsl_distribution = "Ubuntu-24.04"
```

---

## Python からの使用例

### 基本的な使用

```python
from orchestrator.config import OrchestratorConfig
from orchestrator.core.worker_manager import WorkerManager
from orchestrator.core.structured_logging import StructuredLogger

# 設定
config = OrchestratorConfig()
config.execution_mode = "wsl"  # または "windows"
config.wsl_distribution = "Ubuntu-24.04"
config.claude_command = "~/.local/bin/claude"

# ロガー
logger = StructuredLogger(name="my_app", log_dir=Path("logs"))

# WorkerManager
worker_manager = WorkerManager(config=config, logger=logger)
```

### トークン設定（プログラム内）

```python
from orchestrator.utils import setup_claude_token

# GUIでトークン入力
success = setup_claude_token(
    execution_mode="wsl",
    wsl_distribution="Ubuntu-24.04"
)

if success:
    print("✅ 認証完了")
else:
    print("❌ 認証失敗")
```

---

## セキュリティに関する注意

### トークンの取り扱い

- ✅ トークンファイルは `~/.config/claude/token.txt` に保存
- ✅ ファイル権限は `600` (所有者のみ読み書き可能)
- ❌ トークンをコードに直接書かない
- ❌ トークンを Git リポジトリにコミットしない
- ❌ トークンを他人と共有しない

### .gitignore に追加

```gitignore
# Claude CLI token
.config/claude/token.txt
**/token.txt
```

---

## 参考リンク

- [Claude Code 公式ドキュメント](https://docs.claude.com/en/docs/claude-code/setup)
- [Claude API Settings](https://claude.ai/settings/developer)
- [GitHub - Claude Code](https://github.com/anthropics/claude-code)

---

**作成日:** 2025-10-22
**バージョン:** 1.0
**対象:** Claude Orchestrator v11.0+
