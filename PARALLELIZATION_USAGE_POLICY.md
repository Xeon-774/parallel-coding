# Parallel AI Coding - 並列化利用方針 (Parallelization Usage Policy)

**Version**: 1.0.0
**Last Updated**: 2025-10-24
**Status**: ✅ Production Ready
**Target**: すべてのユーザー（人間・AI）

---

## 🎯 Executive Summary

この文書は、並列AIコーディングツールの**適切な使用方針**を定義します。

**基本原則**:
1. ✅ **自発的タスク分析** - すべての状況でタスク分割可能性を自動評価
2. ✅ **安全優先** - 競合リスクがある場合は適切な管理手法を適用
3. ✅ **効率最適化** - Worker間の処理時間を可能な限り均等化
4. ⚠️ **慎重な判断** - 危険な分割や不必要な分割は回避

---

## 📋 Table of Contents

1. [基本方針](#基本方針)
2. [タスク分割判断基準](#タスク分割判断基準)
3. [並列化決定アルゴリズム](#並列化決定アルゴリズム)
4. [Worker割り当て戦略](#worker割り当て戦略)
5. [安全性管理](#安全性管理)
6. [パフォーマンス最適化](#パフォーマンス最適化)
7. [禁止事項](#禁止事項)
8. [ベストプラクティス](#ベストプラクティス)

---

## 🔰 基本方針

### 原則1: 自発的タスク分析 (Proactive Task Analysis)

**すべてのタスクに対して、自動的に並列化可能性を評価する**

```python
# 擬似コード
def analyze_task(task: Task) -> ParallelizationDecision:
    """
    すべてのタスクを自動分析

    Returns:
        ParallelizationDecision: 並列化判断結果
    """
    # Step 1: タスク複雑度分析
    complexity = assess_complexity(task)

    # Step 2: 依存関係分析
    dependencies = analyze_dependencies(task)

    # Step 3: ファイル競合リスク評価
    conflict_risk = assess_conflict_risk(task)

    # Step 4: 並列化価値判定
    parallelization_value = calculate_value(
        complexity, dependencies, conflict_risk
    )

    # Step 5: 決定
    if parallelization_value > THRESHOLD:
        return ParallelizationDecision.PARALLEL
    else:
        return ParallelizationDecision.SEQUENTIAL
```

### 原則2: 安全優先 (Safety First)

**競合リスクがある場合は適切な管理手法を自動適用**

```
競合リスク評価 → 管理手法選択:

🟢 LOW RISK (0-20%)
   → Subprocess モード (最速)
   → Git管理不要

🟡 MEDIUM RISK (20-50%)
   → Git Worktree モード (ファイル分離)
   → 自動マージ戦略

🔴 HIGH RISK (50-80%)
   → Git Worktree + 手動レビュー
   → Sequential fallback option

🔴 CRITICAL RISK (80-100%)
   → Sequential実行のみ
   → 並列化中止
```

### 原則3: 効率最適化 (Efficiency Optimization)

**Worker間の処理時間を可能な限り均等化**

```python
# タスク割り当て最適化
def optimize_task_allocation(tasks: List[Task]) -> List[WorkerAssignment]:
    """
    処理時間を均等化するようにタスクを割り当て

    目標: 全Workerの完了時間差 < 20%
    """
    # Step 1: 各タスクの推定時間計算
    estimated_times = [estimate_duration(t) for t in tasks]

    # Step 2: Bin Packing Problem として解く
    # (Longest Processing Time First アルゴリズム)
    assignments = lpt_algorithm(tasks, estimated_times, num_workers)

    # Step 3: 負荷バランス検証
    max_time = max(sum(t for _, t in worker) for worker in assignments)
    min_time = min(sum(t for _, t in worker) for worker in assignments)

    assert (max_time - min_time) / max_time < 0.20, "Load imbalance > 20%"

    return assignments
```

---

## 🧮 タスク分割判断基準

### Decision Matrix: 並列化すべきか？

| 条件 | 並列化 | Sequential | 理由 |
|------|--------|-----------|------|
| **タスク数 = 1** | ❌ | ✅ | 分割の価値なし |
| **タスク数 = 2, 独立** | ✅ | △ | 2倍速の可能性 |
| **タスク数 ≥ 3, 独立** | ✅ | ❌ | 並列化推奨 |
| **強い依存関係あり** | ❌ | ✅ | Sequential必須 |
| **弱い依存関係** | ✅ | △ | DAG解析して並列化 |
| **同一ファイル編集** | ⚠️ | ✅ | Worktree or Sequential |
| **異なるディレクトリ** | ✅ | ❌ | 競合リスク低 |
| **推定時間 < 5分** | ❌ | ✅ | Overhead > Benefit |
| **推定時間 > 30分** | ✅ | ❌ | 並列化で大幅短縮 |
| **CPU使用率 > 80%** | ⚠️ | △ | Worker数制限 |
| **メモリ不足リスク** | ❌ | ✅ | リソース不足 |

### タスク複雑度分類

```python
class TaskComplexity(Enum):
    TRIVIAL = 1        # < 5分, 並列化不要
    SIMPLE = 2         # 5-15分, 並列化検討
    MODERATE = 3       # 15-30分, 並列化推奨
    COMPLEX = 4        # 30-60分, 並列化強く推奨
    VERY_COMPLEX = 5   # > 60分, 必ず並列化
```

**判定ロジック**:

```python
def should_parallelize(task: Task) -> bool:
    """並列化判断"""

    # Rule 1: 複雑度チェック
    if task.complexity <= TaskComplexity.TRIVIAL:
        return False  # 小さすぎる

    # Rule 2: サブタスク数チェック
    if len(task.subtasks) < 2:
        return False  # 分割できない

    # Rule 3: 依存関係チェック
    if has_strong_dependencies(task):
        return False  # Sequential必須

    # Rule 4: ファイル競合チェック
    conflict_risk = assess_file_conflicts(task)
    if conflict_risk > 0.8:  # 80%以上
        return False  # 危険すぎる

    # Rule 5: リソースチェック
    if not has_sufficient_resources(task):
        return False  # リソース不足

    # Rule 6: 価値計算
    value = calculate_parallelization_value(task)
    return value > 0.3  # 30%以上の価値
```

---

## 🔀 並列化決定アルゴリズム

### Complete Decision Flow

```
タスク受信
    ↓
┌─────────────────────────┐
│ Step 1: タスク分析      │
│ - 複雑度評価            │
│ - サブタスク抽出        │
│ - 推定時間計算          │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│ Step 2: 依存関係解析    │
│ - DAG構築               │
│ - 独立タスク群特定      │
│ - Critical Path分析     │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│ Step 3: 競合リスク評価  │
│ - ファイル重複検出      │
│ - Git conflict予測      │
│ - リスクスコア算出      │
└──────────┬──────────────┘
           ↓
     <リスク評価>
           ↓
    ┌──────┴──────┐
    │             │
  HIGH         LOW/MED
    │             │
    ↓             ↓
Sequential    ┌─────────────────┐
実行          │ Step 4: 価値計算│
    │         │ - 時間短縮率    │
    │         │ - Overhead考慮  │
    │         │ - Cost/Benefit  │
    │         └────────┬────────┘
    │                  ↓
    │            <価値判定>
    │                  ↓
    │         ┌────────┴────────┐
    │         │                 │
    │      価値低            価値高
    │         │                 │
    │         ↓                 ↓
    │    Sequential      ┌─────────────────┐
    │    実行            │ Step 5: 並列実行│
    │         │          │ - Worker割当    │
    │         │          │ - 負荷分散      │
    │         │          │ - 監視開始      │
    │         │          └────────┬────────┘
    │         │                   │
    └─────────┴───────────────────┘
                     ↓
                実行開始
```

### 判断基準の数式化

#### 1. 並列化価値スコア (Parallelization Value Score)

```
PVS = (Time_Saved - Overhead) × Success_Rate - Risk_Cost

Where:
  Time_Saved = Sequential_Time - Parallel_Time
  Overhead = Setup_Time + Coordination_Time + Merge_Time
  Success_Rate = 1 - Conflict_Probability
  Risk_Cost = Expected_Conflict_Resolution_Time × Conflict_Probability
```

**判定**:
- `PVS > 0.3` → 並列化実施
- `0 < PVS ≤ 0.3` → ユーザー判断
- `PVS ≤ 0` → Sequential実行

#### 2. 最適Worker数計算

```
Optimal_Workers = min(
    Available_CPU_Cores - 1,
    Independent_Task_Count,
    floor(Total_Estimated_Time / Min_Task_Time),
    Max_Workers_Config
)
```

**制約**:
- CPU cores - 1 (システム予約)
- Independent tasks数以下
- 負荷バランス考慮
- 設定上限遵守

#### 3. ファイル競合リスク評価

```
Conflict_Risk = Σ(File_Overlap_i × Edit_Probability_i) / Total_Files

Where:
  File_Overlap_i = 複数Workerが触るファイルの数
  Edit_Probability_i = ファイルiが編集される確率
```

**リスクレベル**:
- `< 0.2` → 🟢 LOW
- `0.2 - 0.5` → 🟡 MEDIUM
- `0.5 - 0.8` → 🟠 HIGH
- `> 0.8` → 🔴 CRITICAL

---

## 👷 Worker割り当て戦略

### Strategy 1: Load Balancing (負荷分散)

**目標**: 全Workerの完了時間差を最小化

```python
def load_balanced_allocation(tasks: List[Task], num_workers: int) -> List[List[Task]]:
    """
    LPT (Longest Processing Time First) アルゴリズム

    複雑度: O(n log n)
    最適性: 2 - 1/m 近似解 (m = worker数)
    """
    # タスクを推定時間降順にソート
    sorted_tasks = sorted(tasks, key=lambda t: t.estimated_time, reverse=True)

    # 各Workerの現在負荷を追跡
    worker_loads = [0.0] * num_workers
    worker_tasks = [[] for _ in range(num_workers)]

    # 各タスクを最も負荷が軽いWorkerに割り当て
    for task in sorted_tasks:
        min_load_worker = min(range(num_workers), key=lambda i: worker_loads[i])
        worker_tasks[min_load_worker].append(task)
        worker_loads[min_load_worker] += task.estimated_time

    return worker_tasks
```

### Strategy 2: Module-Based Allocation (モジュール別)

**目標**: ファイル競合を最小化

```python
def module_based_allocation(tasks: List[Task]) -> List[List[Task]]:
    """
    同じモジュールのタスクを同じWorkerに割り当て

    利点: ファイル競合リスク最小化
    欠点: 負荷不均衡の可能性
    """
    # タスクをモジュール別にグループ化
    module_groups = defaultdict(list)
    for task in tasks:
        module = extract_module(task)
        module_groups[module].append(task)

    # 各モジュールグループを1 Workerに割り当て
    allocations = []
    for module, module_tasks in module_groups.items():
        allocations.append(module_tasks)

    return allocations
```

### Strategy 3: Dependency-Aware Allocation (依存関係考慮)

**目標**: 依存関係を満たしつつ並列度最大化

```python
def dependency_aware_allocation(tasks: List[Task]) -> List[List[Task]]:
    """
    DAG (Directed Acyclic Graph) に基づく割り当て

    アルゴリズム: Topological Sort + Level-based Grouping
    """
    # Step 1: DAG構築
    dag = build_dependency_graph(tasks)

    # Step 2: Topological Sort
    sorted_tasks = topological_sort(dag)

    # Step 3: レベル分け (同じレベルのタスクは並列実行可能)
    levels = []
    current_level = []
    completed = set()

    for task in sorted_tasks:
        # 依存先が全て完了していればcurrent_levelに追加
        if all(dep in completed for dep in task.dependencies):
            current_level.append(task)
        else:
            # 新しいレベル開始
            if current_level:
                levels.append(current_level)
                completed.update(current_level)
            current_level = [task]

    if current_level:
        levels.append(current_level)

    return levels
```

### Strategy Selection Logic

```python
def select_allocation_strategy(
    tasks: List[Task],
    conflict_risk: float,
    dependency_complexity: float
) -> AllocationStrategy:
    """最適な割り当て戦略を選択"""

    # 依存関係が複雑な場合
    if dependency_complexity > 0.7:
        return AllocationStrategy.DEPENDENCY_AWARE

    # ファイル競合リスクが高い場合
    if conflict_risk > 0.5:
        return AllocationStrategy.MODULE_BASED

    # デフォルト: 負荷分散
    return AllocationStrategy.LOAD_BALANCED
```

---

## 🛡️ 安全性管理

### 1. Git Conflict管理戦略

#### Strategy A: Git Worktree (推奨)

**適用条件**:
- ファイル競合リスク: MEDIUM - HIGH
- タスク推定時間: > 15分
- Git管理されたプロジェクト

**実装**:
```bash
# 各Workerに独立したWorktreeを作成
git worktree add ../workspace/worker_001 -b feature/worker-001
git worktree add ../workspace/worker_002 -b feature/worker-002
git worktree add ../workspace/worker_003 -b feature/worker-003

# Worker完了後にマージ
git checkout master
git merge feature/worker-001
git merge feature/worker-002
git merge feature/worker-003
```

**利点**:
- ✅ ファイルレベルで完全分離
- ✅ 同時編集可能
- ✅ Git履歴保持

**欠点**:
- ⚠️ マージ時にconflict可能性
- ⚠️ Setup overhead (数秒)

#### Strategy B: File Locking

**適用条件**:
- ファイル競合リスク: LOW
- 事前にファイル割り当て明確

**実装**:
```yaml
# file_locks.yml
worker_001:
  - src/module_a/file1.py
  - src/module_a/file2.py

worker_002:
  - src/module_b/file1.py
  - src/module_b/file2.py

worker_003:
  - src/module_c/file1.py
```

**検証**:
```python
def validate_file_locks(workers: List[Worker]) -> bool:
    """ファイルロックの重複チェック"""
    all_files = []
    for worker in workers:
        all_files.extend(worker.assigned_files)

    # 重複チェック
    duplicates = [f for f in all_files if all_files.count(f) > 1]

    if duplicates:
        raise ConflictError(f"File lock violation: {duplicates}")

    return True
```

### 2. Rollback戦略

#### Scenario 1: 単一Worker失敗

```python
def handle_worker_failure(failed_worker: Worker, all_workers: List[Worker]):
    """
    単一Worker失敗時の処理

    戦略:
    1. 失敗Workerの変更を破棄
    2. 他Workerは継続
    3. 失敗タスクを再試行 or Sequential実行
    """
    # Step 1: 失敗Workerのworktree削除
    failed_worker.rollback()

    # Step 2: 他Workerは継続（影響なし）
    continue_execution(all_workers.remove(failed_worker))

    # Step 3: 失敗タスクの再処理判断
    if should_retry(failed_worker.task):
        retry(failed_worker.task, sequential=True)
    else:
        log_failure(failed_worker.task)
```

#### Scenario 2: Cascade失敗（依存関係）

```python
def handle_cascade_failure(
    failed_worker: Worker,
    dependent_workers: List[Worker]
):
    """
    依存関係のあるWorker群の失敗処理

    戦略:
    1. 失敗Workerと依存Workerを全て停止
    2. 全変更をロールバック
    3. Sequential fallback
    """
    # Step 1: 依存Worker全て停止
    for worker in dependent_workers:
        worker.stop()
        worker.rollback()

    # Step 2: Sequential再実行
    tasks = [failed_worker.task] + [w.task for w in dependent_workers]
    execute_sequential(tasks)
```

### 3. Safety Checks

#### Pre-execution Checks

```python
class SafetyValidator:
    """並列実行前の安全性検証"""

    def validate_before_execution(
        self,
        tasks: List[Task],
        workers: List[Worker]
    ) -> ValidationResult:
        """実行前検証"""

        checks = [
            self.check_file_conflicts(),
            self.check_resource_availability(),
            self.check_dependency_satisfaction(),
            self.check_git_status(),
            self.check_workspace_cleanliness(),
        ]

        failed_checks = [c for c in checks if not c.passed]

        if failed_checks:
            return ValidationResult(
                passed=False,
                failures=failed_checks,
                recommendation="Fix issues or use Sequential mode"
            )

        return ValidationResult(passed=True)
```

#### Runtime Monitoring

```python
class RuntimeMonitor:
    """実行中の監視"""

    def monitor_execution(self, workers: List[Worker]):
        """
        リアルタイム監視

        検出項目:
        - ファイル競合の兆候
        - リソース枯渇
        - Worker停止・エラー
        - 予想外のファイルアクセス
        """
        while any(w.is_running() for w in workers):
            # CPU/メモリチェック
            if get_cpu_usage() > 95%:
                self.reduce_worker_count()

            # ファイル競合検出
            if detect_concurrent_file_access():
                self.alert_conflict_risk()

            # Worker健全性チェック
            for worker in workers:
                if worker.is_stuck():
                    self.handle_stuck_worker(worker)

            time.sleep(1)
```

---

## ⚡ パフォーマンス最適化

### 1. Worker数の最適化

#### CPU-based Optimization

```python
def calculate_optimal_workers() -> int:
    """CPUベースの最適Worker数計算"""

    cpu_count = os.cpu_count()
    cpu_usage = psutil.cpu_percent(interval=1)

    # Rule 1: CPU cores - 1 (システム用に1 core残す)
    max_workers_cpu = max(1, cpu_count - 1)

    # Rule 2: 現在のCPU使用率考慮
    if cpu_usage > 70:
        # 既に負荷が高い → Worker数削減
        max_workers_cpu = max(1, max_workers_cpu // 2)

    return max_workers_cpu
```

#### Memory-based Optimization

```python
def calculate_memory_limit(estimated_memory_per_worker: float) -> int:
    """メモリベースのWorker数制限"""

    total_memory = psutil.virtual_memory().total
    available_memory = psutil.virtual_memory().available

    # Rule: 利用可能メモリの80%まで使用
    usable_memory = available_memory * 0.8

    max_workers_memory = int(usable_memory / estimated_memory_per_worker)

    return max(1, max_workers_memory)
```

#### Combined Optimization

```python
def get_optimal_worker_count(
    tasks: List[Task],
    config: Config
) -> int:
    """総合的な最適Worker数決定"""

    # 各制約から最大値計算
    max_cpu = calculate_optimal_workers()
    max_memory = calculate_memory_limit(estimate_memory_per_task(tasks))
    max_config = config.max_workers
    max_tasks = len([t for t in tasks if not t.dependencies])

    # 最も制約が厳しい値を採用
    optimal = min(max_cpu, max_memory, max_config, max_tasks)

    # 最低1 Worker保証
    return max(1, optimal)
```

### 2. Timeout最適化

```python
def calculate_optimal_timeout(task: Task) -> float:
    """タスク特性に基づくTimeout計算"""

    # Base estimate
    base_timeout = task.estimated_time

    # Complexity multiplier
    complexity_multiplier = {
        TaskComplexity.TRIVIAL: 2.0,
        TaskComplexity.SIMPLE: 2.5,
        TaskComplexity.MODERATE: 3.0,
        TaskComplexity.COMPLEX: 4.0,
        TaskComplexity.VERY_COMPLEX: 5.0,
    }[task.complexity]

    # Historical performance adjustment
    historical_factor = get_historical_performance_factor(task.type)

    # Final calculation
    timeout = base_timeout * complexity_multiplier * historical_factor

    # Bounds
    min_timeout = 60  # 最低1分
    max_timeout = 3600  # 最大1時間

    return max(min_timeout, min(timeout, max_timeout))
```

### 3. Overhead削減

#### Worktree Setup Optimization

```bash
# 最適化前: 各Workerで個別setup (遅い)
git worktree add ../worker_001
git worktree add ../worker_002
git worktree add ../worker_003

# 最適化後: 並列setup (速い)
parallel git worktree add ::: ../worker_001 ../worker_002 ../worker_003
```

#### Lazy Initialization

```python
class LazyWorker:
    """遅延初期化Worker"""

    def __init__(self, task: Task):
        self.task = task
        self._workspace = None
        self._process = None

    @property
    def workspace(self):
        """必要になったときだけworktree作成"""
        if self._workspace is None:
            self._workspace = self.create_worktree()
        return self._workspace

    def execute(self):
        """実行開始時に初期化"""
        # Workspace作成とプロセス起動を並列化
        with concurrent.futures.ThreadPoolExecutor() as executor:
            workspace_future = executor.submit(self.create_worktree)
            process_future = executor.submit(self.prepare_process)

            workspace = workspace_future.result()
            process = process_future.result()

        self._workspace = workspace
        self._process = process
```

---

## 🚫 禁止事項

### Absolute Prohibitions (絶対禁止)

#### 1. 危険なファイル操作の並列化

```python
# ❌ 絶対に並列化してはいけない例

# 同一ファイルの同時編集（Worktreeなし）
Worker 1: Edit config.json
Worker 2: Edit config.json  # ❌ Conflict確実

# システムファイルの並列操作
Worker 1: Update /etc/hosts
Worker 2: Update /etc/hosts  # ❌ 危険

# データベース migration の並列実行
Worker 1: Run migration 001
Worker 2: Run migration 002  # ❌ Data corruption risk
```

**理由**: データ破損、予測不可能な動作

#### 2. 強い依存関係の無視

```python
# ❌ 間違った並列化

# Task Bが Task Aの出力に依存
Worker 1: Task A (generate data.json)
Worker 2: Task B (process data.json)  # ❌ Task A完了前に開始

# 正しい方法
Worker 1: Task A → 完了待ち
Worker 1: Task B  # Sequential実行
```

**理由**: Task Bが失敗、正しい結果が得られない

#### 3. リソース制限の無視

```python
# ❌ システムリソースを超える並列化

# CPU: 4 cores, 起動Worker: 16
# → システム全体が停止する可能性

# Memory: 8GB available, Worker x 10 x 1GB/worker
# → OOM Killer発動

# 正しい方法
max_workers = min(cpu_count - 1, available_memory / memory_per_worker)
```

**理由**: システムクラッシュ、全タスク失敗

#### 4. Git履歴の破壊

```python
# ❌ 危険なGit操作の並列実行

Worker 1: git rebase master
Worker 2: git push --force  # ❌ 履歴破壊

Worker 1: git commit --amend
Worker 2: git commit --amend  # ❌ Commit競合
```

**理由**: Git履歴破損、チーム全体に影響

### Discouraged Patterns (非推奨)

#### 1. 過度な細分化

```python
# 🟡 非推奨: Overhead > Benefit

# 5分のタスクを10個に分割
for i in range(10):
    Worker(task_i)  # 各30秒

# Setup overhead: 5秒/worker x 10 = 50秒
# 実行時間: 30秒（並列）
# Total: 80秒 vs Sequential: 5分 (300秒)
# → 並列化価値あり（約4倍速）

# しかし、1分のタスクを10個に分割は？
# 実行時間: 6秒（並列）
# Total: 56秒 vs Sequential: 60秒
# → 並列化価値低い（約1.07倍速のみ）
```

**目安**: タスク1つあたり最低5分以上

#### 2. 不均等な負荷分散

```python
# 🟡 非推奨: 負荷不均衡

Worker 1: Task A (60分)
Worker 2: Task B (5分)
Worker 3: Task C (5分)

# Worker 1完了まで2,3は待機 → 効率悪い

# 改善策
Worker 1: Task A (60分)
Worker 2: Task B (5分) → Task D (25分) → Task E (30分)
Worker 3: Task C (5分) → Task F (55分)
```

**目安**: Worker間の完了時間差 < 20%

#### 3. 過度なWorker数

```python
# 🟡 非推奨: Worker数過多

# CPU: 8 cores
# Workers: 32  # ❌ 4倍のoversubscription

# Context switch overhead増大
# 各Workerの実行速度低下

# 推奨
workers = cpu_count - 1  # 7 workers
```

**目安**: Worker数 ≤ CPU cores - 1

---

## ✅ ベストプラクティス

### 1. 段階的並列化

```python
# Phase 1: 小規模テスト (1-2 workers)
result = execute_parallel(tasks, max_workers=2)
validate_results(result)

# Phase 2: 中規模テスト (4 workers)
result = execute_parallel(tasks, max_workers=4)
validate_results(result)

# Phase 3: Full並列化 (optimal workers)
optimal_workers = calculate_optimal_workers()
result = execute_parallel(tasks, max_workers=optimal_workers)
```

### 2. Dry-run検証

```python
def dry_run_validation(tasks: List[Task]) -> ValidationReport:
    """
    実際に実行せずに検証

    チェック項目:
    - ファイル競合予測
    - リソース要件
    - 依存関係満足性
    - 推定完了時間
    """
    report = ValidationReport()

    # 静的解析
    report.file_conflicts = predict_file_conflicts(tasks)
    report.resource_requirements = estimate_resources(tasks)
    report.dependency_issues = validate_dependencies(tasks)
    report.estimated_time = estimate_completion_time(tasks)

    # 推奨事項
    if report.file_conflicts > 0.5:
        report.recommendation = "Use Git Worktree mode"

    if report.resource_requirements > available_resources():
        report.recommendation = "Reduce worker count"

    return report
```

### 3. 継続的モニタリング

```python
class ContinuousMonitor:
    """実行中の継続的監視"""

    def __init__(self, workers: List[Worker]):
        self.workers = workers
        self.metrics = MetricsCollector()

    def monitor(self):
        """メトリクス収集とアラート"""
        while self.workers_running():
            # 各Worker状態
            for worker in self.workers:
                self.metrics.record({
                    'worker_id': worker.id,
                    'cpu_percent': worker.cpu_usage(),
                    'memory_mb': worker.memory_usage(),
                    'progress': worker.progress(),
                    'output_rate': worker.output_rate(),
                })

            # アラート判定
            if self.detect_anomaly():
                self.send_alert()

            # ダッシュボード更新
            self.update_dashboard()

            time.sleep(5)  # 5秒間隔
```

### 4. Failsafe設計

```python
class FailsafeExecutor:
    """失敗に強い実行器"""

    def execute_with_fallback(self, tasks: List[Task]) -> Result:
        """
        Fallback戦略:
        1. 並列実行試行
        2. 失敗時は Sequential fallback
        3. それでも失敗なら人間にエスカレーション
        """
        try:
            # 並列実行試行
            result = self.execute_parallel(tasks)

            if result.success_rate < 0.75:  # 75%未満の成功率
                raise ParallelExecutionError("Low success rate")

            return result

        except ParallelExecutionError as e:
            # Sequential fallback
            logger.warning(f"Parallel failed: {e}, falling back to sequential")
            return self.execute_sequential(tasks)

        except Exception as e:
            # 人間にエスカレーション
            logger.error(f"All execution failed: {e}")
            return self.escalate_to_human(tasks, error=e)
```

### 5. ドキュメント駆動

```python
class TaskDocumentation:
    """タスク実行の完全ドキュメント化"""

    def document_execution(self, execution: Execution) -> ExecutionReport:
        """
        実行レポート生成

        含む情報:
        - タスク分割ロジック
        - Worker割り当て戦略
        - 実行時間詳細
        - リソース使用状況
        - 発生した問題と対処
        - 学習ポイント
        """
        return ExecutionReport(
            task_splitting=execution.splitting_logic,
            allocation_strategy=execution.allocation_strategy,
            timeline=execution.timeline,
            resources=execution.resource_usage,
            issues=execution.issues,
            lessons_learned=execution.lessons,
            success_rate=execution.success_rate,
            time_saved=execution.sequential_time - execution.parallel_time,
        )
```

---

## 📊 実践例

### Example 1: Manager AI開発 (成功例)

**タスク**: Manager AI Week 2-3実装 (60時間)

**分析**:
```python
# タスク分割
tasks = [
    Task("Claude Monitor", estimated_time=20h, module="integrations/"),
    Task("Supervisor Manager", estimated_time=20h, module="core/supervisor/"),
    Task("Dashboard & API", estimated_time=20h, module="frontend/"),
]

# 依存関係
dependencies = {}  # 完全独立

# ファイル競合リスク
conflict_risk = 0.05  # 🟢 LOW (異なるディレクトリ)

# 並列化価値
value = (60h - 20h) - 3h_overhead) / 60h = 0.62  # 62%の時間短縮

# 決定: 並列化推奨 ✅
```

**実行**:
```python
workers = [
    Worker(id="001", task=tasks[0], workspace="worker_001/"),
    Worker(id="002", task=tasks[1], workspace="worker_002/"),
    Worker(id="003", task=tasks[2], workspace="worker_003/"),
]

# Git Worktree mode (安全性優先)
for worker in workers:
    worker.create_worktree()

# 並列実行
results = execute_parallel(workers, max_workers=3)

# 結果
# 実行時間: 22h (overhead含む)
# 時間短縮: 38h (63%)
# 成功率: 100%
# 競合: 0件
```

**結論**: ✅ 並列化大成功

### Example 2: Base Manager実装 (失敗例を回避)

**タスク**: BaseAIManager実装 (6時間)

**分析**:
```python
# タスク分割（仮）
tasks = [
    Task("Write base_manager.py", estimated_time=3h),
    Task("Write unit tests", estimated_time=2h),
    Task("Update documentation", estimated_time=1h),
]

# 依存関係
dependencies = {
    tasks[1]: [tasks[0]],  # Tests depend on base_manager.py
    tasks[2]: [tasks[0]],  # Docs depend on base_manager.py
}

# ファイル競合リスク
conflict_risk = 0.9  # 🔴 CRITICAL (同一ファイル編集)

# 並列化価値
# Task 1が完了しないとTask 2,3開始不可
# 実質的にSequential実行と同じ

value = 0.1  # 10%の時間短縮（overhead考慮するとマイナス）

# 決定: 並列化しない ❌
```

**実行**:
```python
# Sequential実行
execute_sequential([tasks[0], tasks[1], tasks[2]])

# 結果
# 実行時間: 6h
# 時間短縮: 0h (並列化なし)
# 競合: 0件 (Sequential実行)
# 品質: 高 (集中して実装)
```

**結論**: ✅ Sequential実行が正しい選択

### Example 3: Frontend Component開発 (ハイブリッド)

**タスク**: 5つのReactコンポーネント作成 (各2時間)

**分析**:
```python
tasks = [
    Task("ComponentA", 2h, file="ComponentA.tsx"),
    Task("ComponentB", 2h, file="ComponentB.tsx"),
    Task("ComponentC", 2h, file="ComponentC.tsx"),
    Task("ComponentD", 2h, file="ComponentD.tsx"),
    Task("ComponentE", 2h, file="ComponentE.tsx"),
]

# 依存関係: ComponentAが基底クラス、他は独立
dependencies = {
    tasks[1]: [tasks[0]],
    tasks[2]: [tasks[0]],
    tasks[3]: [tasks[0]],
    tasks[4]: [tasks[0]],
}

# ファイル競合リスク
conflict_risk = 0.1  # 🟢 LOW (異なるファイル)

# 並列化価値（Phase 1 sequential, Phase 2 parallel）
value = 0.5  # 50%の時間短縮
```

**実行**:
```python
# Phase 1: ComponentA（基底クラス）を先に実装
execute_sequential([tasks[0]])  # 2h

# Phase 2: 他4つを並列実装
execute_parallel(tasks[1:5], max_workers=4)  # 2h

# Total: 4h vs Sequential: 10h
# 時間短縮: 6h (60%)
```

**結論**: ✅ ハイブリッド実行が最適

---

## 🎓 学習と改善

### Continuous Learning

```python
class ParallelizationLearner:
    """並列化の学習・改善システム"""

    def __init__(self):
        self.history = []
        self.model = None

    def record_execution(self, execution: Execution):
        """実行結果を記録"""
        self.history.append({
            'task_characteristics': execution.task_characteristics,
            'parallelization_decision': execution.decision,
            'actual_time': execution.actual_time,
            'estimated_time': execution.estimated_time,
            'success_rate': execution.success_rate,
            'conflicts': execution.conflicts,
        })

    def learn(self):
        """履歴から学習"""
        # 機械学習モデルで最適化
        features = extract_features(self.history)
        self.model = train_model(features)

    def predict_optimal_strategy(self, new_task: Task) -> Strategy:
        """新タスクの最適戦略予測"""
        features = extract_features([new_task])
        return self.model.predict(features)
```

### Feedback Loop

```
実行 → 結果記録 → 分析 → 学習 → 改善 → 次回実行
  ↑                                         ↓
  └─────────────────────────────────────────┘
```

---

## 📚 参考資料

### 関連ドキュメント

1. [HYBRID_ENGINE_GUIDE.md](docs/HYBRID_ENGINE_GUIDE.md) - Safety architecture
2. [user_guide.md](docs/user_guide.md) - Complete usage guide
3. [PARALLEL_EXECUTION_IMPLEMENTATION.md](docs/PARALLEL_EXECUTION_IMPLEMENTATION.md)
4. [PARALLEL_DEVELOPMENT_FEASIBILITY_ANALYSIS.md](PARALLEL_DEVELOPMENT_FEASIBILITY_ANALYSIS.md)

### アルゴリズム参考文献

- **Load Balancing**: Graham's List Scheduling (LPT algorithm)
- **Dependency Analysis**: Topological Sort (Kahn's algorithm)
- **Bin Packing**: First Fit Decreasing (FFD)
- **Graph Theory**: Critical Path Method (CPM)

---

## 📝 Appendix: Quick Reference

### Decision Checklist

```
□ タスク数 ≥ 2 ?
□ 独立タスク or 弱い依存関係?
□ ファイル競合リスク < 50% ?
□ 推定時間 > 15分 ?
□ リソース十分?
□ 並列化価値 > 30% ?

✅ 全てYES → 並列化実施
⚠️ 一部NO → 慎重に判断
❌ 多くNO → Sequential実行
```

### Command Examples

```bash
# Dry-run (検証のみ)
python orchestrator.py --dry-run --tasks task1,task2,task3

# 並列実行 (auto worker count)
python orchestrator.py --parallel --tasks task1,task2,task3

# Worker数指定
python orchestrator.py --parallel --workers 4 --tasks task1,task2,task3

# Git Worktree mode
python orchestrator.py --parallel --mode worktree --tasks task1,task2,task3

# モニタリング有効
python orchestrator.py --parallel --monitor --tasks task1,task2,task3
```

---

**Document Version**: 1.0.0
**Last Updated**: 2025-10-24
**Authors**: Claude (Sonnet 4.5) + User Collaboration
**Status**: ✅ Production Ready

**License**: MIT
**Feedback**: このポリシーは継続的に改善されます。提案やフィードバックをお待ちしています。
