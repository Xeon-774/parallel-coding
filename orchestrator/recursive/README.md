# Recursive Orchestration (v11.0)

**MainAI ⇄ MonitorAI 相互監視システム - pexpectベース**

Claude CodeインスタンスがClaude Codeインスタンスを起動・監視する再帰的なオーケストレーションシステム。

---

## 🎯 コア・アイデア

```
User (あなた)
 ↓ Claude Code起動
MainAI (= このClaude Codeセッション)
 ↓ pexpect.spawn (Bashツール)
MonitorAI (別Claude Code)

MainAI
 ↓ pexpect.spawn (Bashツール)
WorkerAI × N (別Claude Code)
```

**全てClaude Codeインスタンス、既存技術100%再利用**

---

## ✨ 主要機能

- ✅ **ハイブリッド通信**: リアルタイム対話（pexpect） + ファイル共有
- ✅ **相互監視**: MainAI ⇄ MonitorAI
- ✅ **自己修復**: TIMEOUT/EOF検出 → 自動再起動
- ✅ **設定管理**: Wait時間をハードコードしない
- ✅ **100%再利用**: 既存のWorkerManager技術

---

## 🚀 クイックスタート

### 方法1: ヘルパースクリプト使用

**Linux/Mac:**
```bash
./orchestrator/recursive/start_main_ai.sh
```

**Windows:**
```cmd
orchestrator\recursive\start_main_ai.bat
```

### 方法2: 手動起動

```bash
# 1. ワークスペース作成
mkdir -p workspace/main_ai

# 2. Claude Code起動
claude_code --workspace workspace/main_ai

# 3. プロンプト読み込み
# orchestrator/recursive/prompts/main_ai_system.md の内容を送信

# 4. タスク実行
"3つのシンプルなPythonアプリを作成してください。
 MonitorAIで監視しながら実行してください。"
```

---

## 📂 ファイル構成

```
orchestrator/recursive/
├── __init__.py              # モジュール初期化
├── config.py                # 設定管理（Wait時間など）
├── README.md                # このファイル
├── start_main_ai.sh         # 起動ヘルパー (Linux/Mac)
├── start_main_ai.bat        # 起動ヘルパー (Windows)
└── prompts/
    ├── main_ai_system.md    # MainAIシステムプロンプト
    └── monitor_ai_system.md # MonitorAIシステムプロンプト
```

---

## ⚙️ 設定

### デフォルト設定

```python
from orchestrator.recursive.config import DEFAULT_CONFIG

# MonitorAI設定
monitor_heartbeat_interval = 10  # HEARTBEAT間隔（秒）
monitor_timeout = 30             # タイムアウト（秒）
monitor_restart_delay = 5        # 再起動待機（秒）

# 状態監視
status_check_interval = 5        # チェック間隔（秒）
worker_timeout = 60              # Workerタイムアウト（秒）

# リトライ
max_monitor_restart_attempts = 3
max_worker_retry_attempts = 3
```

### 環境変数で変更

```bash
# Wait時間を変更
export RECURSIVE_ORCH_MONITOR_TIMEOUT=60
export RECURSIVE_ORCH_WORKER_TIMEOUT=120

# デバッグモード
export RECURSIVE_ORCH_DEBUG_MODE=true

# Claude Code起動
claude_code --workspace workspace/main_ai
```

### 設定確認

```bash
python orchestrator/recursive/config.py
```

---

## 🔄 実行フロー

### Phase 1: MonitorAI起動

MainAIがBashツールでpexpectを使用してMonitorAIを起動:

```python
import pexpect
monitor = pexpect.spawn('claude_code', ['--workspace', 'workspace/monitor_ai'])
monitor.sendline(monitor_prompt)
```

### Phase 2: MonitorAI監視スレッド

MainAIが別スレッドでMonitorAI出力を監視:

```python
# リアルタイム監視
index = monitor_session.expect([
    r'ERROR DETECTED',
    r'SUGGEST RECOVERY',
    r'HEARTBEAT',
    pexpect.TIMEOUT,  # 30秒
    pexpect.EOF       # MonitorAI終了
])
```

### Phase 3: WorkerAI起動・実行

MainAIが既存のWorkerManagerでWorkerAIを起動:

```python
from orchestrator.core.worker_manager import WorkerManager
worker_manager.spawn_worker(worker_id, task)
```

### Phase 4: 監視・回復

MonitorAIがエラーを検出してMainAIに通知:

```
MonitorAI: "ERROR DETECTED: worker_1 timeout"
MonitorAI: "SUGGEST RECOVERY: retry worker_1"

MainAI: expect('SUGGEST RECOVERY') で検出
MainAI: 回復策を適用
```

---

## 📊 通信方式

### リアルタイム対話（主要）

| 方向 | 方式 | 用途 |
|------|------|------|
| MonitorAI → MainAI | pexpect.expect() | エラー通知、回復提案、HEARTBEAT |
| MainAI → MonitorAI | pexpect.sendline() | 状態更新、指示 |

### ファイル共有（補助・監査証跡）

| ファイル | 用途 |
|---------|------|
| workspace/main_ai/status.json | MainAI状態 |
| workspace/main_ai/workers/*.json | WorkerAI状態 |
| workspace/monitor_ai/recovery_log.jsonl | 回復履歴 |

---

## 🧪 テスト

### 設定テスト

```bash
python orchestrator/recursive/config.py
```

### 動作確認（簡易）

```bash
# MainAI起動
claude_code --workspace workspace/main_ai

# プロンプト送信後、以下を確認:
# ✓ MonitorAI起動
# ✓ HEARTBEAT受信
# ✓ WorkerAI起動
# ✓ エラー検出・回復
```

---

## 🐛 トラブルシューティング

### MonitorAI起動失敗

**症状**: MonitorAI起動タイムアウト

**確認**:
```bash
# Claude Codeがインストールされているか
which claude_code

# ワークスペースが作成されているか
ls -la workspace/monitor_ai
```

**解決**:
- `monitor_startup_timeout`を増やす
- Claude Code再インストール

### HEARTBEAT受信できない

**症状**: MonitorAI応答なし

**確認**:
```bash
# MonitorAIが実行されているか
ps aux | grep claude_code

# 出力ファイルを確認
tail -f workspace/monitor_ai/output.log
```

**解決**:
- `monitor_heartbeat_interval`を短縮
- MonitorAI再起動

### WorkerAIタイムアウト

**症状**: WorkerAIが60秒以上応答なし

**確認**:
```bash
# Worker状態ファイル
cat workspace/main_ai/workers/worker_1.json
```

**解決**:
- `worker_timeout`を増やす
- MonitorAIの回復提案に従う

---

## 📚 参考資料

- [RECURSIVE_ORCHESTRATION_QUICK_START.md](../../RECURSIVE_ORCHESTRATION_QUICK_START.md) - 完全な設計ドキュメント
- [docs/architecture/DUAL_ORCHESTRATOR_DESIGN.md](../../docs/architecture/DUAL_ORCHESTRATOR_DESIGN.md) - アーキテクチャ詳細

---

## 🎯 Next Steps

- [x] Week 1: 基本構造 + リアルタイム通信
- [ ] Week 2: 監視機能 + エラー検出
- [ ] Week 3: 回復機能 + Self-Healing
- [ ] Week 4: 統合 + テスト

---

**Status**: ✅ Week 1 Phase 1 完了
**Version**: v11.0.0
**Updated**: 2025-10-22
