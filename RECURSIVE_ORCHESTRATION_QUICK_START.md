# 🚀 Recursive Orchestration Quick Start

**MainAI ⇄ MonitorAI 相互監視システム（pexpectベース）**

Version: v11.0
Status: 🎯 Ready for Implementation
Date: 2025-10-22

---

## 🎯 Core Idea

**「既存のOrchestrator → WorkerAI の技術を再帰的に適用」**

```
User
 ↓ (pexpect/wexpect)
MainAI (Claude Code)
 ↓ (pexpect/wexpect) ← Same tech!
MonitorAI (Claude Code)

MainAI (Claude Code)
 ↓ (pexpect/wexpect) ← Same tech!
WorkerAI × N (Claude Code)
```

**全てClaude Codeインスタンス、全てpexpect制御、既存技術100%再利用**

---

## ✅ Why This Works

### 1. 既存のインフラを完全再利用

**既に動作している:**
```python
# orchestrator/core/worker_manager.py
class WorkerManager:
    def spawn_worker(self, worker_id, task):
        # pexpect/wexpectでClaude Code起動
        session = pexpect.spawn('claude_code', [...])
        session.sendline(task['prompt'])
        # pattern matching
        session.expect(confirmation_patterns)
```

**新しい:**
```python
# MonitorAI起動も全く同じ方式！
monitor_session = worker_manager.spawn_worker(
    worker_id="monitor_ai",
    task={
        "prompt": "あなたはMonitorAIです。MainAIを監視してください..."
    }
)
```

### 2. Confirmation Patternsを拡張するだけ

**既存（WorkerAI用）:**
```python
confirmation_patterns = [
    (r"write\s+(?:to\s+)?(?:file\s+)?['\"]([^'\"]+)['\"]", FILE_WRITE),
    (r"execute\s+command:?\s*['\"]([^'\"]+)['\"]", COMMAND_EXEC),
    # ... 11 patterns
]
```

**追加（MonitorAI用）:**
```python
monitor_patterns = [
    (r"ERROR DETECTED: (.+)", ERROR_REPORT),
    (r"SUGGEST RECOVERY: (.+)", RECOVERY_SUGGESTION),
    (r"WARNING: (.+)", WARNING),
    (r"STATUS CHECK", HEALTH_CHECK),
]
```

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────┐
│ User/Launcher (Python)                           │
│ pexpect.spawn('claude_code')                     │
└────────────────┬─────────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────────┐
│ MainAI (Claude Code Instance)                      │
│ workspace/main_ai/                                 │
│                                                    │
│ System Prompt:                                     │
│ "あなたはMainAIです。以下を実行してください:         │
│  1. MonitorAIを起動（Bashツール + pexpect）        │
│  2. タスク分析・分割                               │
│  3. WorkerAI起動                                   │
│  4. MonitorAIからの提案に従う"                     │
│                                                    │
│ Tools Used:                                        │
│ - Bash (MonitorAI/WorkerAI起動)                   │
│ - Read/Write (状態ファイル)                        │
│ - 既存Worker management logic                     │
└────────────────┬───────────────────────────────────┘
                 │
       ┌─────────┴───────────┐
       │                     │
       ↓                     ↓
┌──────────────┐    ┌────────────────┐
│ MonitorAI    │    │ WorkerAI × N   │
│ (Claude Code)│    │ (Claude Code)  │
│              │    │                │
│ Prompt:      │    │ Prompt:        │
│ "MainAIを    │    │ "[Task]を      │
│  監視..."    │    │  実行..."      │
└──────────────┘    └────────────────┘
```

---

## 📝 Implementation Example

### Step 1: Launcher

```python
# launcher.py
import pexpect

def launch_main_ai(user_request):
    # MainAI起動
    main_ai = pexpect.spawn(
        'claude_code',
        ['--workspace', 'workspace/main_ai'],
        encoding='utf-8'
    )

    # 初期プロンプト
    main_ai.sendline(f"""
あなたはMainAIです。以下のタスクを処理してください:

{user_request}

処理手順:
1. MonitorAIを起動（Bashツールでpexpect）
2. タスク分析・分割
3. WorkerAI起動
4. MonitorAIの提案に従う
5. 結果統合
""")

    # 出力監視
    while True:
        line = main_ai.readline()
        print(f"[MainAI] {line}")

        if "TASK COMPLETED" in line:
            break

