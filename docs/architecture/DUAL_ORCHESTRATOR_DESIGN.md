# Dual Orchestrator Design (v11.0)

**MainAI ⇄ MonitorAI 相互監視アーキテクチャ（pexpectベース）**

Status: 🚧 Design Phase
Version: v11.0
Created: 2025-10-22
Updated: 2025-10-22
Author: Claude Code + User

---

## 📋 目次

1. [エグゼクティブサマリー](#エグゼクティブサマリー)
2. [コア・アイデア](#コア・アイデア)
3. [アーキテクチャ概要](#アーキテクチャ概要)
4. [実装詳細](#実装詳細)
5. [通信プロトコル](#通信プロトコル)
6. [シーケンス図](#シーケンス図)
7. [実装計画](#実装計画)
8. [未解決課題](#未解決課題)

---

## エグゼクティブサマリー

### 🎯 コア・アイデア

**「Orchestrator ⇄ Worker の関係を再帰的に適用」**

```
User ──pexpect──► MainAI ──pexpect──► MonitorAI
                     │
                     └──pexpect──► WorkerAI × N
```

- **全てClaude Codeインスタンス（対話型AI）**
- **全てpexpect/wexpectで制御**
- **既存のWorkerManager技術を完全再利用**

### 主要コンポーネント

- **MainAI**: Claude Codeインスタンス（タスク実行・ワーカー管理）
- **MonitorAI**: Claude Codeインスタンス（MainAI監視・回復提案）
- **WorkerAI**: Claude Codeインスタンス（実作業実行）

### キー機能

- ✅ 既存インフラ100%再利用
- ✅ 相互監視・自動回復
- ✅ パターンベース通信
- ✅ 完全な監査証跡
- ✅ 擬似端末制御による安全性

---

## コア・アイデア

### 既存の成功パターンを再利用

**v10.0で既に動作している構造:**

```
Orchestrator (Python)
    │
    │ pexpect/wexpect
    │ ├─ spawn
    │ ├─ sendline
    │ ├─ expect (pattern matching)
    │ └─ confirmation handling
    ↓
WorkerAI (Claude Code)
    - 対話型AI
    - 確認パターン送信
    - Orchestratorが検出・応答
```

**v11.0の革新: これを再帰的に適用**

```
User (or Launcher)
    │
    │ pexpect/wexpect ← 同じ技術
    ↓
MainAI (Claude Code)
    │
    │ pexpect/wexpect ← 同じ技術
    ├─► MonitorAI (Claude Code)
    │
    └─► WorkerAI (Claude Code) × N
```

### なぜこれが素晴らしいか

1. **既存コードをそのまま使える**
   - `WorkerManager` → `MonitorManager`として再利用
   - `confirmation_patterns` → MonitorAI用パターン追加
   - `AISafetyJudge` → そのまま適用可能

2. **Claude Codeの特性を最大活用**
   - 全てが対話型AI（プログラムではない）
   - pexpect制御による安全な相互作用
   - パターンマッチングによる構造化通信

3. **拡張性**
   - さらに階層を追加可能（SupervisorAI, AuditorAIなど）
   - 任意の深さまで再帰可能

---

## アーキテクチャ概要

### システム全体図

```
┌──────────────────────────────────────────────────────────┐
│ Launcher (Python Script or User Terminal)               │
│ - MainAIをpexpect/wexpectで起動                          │
└─────────────────────┬────────────────────────────────────┘
                      │ pexpect.spawn('claude_code')
                      ↓
┌──────────────────────────────────────────────────────────┐
│ 【MainAI】= Claude Code Instance (対話型AI)              │
│ Workspace: workspace/main_ai/                            │
│                                                           │
│ 役割:                                                     │
│  - MonitorAIを起動（pexpect/wexpect）                    │
│  - タスク分析・分割                                       │
│  - WorkerAI起動・管理                                     │
│  - MonitorAIと対話                                        │
│  - 結果統合                                              │
└─────────────────────┬────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │ pexpect.spawn             │ pexpect.spawn × N
        ↓                           ↓
┌──────────────────────┐   ┌──────────────────────┐
│【MonitorAI】         │   │【WorkerAI × N】      │
│= Claude Code         │   │= Claude Code         │
│Workspace: monitor_ai/│   │Workspace: worker_N/  │
│                      │   │                      │
│ 役割:                │   │ 役割:                │
│  - MainAI監視        │   │  - タスク実行        │
│  - エラー検出        │   │  - MainAIと対話      │
│  - 回復策提案        │   │                      │
│  - パフォーマンス監視│   │                      │
└──────────────────────┘   └──────────────────────┘
```

### レイヤー構成

```
┌──────────────────────────────────────┐
│  Application Layer                   │  ← ユーザーインターフェース
│  - CLI / Web UI / API                │
└──────────────────┬───────────────────┘
                   │
┌──────────────────▼───────────────────┐
│  Dual Orchestration Layer            │  ← 今回の実装対象
│  - DualOrchestratorManager          │
│  - MainAI / MonitorAI               │
│  - MutualProtocol                   │
└──────────────────┬───────────────────┘
                   │
┌──────────────────▼───────────────────┐
│  Core Services Layer (v10.0)         │  ← 既存コンポーネント
│  - WorkerManager                    │
│  - AISafetyJudge                    │
│  - StreamMonitor                    │
│  - ResultIntegrator                 │
└──────────────────┬───────────────────┘
                   │
┌──────────────────▼───────────────────┐
│  Infrastructure Layer                │
│  - StructuredLogger                 │
│  - Resilience (CircuitBreaker, etc) │
│  - Observability (Metrics, Health)  │
└──────────────────────────────────────┘
```

---

## コンポーネント詳細

### 1. DualOrchestratorManager

**責務**: MainAIとMonitorAIのライフサイクル管理

```python
class DualOrchestratorManager:
    """
    相互監視する2つのAIを統合管理

    Features:
    - 両AIの起動・停止
    - 共有状態の初期化
    - 通信チャネルのセットアップ
    - グレースフルシャットダウン
    """

    def __init__(
        self,
        config: OrchestratorConfig,
        logger: ILogger,
        enable_monitor: bool = True
    ):
        """
        初期化

        Args:
            config: オーケストレーター設定
            logger: ロガー
            enable_monitor: MonitorAI有効化（デバッグ時にfalse可能）
        """
        self.config = config
        self.logger = logger
        self.enable_monitor = enable_monitor

        # 共有状態
        self.shared_state = SharedState()

        # 通信チャネル
        self.main_to_monitor = Queue()
        self.monitor_to_main = Queue()

        # AIインスタンス
        self.main_ai = MainOrchestratorAI(
            config=config,
            logger=logger,
            state=self.shared_state,
            inbox=self.monitor_to_main,
            outbox=self.main_to_monitor
        )

        if enable_monitor:
            self.monitor_ai = MonitorDaemonAI(
                config=config,
                logger=logger,
                state=self.shared_state,
                inbox=self.main_to_monitor,
                outbox=self.monitor_to_main
            )

    def run(self, user_request: str) -> Optional[str]:
        """
        両AIを起動してタスク実行

        Args:
            user_request: ユーザーリクエスト

        Returns:
            統合結果、失敗時はNone
        """
        try:
            # MonitorAIをバックグラウンドで起動
            if self.enable_monitor:
                monitor_thread = threading.Thread(
                    target=self.monitor_ai.run,
                    daemon=True,
                    name="MonitorAI"
                )
                monitor_thread.start()
                self.logger.info("MonitorAI started")

            # MainAIでタスク実行（メインスレッド）
            result = self.main_ai.execute(user_request)

            return result

        except KeyboardInterrupt:
            self.logger.info("Shutting down gracefully...")
            self.shutdown()
            return None

        except Exception as e:
            self.logger.error(f"Critical error: {e}")
            self.shutdown()
            raise

    def shutdown(self):
        """グレースフルシャットダウン"""
        # MainAIに停止シグナル
        self.shared_state.main_status = 'shutting_down'

        # MonitorAIに停止シグナル
        self.monitor_to_main.put({'type': 'shutdown'})

        # クリーンアップ
        self.logger.info("Dual orchestrator shutdown complete")
```

### 2. MainOrchestratorAI

**責務**: タスク実行・ワーカー管理

```python
class MainOrchestratorAI:
    """
    メイン実行AI

    Responsibilities:
    - タスク分析・分割
    - ワーカーAIの起動・管理
    - 結果収集・統合
    - リソース管理
    - MonitorAIへの報告
    """

    def __init__(
        self,
        config: OrchestratorConfig,
        logger: ILogger,
        state: SharedState,
        inbox: Queue,
        outbox: Queue
    ):
        self.config = config
        self.logger = logger
        self.state = state  # 共有状態
        self.inbox = inbox  # MonitorAIからのメッセージ
        self.outbox = outbox  # MonitorAIへのメッセージ

        # コアサービス（v10.0）
        self.worker_manager = WorkerManager(config, logger)
        self.task_analyzer = TaskAnalyzerService(config, logger)
        self.result_integrator = ResultIntegrator(config, logger)

    def execute(self, user_request: str) -> Optional[str]:
        """
        タスク実行（MonitorAI監視下）

        Args:
            user_request: ユーザーリクエスト

        Returns:
            統合結果
        """
        self.state.main_status = 'running'
        self.logger.info("MainAI: Starting execution")

        try:
            # STEP 1: タスク分析・分割
            self.state.main_status = 'analyzing'
            tasks = self.task_analyzer.analyze_and_split(user_request)

            # MonitorAIに通知
            self.outbox.put({
                'type': 'task_analysis_complete',
                'task_count': len(tasks)
            })

            # STEP 2: ワーカー起動
            self.state.main_status = 'spawning_workers'
            for i, task in enumerate(tasks, 1):
                worker_id = f"worker_{i}"

                # MonitorAIからの指示をチェック
                self._check_monitor_commands()

                # ワーカー起動
                session = self.worker_manager.spawn_worker(worker_id, task)
                self.state.workers[worker_id] = {
                    'status': 'running',
                    'task': task,
                    'session': session
                }

            # STEP 3: 実行・監視
            self.state.main_status = 'executing'
            results = []

            for worker_id in self.state.workers.keys():
                # MonitorAIからの指示をチェック
                self._check_monitor_commands()

                # ワーカー実行
                result = self.worker_manager.run_interactive_session(worker_id)
                results.append(result)

                # ステータス更新
                self.state.workers[worker_id]['status'] = 'completed'
                self.state.workers[worker_id]['result'] = result

                # エラー時はMonitorAIに報告
                if not result.success:
                    self.outbox.put({
                        'type': 'worker_error',
                        'worker_id': worker_id,
                        'error': result.error_message
                    })

            # STEP 4: 結果統合
            self.state.main_status = 'integrating'
            final_result = self.result_integrator.integrate(results)

            self.state.main_status = 'completed'
            self.logger.info("MainAI: Execution completed")

            return final_result

        except Exception as e:
            self.state.main_status = 'error'
            self.state.errors.append({
                'timestamp': time.time(),
                'error': str(e),
                'traceback': traceback.format_exc()
            })

            # MonitorAIに緊急報告
            self.outbox.put({
                'type': 'critical_error',
                'error': str(e)
            })

            self.logger.error(f"MainAI: Critical error: {e}")
            return None

    def _check_monitor_commands(self):
        """MonitorAIからのコマンドをチェック"""
        while not self.inbox.empty():
            message = self.inbox.get_nowait()
            self._handle_monitor_message(message)

    def _handle_monitor_message(self, message: Dict[str, Any]):
        """MonitorAIからのメッセージを処理"""
        msg_type = message.get('type')

        if msg_type == 'recovery_suggestion':
            # エラー回復策を適用
            self.logger.info(f"MainAI: Applying recovery: {message['strategy']}")
            self._apply_recovery(message['strategy'])

        elif msg_type == 'optimization_hint':
            # 最適化提案を適用
            self.logger.info(f"MainAI: Applying optimization: {message['hint']}")
            self._apply_optimization(message['hint'])

        elif msg_type == 'pause':
            # 一時停止
            self.logger.warning("MainAI: Paused by MonitorAI")
            self.state.main_status = 'paused'
            # 再開待ち...

        elif msg_type == 'shutdown':
            # 緊急停止
            self.logger.critical("MainAI: Emergency shutdown by MonitorAI")
            raise KeyboardInterrupt("Emergency shutdown")

    def _apply_recovery(self, strategy: Dict[str, Any]):
        """回復戦略を適用"""
        # TODO: 実装
        pass

    def _apply_optimization(self, hint: Dict[str, Any]):
        """最適化を適用"""
        # TODO: 実装
        pass
```

### 3. MonitorDaemonAI

**責務**: 監視・エラー回復・最適化

```python
class MonitorDaemonAI:
    """
    監視・回復AI（デーモン）

    Responsibilities:
    - MainAI健全性監視
    - エラー検出・診断
    - 回復戦略決定・実行
    - パフォーマンス監視
    - 最適化提案
    """

    def __init__(
        self,
        config: OrchestratorConfig,
        logger: ILogger,
        state: SharedState,
        inbox: Queue,
        outbox: Queue
    ):
        self.config = config
        self.logger = logger
        self.state = state  # MainAIの状態を監視
        self.inbox = inbox  # MainAIからのメッセージ
        self.outbox = outbox  # MainAIへのコマンド

        # 監視設定
        self.check_interval = 5  # 5秒ごとに監視
        self.heartbeat_timeout = 30  # 30秒応答なしで警告

        # メトリクス
        self.last_heartbeat = time.time()
        self.error_history = []
        self.recovery_history = []

    def run(self):
        """監視ループ（バックグラウンドスレッド）"""
        self.logger.info("MonitorAI: Started")

        while True:
            try:
                # MainAIのステータスをチェック
                status = self.state.main_status

                if status == 'shutting_down':
                    self.logger.info("MonitorAI: Shutdown signal received")
                    break

                # 健全性チェック
                self._check_health()

                # エラーチェック
                self._check_errors()

                # パフォーマンスチェック
                self._check_performance()

                # MainAIからのメッセージ処理
                self._process_main_messages()

                # 待機
                time.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"MonitorAI: Error in monitoring loop: {e}")
                time.sleep(self.check_interval)

        self.logger.info("MonitorAI: Stopped")

    def _check_health(self):
        """健全性チェック"""
        status = self.state.main_status

        # ステータスチェック
        if status == 'error':
            self.logger.warning("MonitorAI: MainAI in error state")
            self._trigger_recovery()

        elif status == 'frozen':
            self.logger.critical("MonitorAI: MainAI frozen!")
            # 緊急対応...

        # ハートビートチェック
        time_since_heartbeat = time.time() - self.last_heartbeat
        if time_since_heartbeat > self.heartbeat_timeout:
            self.logger.warning(
                f"MonitorAI: No heartbeat for {time_since_heartbeat:.0f}s"
            )

    def _check_errors(self):
        """エラーチェック"""
        errors = self.state.errors

        if not errors:
            return

        # 新しいエラーを処理
        new_errors = errors[len(self.error_history):]

        for error in new_errors:
            self.logger.error(
                f"MonitorAI: Error detected: {error['error']}"
            )

            # エラー診断
            diagnosis = self._diagnose_error(error)

            # 回復戦略決定
            recovery = self._decide_recovery_strategy(diagnosis)

            # MainAIに送信
            self.outbox.put({
                'type': 'recovery_suggestion',
                'strategy': recovery,
                'diagnosis': diagnosis
            })

            # 履歴記録
            self.error_history.append(error)
            self.recovery_history.append({
                'error': error,
                'recovery': recovery,
                'timestamp': time.time()
            })

    def _check_performance(self):
        """パフォーマンスチェック"""
        metrics = self.state.metrics

        if not metrics:
            return

        # CPU使用率チェック
        if metrics.get('cpu_percent', 0) > 90:
            self.logger.warning("MonitorAI: High CPU usage detected")
            self.outbox.put({
                'type': 'optimization_hint',
                'hint': {
                    'issue': 'high_cpu',
                    'suggestion': 'reduce_parallelism'
                }
            })

        # メモリ使用率チェック
        if metrics.get('memory_percent', 0) > 85:
            self.logger.warning("MonitorAI: High memory usage detected")
            self.outbox.put({
                'type': 'optimization_hint',
                'hint': {
                    'issue': 'high_memory',
                    'suggestion': 'enable_streaming'
                }
            })

    def _process_main_messages(self):
        """MainAIからのメッセージを処理"""
        while not self.inbox.empty():
            message = self.inbox.get_nowait()
            msg_type = message.get('type')

            if msg_type == 'task_analysis_complete':
                self.logger.info(
                    f"MonitorAI: {message['task_count']} tasks analyzed"
                )
                self.last_heartbeat = time.time()

            elif msg_type == 'worker_error':
                self.logger.warning(
                    f"MonitorAI: Worker {message['worker_id']} error: "
                    f"{message['error']}"
                )

            elif msg_type == 'critical_error':
                self.logger.critical(
                    f"MonitorAI: Critical error in MainAI: "
                    f"{message['error']}"
                )
                self._trigger_emergency_recovery()

    def _diagnose_error(self, error: Dict[str, Any]) -> Dict[str, Any]:
        """エラー診断"""
        # TODO: より高度な診断ロジック
        return {
            'error_type': 'worker_failure',
            'severity': 'medium',
            'recoverable': True
        }

    def _decide_recovery_strategy(
        self,
        diagnosis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """回復戦略決定"""
        # TODO: より高度な戦略決定
        return {
            'action': 'retry_worker',
            'max_retries': 3,
            'backoff': 'exponential'
        }

    def _trigger_recovery(self):
        """回復処理をトリガー"""
        # TODO: 実装
        pass

    def _trigger_emergency_recovery(self):
        """緊急回復処理"""
        # TODO: 実装
        pass
```

### 4. SharedState

**責務**: スレッド間共有状態

```python
class SharedState:
    """
    MainAIとMonitorAI間で共有される状態

    Thread-Safe:
    - threading.Lock で保護
    - 読み取り/書き込みをアトミックに
    """

    def __init__(self):
        self._lock = threading.Lock()

        # MainAIのステータス
        self._main_status: str = 'idle'

        # ワーカー情報
        self._workers: Dict[str, Dict[str, Any]] = {}

        # メトリクス
        self._metrics: Dict[str, Any] = {}

        # エラー
        self._errors: List[Dict[str, Any]] = []

    # Thread-safe properties
    @property
    def main_status(self) -> str:
        with self._lock:
            return self._main_status

    @main_status.setter
    def main_status(self, value: str):
        with self._lock:
            self._main_status = value

    @property
    def workers(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return dict(self._workers)  # コピーを返す

    def update_worker(self, worker_id: str, data: Dict[str, Any]):
        with self._lock:
            if worker_id not in self._workers:
                self._workers[worker_id] = {}
            self._workers[worker_id].update(data)

    @property
    def metrics(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._metrics)

    def update_metrics(self, metrics: Dict[str, Any]):
        with self._lock:
            self._metrics.update(metrics)

    @property
    def errors(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._errors)  # コピーを返す

    def add_error(self, error: Dict[str, Any]):
        with self._lock:
            self._errors.append(error)
```

---

## 通信プロトコル

### メッセージ形式

**基本構造:**
```python
{
    "type": str,           # メッセージタイプ
    "timestamp": float,    # タイムスタンプ
    "sender": str,         # 送信者 ("main" or "monitor")
    "data": Dict[str, Any] # ペイロード
}
```

### MainAI → MonitorAI

| Type | Description | Payload |
|------|-------------|---------|
| `heartbeat` | 生存確認 | `{}` |
| `task_analysis_complete` | タスク分析完了 | `{task_count: int}` |
| `worker_spawned` | ワーカー起動 | `{worker_id: str}` |
| `worker_error` | ワーカーエラー | `{worker_id: str, error: str}` |
| `critical_error` | 致命的エラー | `{error: str, traceback: str}` |
| `status_update` | ステータス更新 | `{status: str}` |

### MonitorAI → MainAI

| Type | Description | Payload |
|------|-------------|---------|
| `recovery_suggestion` | 回復策提案 | `{strategy: Dict, diagnosis: Dict}` |
| `optimization_hint` | 最適化提案 | `{hint: Dict}` |
| `pause` | 一時停止 | `{}` |
| `resume` | 再開 | `{}` |
| `shutdown` | シャットダウン | `{reason: str}` |

---

## データ構造

### WorkerInfo
```python
@dataclass
class WorkerInfo:
    worker_id: str
    status: str  # 'running', 'completed', 'failed', 'paused'
    task: Dict[str, Any]
    session: WorkerSession
    started_at: float
    completed_at: Optional[float] = None
    result: Optional[TaskResult] = None
    error: Optional[str] = None
```

### ErrorRecord
```python
@dataclass
class ErrorRecord:
    timestamp: float
    error_type: str
    error_message: str
    traceback: str
    worker_id: Optional[str] = None
    severity: str = 'medium'  # 'low', 'medium', 'high', 'critical'
    recoverable: bool = True
```

### RecoveryStrategy
```python
@dataclass
class RecoveryStrategy:
    action: str  # 'retry_worker', 'restart_worker', 'skip_task', etc.
    parameters: Dict[str, Any]
    estimated_time: float
    success_probability: float
```

### PerformanceMetrics
```python
@dataclass
class PerformanceMetrics:
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    active_workers: int
    completed_tasks: int
    failed_tasks: int
    avg_task_duration: float
```

---

## エラーハンドリング

### エラー分類

**Level 1: Worker Error（ワーカーレベル）**
- 影響範囲: 単一ワーカー
- 対応: MonitorAIが自動回復を試行
- 例: ワーカーAIのタイムアウト、実行エラー

**Level 2: MainAI Error（オーケストレーターレベル）**
- 影響範囲: タスク実行全体
- 対応: MonitorAIが診断・回復策提案
- 例: タスク分析失敗、リソース枯渇

**Level 3: System Error（システムレベル）**
- 影響範囲: システム全体
- 対応: グレースフルシャットダウン、ユーザー通知
- 例: メモリ不足、ディスク満杯

### 回復戦略

**1. Retry（リトライ）**
```python
strategy = {
    'action': 'retry_worker',
    'max_retries': 3,
    'backoff': 'exponential',  # 1s, 2s, 4s
    'timeout': 120
}
```

**2. Restart（再起動）**
```python
strategy = {
    'action': 'restart_worker',
    'cleanup': True,  # ワークスペースクリーンアップ
    'timeout': 60
}
```

**3. Skip（スキップ）**
```python
strategy = {
    'action': 'skip_task',
    'mark_as': 'failed',
    'continue_others': True
}
```

**4. Reassign（再割り当て）**
```python
strategy = {
    'action': 'reassign_task',
    'target_worker': 'worker_X',
    'priority': 'high'
}
```

---

## シーケンス図

### 正常フロー

```
User          MainAI              MonitorAI           WorkerAI
 |              |                     |                   |
 |--request---->|                     |                   |
 |              |                     |                   |
 |              |--task_analyzed----->|                   |
 |              |                     |                   |
 |              |----spawn----------->|                   |
 |              |                     |                   |
 |              |                     |<--monitor---------|
 |              |                     |                   |
 |              |<---ok---------------|                   |
 |              |                     |                   |
 |              |--execute-------------------------------->|
 |              |                     |                   |
 |              |<--result---------------------------------|
 |              |                     |                   |
 |              |--completed--------->|                   |
 |<--result-----|                     |                   |
```

### エラー回復フロー

```
MainAI              MonitorAI           WorkerAI
  |                     |                   |
  |----execute-------------------------------->|
  |                     |                   |
  |<--ERROR-------------------------------------|
  |                     |                   |
  |--worker_error------>|                   |
  |                     |                   |
  |                     |--diagnose---------|
  |                     |                   |
  |<--recovery_suggest--|                   |
  |                     |                   |
  |--apply_recovery---->|                   |
  |                     |                   |
  |----retry_execute-------------------------->|
  |                     |                   |
  |<--SUCCESS----------------------------------|
  |                     |                   |
  |--completed--------->|                   |
```

---

## 実装計画

### Phase 1: 基本構造（Week 1-2）

**目標**: DualOrchestratorManagerの基本実装

**タスク**:
- [ ] SharedState実装
- [ ] 通信チャネル（Queue）セットアップ
- [ ] DualOrchestratorManager骨組み
- [ ] MainAI骨組み
- [ ] MonitorAI骨組み
- [ ] 基本的な起動・停止フロー

**成果物**:
```
orchestrator/dual/
├── __init__.py
├── dual_manager.py
├── main_ai.py
├── monitor_ai.py
└── shared_state.py
```

### Phase 2: 通信プロトコル（Week 3）

**目標**: MainAI ⇄ MonitorAI 通信確立

**タスク**:
- [ ] メッセージ形式定義
- [ ] メッセージ送受信実装
- [ ] ハートビート機構
- [ ] 基本的なコマンド処理

**成果物**:
```
orchestrator/dual/
├── protocol.py          # メッセージ定義
└── message_handler.py   # メッセージ処理
```

### Phase 3: 監視機能（Week 4-5）

**目標**: MonitorAIの監視機能実装

**タスク**:
- [ ] 健全性チェック
- [ ] エラー検出
- [ ] パフォーマンス監視
- [ ] メトリクス収集

**成果物**:
```
orchestrator/dual/
├── health_checker.py
├── error_detector.py
└── performance_monitor.py
```

### Phase 4: 回復機能（Week 6-7）

**目標**: エラー診断・回復実装

**タスク**:
- [ ] エラー診断ロジック
- [ ] 回復戦略決定
- [ ] 回復実行
- [ ] リトライ機構

**成果物**:
```
orchestrator/dual/
├── error_diagnosis.py
├── recovery_strategy.py
└── recovery_executor.py
```

### Phase 5: テスト・ドキュメント（Week 8）

**目標**: 品質保証

**タスク**:
- [ ] ユニットテスト
- [ ] 統合テスト
- [ ] ドキュメント整備
- [ ] 使用例作成

**成果物**:
```
tests/dual/
├── test_dual_manager.py
├── test_main_ai.py
├── test_monitor_ai.py
└── test_recovery.py

docs/
└── DUAL_ORCHESTRATOR_GUIDE.md
```

---

## テスト戦略

### ユニットテスト

**SharedState**:
```python
def test_shared_state_thread_safety():
    """スレッドセーフ性をテスト"""
    state = SharedState()

    def writer():
        for i in range(1000):
            state.main_status = f'status_{i}'

    threads = [threading.Thread(target=writer) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # データ破損がないことを確認
    assert state.main_status.startswith('status_')
```

**MainAI**:
```python
def test_main_ai_message_handling():
    """MonitorAIからのメッセージを正しく処理"""
    # TODO
    pass
```

**MonitorAI**:
```python
def test_monitor_ai_error_detection():
    """エラー検出が正しく動作"""
    # TODO
    pass
```

### 統合テスト

**シナリオ1: 正常実行**
```python
def test_dual_orchestrator_normal_execution():
    """エラーなしで完了"""
    manager = DualOrchestratorManager(config, logger)
    result = manager.run("Create 3 simple apps")

    assert result is not None
    assert "completed" in result
```

**シナリオ2: エラー回復**
```python
def test_dual_orchestrator_error_recovery():
    """エラー発生時に自動回復"""
    # ワーカーがエラーを出すようにモック
    # MonitorAIが回復することを確認
    pass
```

**シナリオ3: パフォーマンス監視**
```python
def test_monitor_ai_performance_optimization():
    """高負荷時に最適化提案"""
    # 高CPU使用率をシミュレート
    # MonitorAIが最適化提案を送ることを確認
    pass
```

---

## 未解決課題

### 1. MonitorAI自身の監視

**課題**: MonitorAIがハングした場合の対応

**候補解決策**:
- Option A: Watchdog timer（別スレッド）
- Option B: MainAIがMonitorAIを監視（相互監視）
- Option C: 外部プロセスで監視

**決定**: 未定（要議論）

### 2. 回復戦略の優先順位

**課題**: 複数の回復策がある場合の選択基準

**候補解決策**:
- Option A: 成功確率ベース
- Option B: コストベース（時間・リソース）
- Option C: ML/AI による学習

**決定**: Phase 4で決定

### 3. スケーラビリティ

**課題**: 大量ワーカー時のMonitorAI負荷

**候補解決策**:
- Option A: サンプリング監視
- Option B: 階層的監視（グループ単位）
- Option C: 分散MonitorAI

**決定**: v12.0で検討

### 4. 永続化

**課題**: エラー履歴・回復履歴の保存

**候補解決策**:
- Option A: SQLite
- Option B: JSON files
- Option C: StructuredLoggerに統合

**決定**: Option C（既存インフラ活用）

---

## 付録

### 用語集

| 用語 | 説明 |
|------|------|
| MainAI | タスク実行を担当するオーケストレーターAI |
| MonitorAI | 監視・回復を担当するデーモンAI |
| SharedState | スレッド間で共有される状態オブジェクト |
| Recovery Strategy | エラー発生時の回復手順 |
| Heartbeat | 生存確認のための定期的なシグナル |

### 参考資料

- [v10.0 Architecture](./ARCHITECTURE.md)
- [Worker Manager Design](../orchestrator/core/worker_manager.py)
- [AI Safety Judge](../orchestrator/core/ai_safety_judge.py)
- [Resilience Patterns](../orchestrator/core/resilience.py)

---

**Document Status**: 🚧 Draft - Ready for Review
**Next Steps**: レビュー → 実装開始
**Contact**: Claude Code + User
