# 再帰的AIオーケストレーション - ディレクトリ構造とレポート設計

## 📁 ディレクトリ構造の全体像

### 現在の構造（平坦）
```
workspace/
├── worker_1/          # Level 0 Worker 1
├── worker_2/          # Level 0 Worker 2
├── worker_3/          # Level 0 Worker 3
├── logs/              # 全体ログ
├── results.json       # 結果
└── FINAL_RESULT.md    # 最終レポート
```

### 再帰的構造（階層的）
```
workspace/
├── job_abc123/                          # ★ Job ID ベースのルート
│   ├── depth_0/                         # Level 0 (親オーケストレーター)
│   │   ├── metadata.json                # レベル0のメタデータ
│   │   ├── orchestration_plan.json      # タスク分割計画
│   │   ├── worker_1/                    # 通常のワーカー
│   │   │   ├── input.txt
│   │   │   ├── output.txt
│   │   │   ├── error.txt
│   │   │   └── result.json
│   │   ├── worker_2_recursive/          # ★ 再帰的ワーカー
│   │   │   ├── input.txt                # "子オーケストレーションを実行せよ"
│   │   │   ├── output.txt               # 子の結果サマリー
│   │   │   ├── recursive_call.json      # 再帰呼び出しのメタデータ
│   │   │   └── child_job_ref.json       # 子ジョブへの参照
│   │   ├── worker_3/
│   │   │   └── ...
│   │   ├── LEVEL_0_REPORT.md            # このレベルのレポート
│   │   └── level_0_results.json         # このレベルの結果
│   │
│   ├── depth_1/                         # Level 1 (子オーケストレーター)
│   │   ├── parent_worker_id.txt         # 親のworker_2から呼ばれた
│   │   ├── metadata.json                # レベル1のメタデータ
│   │   ├── orchestration_plan.json
│   │   ├── worker_1_1/                  # 孫ワーカー 1
│   │   │   ├── input.txt
│   │   │   ├── output.txt
│   │   │   └── result.json
│   │   ├── worker_1_2/                  # 孫ワーカー 2
│   │   │   └── ...
│   │   ├── worker_1_3_recursive/        # ★ 再再帰的ワーカー
│   │   │   ├── recursive_call.json
│   │   │   └── child_job_ref.json       # さらに子へ
│   │   ├── LEVEL_1_REPORT.md
│   │   └── level_1_results.json
│   │
│   ├── depth_2/                         # Level 2 (孫オーケストレーター)
│   │   ├── parent_worker_id.txt         # worker_1_3から呼ばれた
│   │   ├── worker_2_1/                  # 曾孫ワーカー 1
│   │   ├── worker_2_2/                  # 曾孫ワーカー 2
│   │   ├── LEVEL_2_REPORT.md
│   │   └── level_2_results.json
│   │
│   ├── logs/                            # 全体ログ（時系列）
│   │   ├── depth_0_orchestrator.log
│   │   ├── depth_0_worker_1.log
│   │   ├── depth_0_worker_2.log         # 再帰呼び出しログ含む
│   │   ├── depth_1_orchestrator.log
│   │   ├── depth_1_worker_1_1.log
│   │   ├── depth_2_orchestrator.log
│   │   └── ...
│   │
│   ├── reports/                         # 統合レポート
│   │   ├── tree_view.txt                # ASCII tree 構造
│   │   ├── execution_timeline.json      # 実行タイムライン
│   │   ├── recursion_graph.json         # 再帰グラフ
│   │   └── performance_breakdown.json   # パフォーマンス分析
│   │
│   ├── FINAL_RESULT.md                  # ★ 最終統合レポート
│   ├── complete_results.json            # 全結果の統合
│   └── job_metadata.json                # Job全体のメタデータ
│
└── job_def456/                          # 別のJob
    └── ...
```

## 📊 レポート体系の詳細

### 1. レベル別レポート（`LEVEL_N_REPORT.md`）

各階層でのレポート例：

#### `depth_0/LEVEL_0_REPORT.md`
```markdown
# Level 0 オーケストレーション レポート

## 概要
- **Job ID**: abc123
- **Depth**: 0 (Root)
- **開始時刻**: 2025-10-21 21:30:00
- **完了時刻**: 2025-10-21 21:45:00
- **実行時間**: 15分00秒

## タスク分割
このレベルで3つのタスクに分割：
1. Task 1.1: フロントエンド実装 → worker_1 ✓
2. Task 1.2: バックエンド実装（複雑） → worker_2_recursive ⚡ (再帰)
3. Task 1.3: テスト作成 → worker_3 ✓

## ワーカー実行結果

### Worker 1 (通常) ✓
- **状態**: SUCCESS
- **実行時間**: 3分20秒
- **成果物**: `worker_1/output.txt`
- **サマリー**: Reactコンポーネント5個を作成

### Worker 2 (再帰) ⚡
- **状態**: RECURSIVE_SUCCESS
- **実行時間**: 10分15秒
- **再帰先**: depth_1 (3 sub-workers)
- **子Job ID**: def456
- **サマリー**:
  - 子オーケストレーターが3つのAPIエンドポイントを並列実装
  - 全て成功
  - 統合テスト実施済み

### Worker 3 (通常) ✓
- **状態**: SUCCESS
- **実行時間**: 2分45秒
- **成果物**: `worker_3/output.txt`
- **サマリー**: E2Eテストスイート作成

## 次のレベル
- **depth_1**: Worker 2 が開始した子オーケストレーション
  - 参照: `depth_1/LEVEL_1_REPORT.md`
```