if __name__ == '__main__':
    launch_main_ai("Create 3 simple Python apps")
```

### Step 2: MainAI System Prompt

```markdown
# MainAI Instructions

あなたはMainAIです。オーケストレーションを担当します。

## Step 1: MonitorAI起動

Bashツールを使用してMonitorAIを起動してください:

\`\`\`python
import pexpect
import json

monitor = pexpect.spawn('claude_code', ['--workspace', 'workspace/monitor_ai'])

monitor_prompt = """
あなたはMonitorAIです。MainAIを監視してください。

監視対象:
- workspace/main_ai/status.json
- workspace/main_ai/workers/*.json
- workspace/main_ai/output.log

エラー検出時:
- "ERROR DETECTED: [詳細]" と出力

回復策提案時:
- "SUGGEST RECOVERY: [提案]" と出力

定期チェック: 5秒ごと
"""

monitor.sendline(monitor_prompt)

# セッション情報保存
with open('workspace/main_ai/monitor_session.json', 'w') as f:
    json.dump({'pid': monitor.pid, 'started': True}, f)
\`\`\`

## Step 2: タスク分析

（既存のTaskSplitter使用）

## Step 3: WorkerAI起動

（既存のWorkerManager使用）

## Step 4: MonitorAI監視

MonitorAIの出力を定期的にチェック:

\`\`\`python
# workspace/monitor_ai/output.log を読み取り
with open('workspace/monitor_ai/output.log', 'r') as f:
    for line in f:
        if 'ERROR DETECTED:' in line:
            # エラー処理
            pass
        elif 'SUGGEST RECOVERY:' in line:
            # 回復策適用
            pass
\`\`\`

## 完了条件

全WorkerAI完了 + MonitorAI "NO ISSUES" → "TASK COMPLETED"出力
```

### Step 3: MonitorAI System Prompt

```markdown
# MonitorAI Instructions

あなたはMonitorAIです。MainAIを監視します。

## 監視ループ

\`\`\`python
import time
import json
import os

while True:
    # 1. MainAI状態確認
    if os.path.exists('workspace/main_ai/status.json'):
        with open('workspace/main_ai/status.json') as f:
            status = json.load(f)

        if status.get('status') == 'error':
            print(f"ERROR DETECTED: {status['error']}")
            print(f"SUGGEST RECOVERY: restart_worker")

    # 2. Worker状態確認
    for worker_file in glob('workspace/main_ai/workers/*.json'):
        with open(worker_file) as f:
            worker = json.load(f)

        # タイムアウトチェック
        if time.time() - worker['last_update'] > 60:
            print(f"ERROR DETECTED: Worker {worker['id']} timeout")
            print(f"SUGGEST RECOVERY: retry_worker {worker['id']}")

    # 3. 完了チェック
    if all_workers_completed():
        print("NO ISSUES DETECTED")
        break

    time.sleep(5)
\`\`\`

## 出力フォーマット

- エラー: `ERROR DETECTED: [詳細]`
- 回復策: `SUGGEST RECOVERY: [提案]`
- 警告: `WARNING: [警告]`
- 正常: `NO ISSUES DETECTED`
```

---

## 🔄 Communication Flow

**ハイブリッド方式: リアルタイム対話（pexpect） + ファイル共有**

### 1. リアルタイム対話（メイン通信）

#### MainAI → MonitorAI

```python
# MainAI側（pexpectセッションに送信）
monitor_session.sendline("STATUS: worker_1 spawned")
monitor_session.sendline("WORKER_ERROR: worker_1 - TimeoutError")
monitor_session.sendline("TASK_COMPLETED: worker_1")
```

#### MonitorAI → MainAI（リアルタイム検出）

