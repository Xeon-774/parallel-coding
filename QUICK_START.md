# クイックスタート - Claude Orchestrator

このガイドでは、Claude Orchestrator を最速でセットアップして動作確認するまでの手順を説明します。

---

## 🚀 1コマンドで完全自動セットアップ

### 最も簡単な方法：自動セットアップスクリプト ⭐

```bash
python setup_wsl_claude.py
```

**このスクリプトが自動的に行うこと:**
1. ✅ WSL (Ubuntu-24.04) への Claude CLI インストール
2. ✅ GUIダイアログでトークン入力
3. ✅ 認証設定・確認
4. ✅ 動作テスト

**手順:**
1. 上記コマンドを実行
2. GUIダイアログが表示されたら、https://claude.ai/settings/developer でトークンを生成
3. トークンをダイアログに貼り付け
4. 完了！

---

## 📖 手動セットアップ（詳細制御したい場合）

### ステップ1: Claude CLI インストール (WSL)

```bash
# WSL (Ubuntu) で実行
curl -fsSL https://claude.ai/install.sh | bash
```

**確認:**
```bash
~/.local/bin/claude --version
# 出力: 2.0.25 (Claude Code)
```

### ステップ2: Claude API トークン設定

#### 方法A: 対話型スクリプト（推奨）

```bash
python setup_claude_token.py
```

**手順:**
1. https://claude.ai/settings/developer にアクセス
2. "Create Long-Lived Session Token" をクリック
3. トークンをコピー
4. スクリプトに貼り付け

#### 方法B: 環境変数

```bash
export CLAUDE_API_TOKEN="sk-ant-sid01-xxxxx..."
```

#### 方法C: ファイル

```bash
echo "sk-ant-sid01-xxxxx..." > ~/.claude_token
```

### ステップ3: 動作確認テスト

```bash
python tests/test_simple_worker_wsl.py
```

**成功時の出力:**
```
======================================================================
WorkerAI起動テスト (WSL Mode)
======================================================================

[SUCCESS] WorkerAI起動・実行成功！
OrchestratorAI <-> WorkerAI 対話が正常に機能しています。
```

---

## 📖 基本的な使い方

### Python コードから使用

```python
from pathlib import Path
from orchestrator.config import OrchestratorConfig
from orchestrator.core.worker_manager import WorkerManager
from orchestrator.core.structured_logging import StructuredLogger

# 設定
config = OrchestratorConfig()
config.execution_mode = "wsl"
config.wsl_distribution = "Ubuntu-24.04"
config.workspace_root = "workspace/my_project"

# ロガー
logger = StructuredLogger(
    name="my_app",
    log_dir=Path(config.workspace_root)
)

# WorkerManager
worker_manager = WorkerManager(
    config=config,
    logger=logger,
    user_approval_callback=None  # 自動承認モード
)

# タスク定義
task = {
    "name": "Hello Task",
    "prompt": "Hello from OrchestratorAI! Please respond."
}

# WorkerAI起動・実行
session = worker_manager.spawn_worker(
    worker_id="worker_1",
    task=task
)

result = worker_manager.run_interactive_session(session.worker_id)

# 結果表示
print(f"成功: {result.success}")
print(f"出力: {result.output}")
```

---

## 🔧 設定オプション

### 実行モード

```python
# WSLモード（Windows推奨）
config.execution_mode = "wsl"
config.wsl_distribution = "Ubuntu-24.04"
config.claude_command = "~/.local/bin/claude"

# Windowsネイティブモード（git-bash必要）
config.execution_mode = "windows"
config.windows_claude_path = "claude"
config.git_bash_path = r"C:\Program Files\Git\bin\bash.exe"

# Linuxネイティブモード
config.execution_mode = "linux"
config.claude_command = "claude"
```

### ログ設定

```python
logger = StructuredLogger(
    name="app_name",
    log_dir=Path("logs"),
    enable_console=True,   # コンソール出力
    enable_file=True       # ファイル出力
)
```

---

## 📊 テスト一覧

### 基本テスト

```bash
# シンプルなWorker起動テスト (WSL)
python tests/test_simple_worker_wsl.py

# Orchestrator-Worker対話テスト
python tests/test_orchestrator_worker_interaction.py
```

### 認証テスト

```bash
# トークン設定ヘルパー
python setup_claude_token.py
```

---

## 🐛 トラブルシューティング

### 問題1: `Invalid API key`

**原因:** トークンが設定されていない

**解決:**
```bash
python setup_claude_token.py
```

### 問題2: `bash: line 1: D:\...: No such file or directory`

**原因:** WindowsパスがWSLパスに変換されていない

**解決:** WorkerManagerは自動的にパス変換します。`execution_mode = "wsl"` を確認してください。

### 問題3: `claude: command not found`

**原因:** PATHにClaude CLIが含まれていない

**解決:**
```bash
# ~/.bashrc に追加
export PATH="$HOME/.local/bin:$PATH"
source ~/.bashrc
```

---

## 📚 詳細ドキュメント

- [Claude CLI セットアップガイド](docs/CLAUDE_CLI_SETUP.md) - 詳細なインストール手順
- [アーキテクチャ](ARCHITECTURE.md) - システム設計
- [開発ガイド](AI_DEVELOPMENT_GUIDE.md) - 開発者向け情報

---

## 🎯 次のステップ

1. ✅ Claude CLI インストール完了
2. ✅ トークン設定完了
3. ✅ テスト実行成功

**次に試すこと:**

- [Recursive Orchestration](orchestrator/recursive/README.md) - MainAI ⇄ MonitorAI システム
- [Advanced Features](docs/) - 高度な機能

---

**最終更新:** 2025-10-22
**バージョン:** v11.0