#### `depth_1/LEVEL_1_REPORT.md`
```markdown
# Level 1 オーケストレーション レポート

## 概要
- **Parent Job ID**: abc123
- **Parent Worker**: depth_0/worker_2_recursive
- **Depth**: 1 (Child)
- **開始時刻**: 2025-10-21 21:33:30
- **完了時刻**: 2025-10-21 21:43:00
- **実行時間**: 9分30秒

## 親からの指示
```
バックエンドAPI実装を3つのエンドポイントに分割して実装：
1. ユーザー認証 API
2. データ取得 API
3. データ更新 API
```

## タスク分割
3つのサブタスクに分割：
1. Task 2.1: 認証API → worker_1_1 ✓
2. Task 2.2: 取得API → worker_1_2 ✓
3. Task 2.3: 更新API → worker_1_3 ✓

## ワーカー実行結果
### Worker 1_1 ✓
- **実行時間**: 3分10秒
- **成果物**: auth_api.py, tests/test_auth.py
- **サマリー**: JWT認証を実装、テスト全てパス

### Worker 1_2 ✓
- **実行時間**: 2分50秒
- **成果物**: data_api.py, tests/test_data.py
- **サマリー**: RESTful GET endpoints実装

### Worker 1_3 ✓
- **実行時間**: 3分30秒
- **成果物**: update_api.py, tests/test_update.py
- **サマリー**: PUT/PATCH endpoints実装

## 統合結果
全てのサブワーカーが成功。親（depth_0/worker_2）に結果を返却。
```

### 2. 最終統合レポート（`FINAL_RESULT.md`）

全階層を統合した最終レポート：

```markdown
# 🎯 Job abc123 - 最終統合レポート

## エグゼクティブサマリー
- **Total Execution Time**: 15分00秒
- **Total Workers**: 6 (3 at depth 0, 3 at depth 1)
- **Recursion Depth**: 2 levels
- **Success Rate**: 100% (6/6)

## 再帰構造の可視化

```
[Depth 0] Root Orchestrator (Job: abc123)
├─ [Worker 1] Frontend Implementation ✓ (3m20s)
│   └─ Output: 5 React components
│
├─ [Worker 2] Backend (RECURSIVE) ⚡ (10m15s)
│   │
│   └─ [Depth 1] Child Orchestrator (Job: def456)
│       ├─ [Worker 1_1] Auth API ✓ (3m10s)
│       │   └─ Output: auth_api.py + tests
│       ├─ [Worker 1_2] Data API ✓ (2m50s)
│       │   └─ Output: data_api.py + tests
│       └─ [Worker 1_3] Update API ✓ (3m30s)
│           └─ Output: update_api.py + tests
│
└─ [Worker 3] E2E Tests ✓ (2m45s)
    └─ Output: E2E test suite
```

## 階層別サマリー

### Depth 0 (Root)
- **Workers**: 3 (1 normal, 1 recursive, 1 normal)
- **Success**: 3/3
- **Time**: 15m00s
- **Details**: `depth_0/LEVEL_0_REPORT.md`

### Depth 1 (Child)
- **Parent**: depth_0/worker_2_recursive
- **Workers**: 3 (all normal)
- **Success**: 3/3
- **Time**: 9m30s
- **Details**: `depth_1/LEVEL_1_REPORT.md`

## 成果物の場所

### Frontend Components
- 場所: `depth_0/worker_1/output/`
- ファイル: components/*.jsx (5 files)

### Backend APIs
- 場所: `depth_1/worker_1_*/output/`
- ファイル:
  - `worker_1_1/auth_api.py`
  - `worker_1_2/data_api.py`
  - `worker_1_3/update_api.py`
  - `worker_1_*/tests/` (各種テスト)

### Tests
- 場所: `depth_0/worker_3/output/`
- ファイル: e2e_tests/ (E2Eテストスイート)

## パフォーマンス分析

### 時間配分
```
Total: 15m00s
├─ Depth 0 Orchestration: 30s (3.3%)
├─ Worker 1 (Depth 0): 3m20s (22.2%)
├─ Worker 2 Recursion (Depth 0→1): 10m15s (68.3%)
│   ├─ Depth 1 Orchestration: 30s
│   ├─ Worker 1_1: 3m10s
│   ├─ Worker 1_2: 2m50s
│   └─ Worker 1_3: 3m30s
└─ Worker 3 (Depth 0): 2m45s (18.3%)