```python
# MainAI側（MonitorAI出力をリアルタイム監視）
import pexpect

# MonitorAI出力をexpectでパターンマッチング
index = monitor_session.expect([
    r'ERROR DETECTED: (.+)',          # パターン0
    r'SUGGEST RECOVERY: (.+)',        # パターン1
    r'WARNING: (.+)',                 # パターン2
    r'NO ISSUES DETECTED',            # パターン3
    r'HEARTBEAT',                     # パターン4
    pexpect.TIMEOUT,                  # パターン5 (30秒)
    pexpect.EOF                       # パターン6 (MonitorAI終了)
], timeout=30)

if index == 0:  # ERROR DETECTED
    error_msg = monitor_session.match.group(1).decode()
    print(f"[MainAI] MonitorAI detected error: {error_msg}")
    # エラー処理...

elif index == 1:  # SUGGEST RECOVERY
    recovery = monitor_session.match.group(1).decode()
    print(f"[MainAI] Applying recovery: {recovery}")
    apply_recovery(recovery)

elif index == 2:  # WARNING
    warning = monitor_session.match.group(1).decode()
    print(f"[MainAI] Warning from MonitorAI: {warning}")

elif index == 3:  # NO ISSUES
    print("[MainAI] MonitorAI reports: All OK")

elif index == 4:  # HEARTBEAT
    print("[MainAI] MonitorAI is alive")
    # ハートビート受信 → 次のexpectへ

elif index == 5:  # TIMEOUT
    print("[MainAI] MonitorAI not responding!")
    restart_monitor_ai()

elif index == 6:  # EOF
    print("[MainAI] MonitorAI crashed!")
    restart_monitor_ai()
```

### 2. ファイル共有（永続化・監査証跡）

#### 用途
- **状態の永続化**: 再起動時に復元
- **監査証跡**: すべてのイベントを記録
- **非同期イベント**: MonitorAIが非同期でファイル監視

#### MainAI → MonitorAI（状態ファイル）

```python
# MainAI側: 状態を書き込み（MonitorAIが監視）
status = {
    "timestamp": time.time(),
    "status": "running",
    "workers": {
        "worker_1": {
            "status": "running",
            "last_update": time.time()
        }
    }
}

with open('workspace/main_ai/status.json', 'w') as f:
    json.dump(status, f)

# MonitorAI側: 定期的に読み取り
with open('workspace/main_ai/status.json') as f:
    status = json.load(f)

# タイムアウトチェック
if time.time() - status['workers']['worker_1']['last_update'] > 60:
    # リアルタイム対話で通知
    print("ERROR DETECTED: worker_1 timeout (no update for 60s)")
```

#### MonitorAI → MainAI（回復履歴）

```python
# MonitorAI側: 回復提案を記録
recovery = {
    "timestamp": time.time(),
    "action": "retry_worker",
    "worker_id": "worker_1",
    "params": {"timeout": 180}
}

# リアルタイム通知（メイン）
print(f"SUGGEST RECOVERY: {json.dumps(recovery)}")

# ファイルにも記録（監査証跡）
with open('workspace/monitor_ai/recovery_log.jsonl', 'a') as f:
    f.write(json.dumps(recovery) + '\n')
```

### 通信方式の使い分け

| 通信目的 | 方式 | 理由 |
|---------|------|------|
| MonitorAI → MainAI エラー通知 | **リアルタイム対話**（pexpect.expect） | 即座に対応が必要 |
| MonitorAI → MainAI 回復提案 | **リアルタイム対話**（pexpect.expect） | 即座に適用が必要 |
| MainAI → MonitorAI 状態報告 | **両方**（sendline + ファイル） | リアルタイム通知 + 永続化 |
| MonitorAI健全性チェック | **リアルタイム対話**（HEARTBEAT） | MainAIがリアルタイム監視 |
| 監査証跡 | **ファイル共有** | 後から確認・分析 |
| 状態復元 | **ファイル共有** | 再起動時に復元 |

---

## 🔍 MonitorAI自身の監視（重要！）

**MainAIがMonitorAIをリアルタイム監視 → 既存のWorkerAI監視と同じ方式**

### MainAI側の実装