Parallelization Benefit:
- Sequential time would be: 18m25s
- Actual time: 15m00s
- Time saved: 3m25s (18.5%)
```

### 再帰オーバーヘッド
- Depth 1 orchestration setup: 30s
- API communication: ~15s
- Total overhead: 45s (4.9% of total time)
- **結論**: 再帰のオーバーヘッドは最小限

## 品質メトリクス
- ✅ All tests passing: 100%
- ✅ Type safety: 0 mypy errors
- ✅ Code coverage: 95%+
- ✅ No security issues found

## トレーサビリティ
各成果物の作成者を追跡可能：
- `git log --author="worker_1"` → Frontend components
- `git log --author="worker_1_1"` → Auth API
- `git log --author="worker_1_2"` → Data API
- etc.
```

## 🔍 メタデータ構造

### `job_metadata.json` (Job全体のメタデータ)
```json
{
  "job_id": "abc123",
  "created_at": "2025-10-21T21:30:00Z",
  "completed_at": "2025-10-21T21:45:00Z",
  "total_duration_seconds": 900,
  "user_request": "フルスタックWebアプリを実装せよ",
  "max_recursion_depth": 3,
  "actual_recursion_depth": 1,
  "recursion_tree": {
    "root": {
      "depth": 0,
      "job_id": "abc123",
      "workers": 3,
      "children": [
        {
          "parent_worker": "worker_2_recursive",
          "depth": 1,
          "job_id": "def456",
          "workers": 3,
          "children": []
        }
      ]
    }
  },
  "total_workers": 6,
  "success_rate": 1.0,
  "workspace_path": "/workspace/job_abc123"
}
```

### `depth_0/metadata.json` (レベル0のメタデータ)
```json
{
  "depth": 0,
  "job_id": "abc123",
  "parent_job_id": null,
  "parent_worker_id": null,
  "started_at": "2025-10-21T21:30:00Z",
  "completed_at": "2025-10-21T21:45:00Z",
  "workers": [
    {
      "worker_id": "worker_1",
      "type": "normal",
      "status": "success",
      "duration_seconds": 200
    },
    {
      "worker_id": "worker_2_recursive",
      "type": "recursive",
      "status": "success",
      "duration_seconds": 615,
      "child_job_id": "def456",
      "recursion_depth": 1
    },
    {
      "worker_id": "worker_3",
      "type": "normal",
      "status": "success",
      "duration_seconds": 165
    }
  ]
}
```

### `depth_1/metadata.json` (レベル1のメタデータ)
```json
{
  "depth": 1,
  "job_id": "def456",
  "parent_job_id": "abc123",
  "parent_worker_id": "worker_2_recursive",
  "started_at": "2025-10-21T21:33:30Z",
  "completed_at": "2025-10-21T21:43:00Z",
  "workers": [
    {
      "worker_id": "worker_1_1",
      "type": "normal",
      "status": "success",
      "duration_seconds": 190
    },
    {
      "worker_id": "worker_1_2",
      "type": "normal",
      "status": "success",
      "duration_seconds": 170
    },
    {
      "worker_id": "worker_1_3",
      "type": "normal",
      "status": "success",
      "duration_seconds": 210
    }
  ]
}
```

### `depth_0/worker_2_recursive/recursive_call.json`
```json
{
  "worker_id": "worker_2_recursive",
  "recursion_initiated_at": "2025-10-21T21:33:30Z",
  "api_url": "http://localhost:8000/api/v1/orchestrate",
  "child_job_id": "def456",
  "child_depth": 1,
  "request_payload": {
    "request": "バックエンドAPI実装を3つのエンドポイントに分割",
    "config": {
      "max_workers": 3,
      "current_depth": 1,
      "max_recursion_depth": 3
    }
  },
  "response_summary": {
    "status": "completed",
    "workers_spawned": 3,
    "all_successful": true,
    "total_duration_seconds": 570
  },
  "child_workspace": "/workspace/job_abc123/depth_1"
}
```

## 🎨 可視化ツール