```python
# MainAI内でMonitorAI監視スレッドを起動
import threading

def monitor_monitor_ai_thread(monitor_session):
    """MonitorAIをリアルタイム監視（別スレッド）"""

    while True:
        try:
            # MonitorAI出力をリアルタイム監視
            index = monitor_session.expect([
                r'ERROR DETECTED: (.+)',      # 0: エラー報告
                r'SUGGEST RECOVERY: (.+)',    # 1: 回復提案
                r'WARNING: (.+)',             # 2: 警告
                r'NO ISSUES DETECTED',        # 3: 正常
                r'HEARTBEAT',                 # 4: 生存確認
                pexpect.TIMEOUT,              # 5: 30秒応答なし
                pexpect.EOF                   # 6: MonitorAI終了
            ], timeout=30)

            if index == 0:  # ERROR DETECTED
                error = monitor_session.match.group(1).decode()
                print(f"[MainAI] ⚠️  MonitorAI報告: {error}")
                # エラー処理...

            elif index == 1:  # SUGGEST RECOVERY
                recovery = monitor_session.match.group(1).decode()
                print(f"[MainAI] 💡 回復策適用: {recovery}")
                apply_recovery_suggestion(recovery)

            elif index == 2:  # WARNING
                warning = monitor_session.match.group(1).decode()
                print(f"[MainAI] ⚡ 警告: {warning}")

            elif index == 3:  # NO ISSUES
                print(f"[MainAI] ✅ MonitorAI: 問題なし")

            elif index == 4:  # HEARTBEAT
                print(f"[MainAI] 💓 MonitorAI生存確認")
                last_heartbeat = time.time()

            elif index == 5:  # TIMEOUT
                print(f"[MainAI] 🚨 MonitorAIが30秒応答なし！再起動します...")
                restart_monitor_ai()
                break

            elif index == 6:  # EOF
                print(f"[MainAI] 💀 MonitorAIが終了しました！再起動します...")
                restart_monitor_ai()
                break

        except Exception as e:
            print(f"[MainAI] MonitorAI監視エラー: {e}")
            time.sleep(5)

# MonitorAI起動後、監視スレッドを開始
monitor_thread = threading.Thread(
    target=monitor_monitor_ai_thread,
    args=(monitor_session,),
    daemon=True
)
monitor_thread.start()
```

### MonitorAI側の実装

```python
# MonitorAI側: 定期的にHEARTBEAT送信
import time

def monitoring_loop():
    """監視ループ"""
    last_heartbeat = time.time()

    while True:
        # 1. MainAI状態確認
        check_main_ai_status()

        # 2. Worker状態確認
        check_workers_status()

        # 3. HEARTBEAT送信（10秒ごと）
        if time.time() - last_heartbeat > 10:
            print("HEARTBEAT")
            last_heartbeat = time.time()

        # 4. 待機
        time.sleep(5)
```

### MonitorAI再起動ロジック

```python
def restart_monitor_ai():
    """MonitorAIを再起動"""

    print("[MainAI] MonitorAIを再起動しています...")

    # 古いセッションをクリーンアップ
    try:
        monitor_session.close(force=True)
    except:
        pass

    # 新しいMonitorAI起動
    monitor_session = pexpect.spawn(
        'claude_code',
        ['--workspace', 'workspace/monitor_ai'],
        encoding='utf-8'
    )

    # 初期プロンプト送信
    monitor_prompt = """
あなたはMonitorAIです。MainAIを監視してください。
[詳細プロンプト...]
"""
    monitor_session.sendline(monitor_prompt)

    # 監視スレッド再起動
    monitor_thread = threading.Thread(
        target=monitor_monitor_ai_thread,
        args=(monitor_session,),
        daemon=True
    )
    monitor_thread.start()

    print("[MainAI] MonitorAI再起動完了")
```

### 監視フロー図

```
MainAI
  │
  ├─ [Main Thread] タスク実行
  │   ├─ WorkerAI spawn
  │   ├─ WorkerAI monitoring
  │   └─ Result integration
  │
  └─ [Monitor Thread] MonitorAI監視 ★
      │
      ├─ monitor_session.expect([
      │     'ERROR DETECTED',
      │     'SUGGEST RECOVERY',
      │     'HEARTBEAT',
      │     TIMEOUT,     ← 30秒応答なし
      │     EOF          ← MonitorAI終了
      │  ])
      │
      ├─ ERROR → 処理
      ├─ RECOVERY → 適用
      ├─ TIMEOUT → 再起動 ★
      └─ EOF → 再起動 ★
```

### 相互監視の完成形

```
┌──────────────────────────────────────┐
│ MainAI                               │
│                                      │
│ [Main Thread]                        │
│  ├─ タスク実行                        │
│  ├─ WorkerAI管理                     │
│  └─ MonitorAIに状態報告               │
│                                      │
│ [Monitor Thread] ★                   │
│  └─ MonitorAI出力を監視               │
│      ├─ HEARTBEAT確認                │
│      ├─ ERROR/RECOVERY検出           │
│      └─ TIMEOUT/EOF → 再起動         │
└────────────┬─────────────────────────┘
             │ リアルタイム対話
             ↓
┌──────────────────────────────────────┐
│ MonitorAI                            │
│                                      │
│ [Monitoring Loop]                    │
│  ├─ MainAI状態ファイル監視            │
│  ├─ Worker状態ファイル監視            │
│  ├─ エラー検出                        │
│  ├─ 回復策決定                        │
│  ├─ ERROR DETECTED出力 ★             │
│  ├─ SUGGEST RECOVERY出力 ★           │
│  └─ HEARTBEAT出力（10秒ごと）★       │
└──────────────────────────────────────┘
```

---

## 📊 Data Structures

### status.json (MainAI)

```json
{
  "status": "running",
  "phase": "executing_workers",
  "workers": {
    "worker_1": {
      "status": "running",
      "started_at": 1729598400.0,
      "last_update": 1729598450.0
    }
  },
  "monitor_ai": {
    "pid": 12345,
    "status": "running"
  }
}
```

### events.jsonl (MainAI → MonitorAI)

```jsonl
{"ts": 1729598400.0, "type": "worker_spawned", "id": "worker_1"}
{"ts": 1729598450.0, "type": "worker_error", "id": "worker_1", "error": "TimeoutError"}
```

### recovery_suggestions.jsonl (MonitorAI → MainAI)

```jsonl
{"ts": 1729598455.0, "action": "retry_worker", "id": "worker_1", "timeout": 180}
```

---

## 🎬 Sequence Diagram

### 正常フロー（リアルタイム対話 + ファイル共有）

```
User    Launcher   MainAI                MonitorAI       WorkerAI
 |         |         |                       |              |
 |--req--->|         |                       |              |
 |         |--spawn->|                       |              |
 |         |   (pexpect.spawn)               |              |
 |         |         |                       |              |
 |         |         |--spawn--------------->|              |
 |         |         |   (pexpect.spawn)     |              |
 |         |         |                       |              |
 |         |         |--sendline("START")--->|              |
 |         |         |   [リアルタイム対話]   |              |
 |         |         |                       |              |
 |         |         |<--expect("HEARTBEAT")-|              |
 |         |         |   [10秒ごと]          |              |
 |         |         |                       |              |
 |         |         |--spawn----------------------------------->|
 |         |         |   (pexpect.spawn)                    |
 |         |         |                       |              |
 |         |         |--write(status.json)-->|              |
 |         |         |   [ファイル共有]       |              |
 |         |         |                       |              |
 |         |         |                       |--read(status.json)
 |         |         |                       |              |
 |         |         |<--expect("NO ISSUES")-|              |
 |         |         |   [リアルタイム対話]   |              |
 |         |         |                       |              |
 |         |         |<--result--------------------------------|
 |         |         |                       |              |
 |         |         |--sendline("DONE")---->|              |
 |         |         |                       |              |
 |         |         |<--expect("OK")--------|              |
 |         |<--done--|                       |              |
 |<--done--|         |                       |              |
```

### エラー回復フロー（リアルタイム）

```
MainAI              MonitorAI           WorkerAI
  |                     |                   |
  |--spawn----------------------------------->|
  |                     |                   |
  |--write(status.json)->|                   |
  |                     |                   |
  |                     |--read(status.json)|
  |                     |                   |
  |                     |<--read timeout----|
  |                     |                   |
  |<--expect("ERROR")---|                   |
  |   "worker_1 timeout"|                   |
  |   [リアルタイム検出] |                   |
  |                     |                   |
  |<--expect("RECOVERY")|                   |
  |   "retry worker_1"  |                   |
  |   [リアルタイム受信] |                   |
  |                     |                   |
  |--apply_recovery---->|                   |
  |                     |                   |
  |--retry_spawn----------------------------->|
  |                     |                   |
  |<--success---------------------------------|
  |                     |                   |
  |--sendline("OK")---->|                   |
```

### MonitorAI監視フロー（重要！）