### `reports/tree_view.txt` (ASCII Tree)
```
Job abc123 - Fullstack Web App Implementation
│
├─ [Depth 0] Root Orchestrator
│  ├─ worker_1 (Frontend) ✓ 3m20s
│  │  └─ 📦 5 React components
│  │
│  ├─ worker_2_recursive (Backend) ⚡ 10m15s
│  │  │
│  │  └─ [Depth 1] Child Orchestrator (Job: def456)
│  │     ├─ worker_1_1 (Auth API) ✓ 3m10s
│  │     │  └─ 📦 auth_api.py + tests
│  │     ├─ worker_1_2 (Data API) ✓ 2m50s
│  │     │  └─ 📦 data_api.py + tests
│  │     └─ worker_1_3 (Update API) ✓ 3m30s
│  │        └─ 📦 update_api.py + tests
│  │
│  └─ worker_3 (E2E Tests) ✓ 2m45s
│     └─ 📦 E2E test suite
│
└─ Total: 15m00s, 6 workers, 100% success
```

### `reports/execution_timeline.json`
```json
{
  "timeline": [
    {"time": "21:30:00", "event": "Job abc123 started", "depth": 0},
    {"time": "21:30:05", "event": "Worker 1 started", "depth": 0},
    {"time": "21:30:05", "event": "Worker 2 started", "depth": 0},
    {"time": "21:30:05", "event": "Worker 3 started", "depth": 0},
    {"time": "21:33:25", "event": "Worker 1 completed", "depth": 0},
    {"time": "21:33:30", "event": "Worker 2 initiated recursion", "depth": 0},
    {"time": "21:33:30", "event": "Child Job def456 started", "depth": 1},
    {"time": "21:33:35", "event": "Worker 1_1 started", "depth": 1},
    {"time": "21:33:35", "event": "Worker 1_2 started", "depth": 1},
    {"time": "21:33:35", "event": "Worker 1_3 started", "depth": 1},
    {"time": "21:35:50", "event": "Worker 3 completed", "depth": 0},
    {"time": "21:36:45", "event": "Worker 1_1 completed", "depth": 1},
    {"time": "21:36:25", "event": "Worker 1_2 completed", "depth": 1},
    {"time": "21:37:05", "event": "Worker 1_3 completed", "depth": 1},
    {"time": "21:43:00", "event": "Child Job def456 completed", "depth": 1},
    {"time": "21:43:00", "event": "Worker 2 recursion completed", "depth": 0},
    {"time": "21:45:00", "event": "Job abc123 completed", "depth": 0}
  ]
}
```

## 📈 レポート集約の仕組み

### Bottom-Up 集約方式

```
1. 最深部（Depth N）のワーカーが完了
   ↓
2. Depth N のオーケストレーターが LEVEL_N_REPORT.md を生成
   ↓
3. 親（Depth N-1）のワーカーが子の結果を受け取る
   ↓
4. Depth N-1 のオーケストレーターが LEVEL_(N-1)_REPORT.md を生成
   ↓
5. これを Depth 0 まで繰り返し
   ↓
6. Depth 0 が全階層の情報を統合して FINAL_RESULT.md を生成
```

### レポート参照チェーン

```
FINAL_RESULT.md (Root)
├─ 参照: depth_0/LEVEL_0_REPORT.md
│  ├─ Worker 1 の結果
│  ├─ Worker 2 の再帰サマリー
│  │  └─ 参照: depth_1/LEVEL_1_REPORT.md
│  │     ├─ Worker 1_1 の結果
│  │     ├─ Worker 1_2 の結果
│  │     └─ Worker 1_3 の結果
│  └─ Worker 3 の結果
└─ 統合メトリクス
```

## 🛡️ トレーサビリティ保証

### 各成果物のメタデータ

各ワーカーの `result.json` に以下を記録：

```json
{
  "worker_id": "worker_1_2",
  "depth": 1,
  "job_id": "def456",
  "parent_job_id": "abc123",
  "parent_worker_id": "worker_2_recursive",
  "task_description": "データ取得APIの実装",
  "created_files": [
    "data_api.py",
    "tests/test_data.py"
  ],
  "git_commits": [
    "a1b2c3d - feat: Implement data retrieval API"
  ],
  "ancestry": [
    "Job abc123 > Depth 0 > worker_2_recursive",
    "Job def456 > Depth 1 > worker_1_2"
  ]
}
```

## 💡 実装のポイント

### 1. **Job IDベースの隔離**
- 各Jobは独立したディレクトリ
- 並行実行時の衝突なし

### 2. **Depthベースの階層化**
- 各レベルが独立してレポート生成
- Bottom-upで集約

### 3. **親子関係の明示**
- `parent_worker_id.txt` で親を記録
- `recursive_call.json` で子を記録
- 双方向トレーサビリティ

### 4. **段階的レポート生成**
- 各レベル完了時にレポート作成
- 最終的にルートが全体を統合
- リアルタイム進捗確認可能

これにより、**どんなに深い再帰でも完全にトレース可能**な体系になります！