```
MainAI                    MonitorAI
  |                          |
  |--spawn------------------>|
  |   (pexpect)              |
  |                          |
  |--start_monitor_thread--->|
  |   [別スレッドで監視開始]   |
  |                          |
  |                          |--HEARTBEAT (10秒ごと)
  |<--expect("HEARTBEAT")----|
  |   [リアルタイム検出]       |
  |                          |
  |   [Main Thread]          |   [Monitor Loop]
  |--task_execution          |--check_status
  |--worker_spawn            |--check_workers
  |                          |--HEARTBEAT
  |<--expect("HEARTBEAT")----|
  |                          |
  |                          |--ERROR DETECTED
  |<--expect("ERROR")--------|
  |   [即座に検出]            |
  |                          |
  |                          |--SUGGEST RECOVERY
  |<--expect("RECOVERY")-----|
  |   [即座に適用]            |
  |                          |
  |                          X (MonitorAIクラッシュ)
  |<--expect(EOF)------------|
  |   [即座に検出]            |
  |                          |
  |--restart_monitor-------->|
  |   [自動再起動]            |
  |                          |
  |<--expect("HEARTBEAT")----|
  |   [復旧確認]              |
```

---

## 📦 Implementation Plan

### Week 1: Basic Structure + Real-time Communication

**目標**: MainAI ⇄ MonitorAI リアルタイム対話確立

- [ ] **Launcher実装**
  - `orchestrator/recursive/launcher.py`
  - pexpect/wexpectでMainAI起動

- [ ] **MainAI初期プロンプト作成**
  - `orchestrator/recursive/prompts/main_ai_prompt.md`
  - MonitorAI起動ロジック（Bashツール + pexpect）
  - MonitorAI監視スレッド起動ロジック

- [ ] **MonitorAI初期プロンプト作成**
  - `orchestrator/recursive/prompts/monitor_ai_prompt.md`
  - 監視ループロジック
  - HEARTBEAT送信ロジック

- [ ] **リアルタイム対話確認**
  - MainAI → MonitorAI: `sendline()`
  - MonitorAI → MainAI: `expect(patterns)`
  - HEARTBEAT機構確認
  - TIMEOUT/EOF検出確認

**成果物**:
```python
# 動作確認
python orchestrator/recursive/launcher.py "Test request"
# → MainAI起動
# → MonitorAI起動
# → HEARTBEAT検出
# → 相互通信確認
```

### Week 2: Monitoring + Error Detection

**目標**: MonitorAIによる監視・エラー検出

- [ ] **MonitorAI監視ループ**
  - 状態ファイル監視（ファイル共有）
  - Worker状態確認
  - エラー検出パターン

- [ ] **リアルタイムエラー通知**
  - `ERROR DETECTED: [詳細]` 出力
  - MainAIがexpectで即座に検出

- [ ] **MainAI監視スレッド**
  - MonitorAI出力をリアルタイム監視
  - エラー検出時の処理
  - MonitorAI再起動ロジック

**成果物**:
```python
# テスト: 意図的にWorkerエラーを発生
# → MonitorAIがエラー検出
# → ERROR DETECTED出力
# → MainAIがリアルタイム検出
# → エラー処理実行
```

### Week 3: Recovery + Self-Healing

**目標**: 自動エラー回復・MonitorAI自己修復

- [ ] **回復戦略定義**
  - Retry, Restart, Skip, Reassign
  - `orchestrator/recursive/recovery_strategies.py`

- [ ] **MainAI回復実行**
  - MonitorAIからの`SUGGEST RECOVERY`を検出
  - 回復策を即座に適用
  - 回復履歴記録

- [ ] **MonitorAI診断ロジック**
  - エラー分類
  - 回復策決定
  - `SUGGEST RECOVERY: [提案]` 出力

- [ ] **MonitorAI自己修復**
  - TIMEOUT検出 → 自動再起動
  - EOF検出 → 自動再起動
  - 再起動後のHEARTBEAT確認

**成果物**:
```python
# テスト1: WorkerエラーからMainAIが回復
# テスト2: MonitorAIクラッシュからMainAIが回復
```

### Week 4: Integration + Testing

**目標**: エンドツーエンドテスト・ドキュメント整備

- [ ] **統合テスト**
  - 正常フロー
  - エラー回復フロー
  - MonitorAI再起動フロー
  - 複数Workerシナリオ

- [ ] **パフォーマンステスト**
  - リアルタイム対話のレイテンシ
  - HEARTBEAT間隔調整
  - ファイル共有のオーバーヘッド

- [ ] **ドキュメント整備**
  - 実装ガイド
  - トラブルシューティング
  - ベストプラクティス

- [ ] **デモ実装**
  - `examples/recursive_demo.py`
  - tmux 3ペイン表示（User, MainAI, MonitorAI）

**成果物**:
- 動作するデモ
- 完全なドキュメント
- テストカバレッジ 80%+

---

## ✨ Key Advantages

### 1. **100% Code Reuse**
   - `WorkerManager` → そのまま使える
   - `confirmation_patterns` → 拡張するだけ
   - `AISafetyJudge` → 適用可能

### 2. **All Claude Code Instances**
   - 全て対話型AI（Pythonコードではない）
   - 柔軟な対話・推論能力
   - pexpect制御で安全

### 3. **Hybrid Communication** ★
   - **リアルタイム対話**: 即座のエラー検出・回復（pexpect.expect）
   - **ファイル共有**: 永続化・監査証跡・状態復元
   - 両方の利点を活用

### 4. **Self-Healing** ★
   - MonitorAI → MainAI: エラー検出・回復提案（リアルタイム）
   - MainAI → MonitorAI: 健全性監視・自動再起動（リアルタイム）
   - 相互監視による高可用性

### 5. **Extensibility**
   - SupervisorAI, AuditorAI等を追加可能
   - 任意の深さまで再帰可能

---

## 🎯 Design Summary

### 通信方式のハイブリッド設計 ★

| 要素 | リアルタイム対話<br>(pexpect) | ファイル共有 | 理由 |
|------|---------------------------|------------|------|
| **MonitorAI → MainAI<br>エラー通知** | ✅ 主要 | ✅ 補助 | 即座に対応が必要 |
| **MonitorAI → MainAI<br>回復提案** | ✅ 主要 | ✅ 補助 | 即座に適用が必要 |
| **MonitorAI健全性チェック** | ✅ HEARTBEAT | - | 30秒タイムアウト検出 |
| **MainAI → MonitorAI<br>状態報告** | ✅ sendline | ✅ status.json | リアルタイム + 永続化 |
| **監査証跡** | - | ✅ *.jsonl | 後から確認・分析 |
| **状態復元** | - | ✅ status.json | 再起動時に復元 |

### 相互監視の完成形 ★

```
MainAI監視MonitorAI          MonitorAI監視MainAI
─────────────────────────────────────────────────
expect('HEARTBEAT')      →   状態ファイル監視
expect('ERROR')          →   Worker状態監視
expect('RECOVERY')       →   タイムアウト検出
expect(TIMEOUT)          →   エラーパターン検出
expect(EOF)              →
→ 自動再起動             →   → リアルタイム通知
```

---

## 🚧 Resolved Questions ✅

### 1. **通信方式**
✅ **解決**: ハイブリッド方式
- リアルタイム対話（pexpect.expect）: メイン通信
- ファイル共有: 永続化・監査証跡

### 2. **MonitorAI自身のエラー**
✅ **解決**: MainAIがリアルタイム監視
- HEARTBEAT: 10秒ごと
- TIMEOUT: 30秒応答なし → 自動再起動
- EOF: MonitorAI終了 → 自動再起動

### 3. **通信遅延**
✅ **解決**: リアルタイム対話で即座に検出
- pexpect.expect(): パターンマッチング（ミリ秒オーダー）
- ファイルポーリング: 5秒間隔（補助）

### 4. **デバッグ**
✅ **解決**: tmux + 構造化ログ
- tmux 3ペイン: User, MainAI, MonitorAI
- JSON Lines形式ログ: 後から分析

---

## 🚀 Next Steps

### Option A: すぐに実装開始

**Week 1 (Phase 1) から実装:**

```bash
# 1. ディレクトリ作成
mkdir -p orchestrator/recursive/prompts

# 2. Launcher実装
vim orchestrator/recursive/launcher.py

# 3. プロンプト作成
vim orchestrator/recursive/prompts/main_ai_prompt.md
vim orchestrator/recursive/prompts/monitor_ai_prompt.md

# 4. テスト実行
python orchestrator/recursive/launcher.py "Create 3 apps"
```

### Option B: 設計レビュー

フィードバックをお待ちしています：
1. ハイブリッド通信方式で問題ないか？
2. HEARTBEAT間隔（10秒）は適切か？
3. TIMEOUT（30秒）は適切か？
4. 優先的に実装すべき機能は？

---

**Status**: 🎯 Ready for Implementation with Hybrid Communication
**Version**: v11.0 (pexpect-based + hybrid communication)
**Updated**: 2025-10-22
**Next**: Week 1 Phase 1実装開始
