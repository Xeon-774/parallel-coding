# 再帰的AIオーケストレーション - ビジュアルガイド

## 🎯 実行フローの可視化

### シナリオ: 「ECサイト全体を実装せよ」

```
👤 ユーザーリクエスト
│  "完全なECサイトを実装: フロントエンド、バックエンド、決済、管理画面"
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ [Depth 0] 親オーケストレーター (Job: abc123)                   │
│ 🤖 AI判断: "これは4つの大きなモジュールに分割できる"            │
└─────────────────────────────────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┬──────────────┐
        ▼                      ▼                      ▼              ▼
   ┌─────────┐          ┌──────────┐          ┌─────────┐    ┌─────────┐
   │Worker 1 │          │Worker 2  │          │Worker 3 │    │Worker 4 │
   │Frontend │          │Backend   │          │Payment  │    │Admin    │
   │         │          │(RECURSIVE│          │         │    │Dashboard│
   └─────────┘          │ NEEDED!) │          └─────────┘    └─────────┘
        │               └──────────┘               │              │
        │                    │                     │              │
        ▼                    │                     ▼              ▼
   [3時間で完了]            │                [2時間で完了]  [1時間で完了]
        │                    │                     │              │
        │                    ▼                     │              │
        │            "バックエンドは複雑すぎる     │              │
        │             子オーケストレーターを起動!" │              │
        │                    │                     │              │
        │                    │ HTTP POST           │              │
        │                    │ /api/v1/orchestrate │              │
        │                    ▼                     │              │
        │    ┌──────────────────────────────────┐ │              │
        │    │[Depth 1] 子オーケストレーター    │ │              │
        │    │(Job: def456, Parent: Worker 2)   │ │              │
        │    │🤖 "バックエンドを3つのAPIに分割" │ │              │
        │    └──────────────────────────────────┘ │              │
        │             │                            │              │
        │      ┌──────┼──────┐                   │              │
        │      ▼      ▼      ▼                   │              │
        │   ┌────┐ ┌────┐ ┌────┐                │              │
        │   │W1_1│ │W1_2│ │W1_3│                │              │
        │   │Auth│ │Data│ │Pay │                │              │
        │   │API │ │API │ │API │                │              │
        │   └────┘ └────┘ └────┘                │              │
        │     │      │      │                    │              │
        │     │      │      │                    │              │
        │     ▼      ▼      ▼                    │              │
        │   [各40分で完了]                       │              │
        │     │      │      │                    │              │
        │     └──────┴──────┘                    │              │
        │            │                           │              │
        │            ▼                           │              │
        │    [子が結果を統合]                    │              │
        │    LEVEL_1_REPORT.md                   │              │
        │            │                           │              │
        │            │ 結果を親に返す            │              │
        │            ▼                           │              │
        │    [Worker 2 が完了]                   │              │
        │            │                           │              │
        └────────────┴───────────────────────────┴──────────────┘
                     │
                     ▼
             [全Worker完了]
             親が最終レポート生成
                     │
                     ▼
            FINAL_RESULT.md
```

## 📊 時系列での実行フロー

```
時刻    Depth 0           Depth 1            Depth 2
────────────────────────────────────────────────────────
10:00  🚀 Job開始
       Task分析中...
10:05
       ├─ W1 開始
       ├─ W2 開始
       ├─ W3 開始
       └─ W4 開始
10:10
       W1 作業中...
       W2 作業中...
       W3 作業中...
       W4 作業中...
10:30
       W3 完了 ✓
       W4 完了 ✓
10:45
       W2: 再帰判断
       "複雑すぎる!"
                        🚀 子Job開始
                        Task分析中...
11:00
       W1 完了 ✓
                        ├─ W1_1 開始
                        ├─ W1_2 開始
                        └─ W1_3 開始
11:20
                        W1_2 完了 ✓
11:30
                        W1_1 完了 ✓
11:35
                        W1_3 完了 ✓
11:40
                        統合処理中...
                        LEVEL_1完了 ✓
                        結果を親に返却
11:45
       W2 完了 ✓
       (子の結果受領)
11:50
       全Worker完了
       最終統合中...
12:00
       ✅ Job完了
       FINAL_RESULT生成
```

## 💾 ディレクトリ構造の実例

実際のファイルシステム上での配置：

```
D:\user\parallel_ai_test_project\workspace\
│
├─ job_abc123_20251021_100000\              # タイムスタンプ付きJob ID
│  │
│  ├─ job_metadata.json                     # Job全体のメタ情報
│  │  {
│  │    "job_id": "abc123",
│  │    "request": "完全なECサイトを実装",
│  │    "total_duration": "2h00m",
│  │    "recursion_depth_actual": 1,
│  │    "total_workers": 7
│  │  }
│  │
│  ├─ depth_0\                               # ★ Root Level
│  │  ├─ metadata.json                       # このレベルのメタ情報
│  │  │  {
│  │  │    "depth": 0,
│  │  │    "workers_count": 4,
│  │  │    "recursive_workers": ["worker_2"]
│  │  │  }
│  │  │
│  │  ├─ orchestration_plan.json             # タスク分割計画
│  │  │  {
│  │  │    "original_request": "ECサイト実装",
│  │  │    "decomposed_tasks": [
│  │  │      {"id": 1, "name": "Frontend", "complexity": "medium"},
│  │  │      {"id": 2, "name": "Backend", "complexity": "high", "recursive": true},
│  │  │      {"id": 3, "name": "Payment", "complexity": "medium"},
│  │  │      {"id": 4, "name": "Admin", "complexity": "low"}
│  │  │    ]
│  │  │  }
│  │  │
│  │  ├─ worker_1\                           # Frontend Worker
│  │  │  ├─ input.txt                        # タスク指示
│  │  │  │  "React + TypeScriptでECサイトのフロントエンドを実装"
│  │  │  │
│  │  │  ├─ output.txt                       # 実行ログ
│  │  │  │  "Created 12 components..."
│  │  │  │
│  │  │  ├─ result.json                      # 構造化結果
│  │  │  │  {
│  │  │  │    "status": "success",
│  │  │  │    "duration_seconds": 10800,
│  │  │  │    "files_created": 25,
│  │  │  │    "git_commits": ["f1a2b3c"]
│  │  │  │  }
│  │  │  │
│  │  │  └─ artifacts\                       # 成果物
│  │  │     ├─ src\
│  │  │     │  ├─ components\
│  │  │     │  │  ├─ ProductList.tsx
│  │  │     │  │  ├─ Cart.tsx
│  │  │     │  │  └─ ...
│  │  │     │  └─ pages\
│  │  │     └─ tests\
│  │  │
│  │  ├─ worker_2_recursive\                 # ★ Backend (再帰的Worker)
│  │  │  ├─ input.txt
│  │  │  │  "バックエンドAPI群を実装（複雑な場合は再帰呼び出し可）"
│  │  │  │
│  │  │  ├─ decision.txt                     # AI判断記録
│  │  │  │  "Analysis: Backend is too complex (20+ endpoints)"
│  │  │  │  "Decision: Initiating recursive orchestration"
│  │  │  │  "子オーケストレーターを起動します"
│  │  │  │
│  │  │  ├─ recursive_call.json              # 再帰呼び出しの詳細
│  │  │  │  {
│  │  │  │    "initiated_at": "2025-10-21T10:45:00Z",
│  │  │  │    "api_url": "http://localhost:8000/api/v1/orchestrate",
│  │  │  │    "child_job_id": "def456",
│  │  │  │    "request_to_child": "バックエンドを3つのAPIモジュールに分割",
│  │  │  │    "config": {
│  │  │  │      "current_depth": 1,
│  │  │  │      "max_workers": 3
│  │  │  │    }
│  │  │  │  }
│  │  │  │
│  │  │  ├─ child_job_ref.json               # 子Jobへの参照
│  │  │  │  {
│  │  │  │    "child_job_id": "def456",
│  │  │  │    "child_workspace": "./depth_1",
│  │  │  │    "child_report": "./depth_1/LEVEL_1_REPORT.md"
│  │  │  │  }
│  │  │  │
│  │  │  ├─ output.txt                       # 子からの結果サマリー
│  │  │  │  "Child orchestration completed successfully"
│  │  │  │  "3 API modules implemented:"
│  │  │  │  "- Auth API (JWT, OAuth2)"
│  │  │  │  "- Data API (CRUD operations)"
│  │  │  │  "- Payment API (Stripe integration)"
│  │  │  │
│  │  │  └─ result.json
│  │  │     {
│  │  │       "status": "recursive_success",
│  │  │       "child_job_id": "def456",
│  │  │       "child_workers": 3,
│  │  │       "all_child_tasks_successful": true
│  │  │     }
│  │  │
│  │  ├─ worker_3\                           # Payment Integration Worker
│  │  │  ├─ input.txt
│  │  │  ├─ output.txt
│  │  │  ├─ result.json
│  │  │  └─ artifacts\
│  │  │     └─ payment_integration\
│  │  │
│  │  ├─ worker_4\                           # Admin Dashboard Worker
│  │  │  ├─ input.txt
│  │  │  ├─ output.txt
│  │  │  ├─ result.json
│  │  │  └─ artifacts\
│  │  │     └─ admin_dashboard\
│  │  │
│  │  ├─ LEVEL_0_REPORT.md                   # このレベルのレポート
│  │  │  # Level 0 オーケストレーション レポート
│  │  │  ## 概要
│  │  │  - Job ID: abc123
│  │  │  - Workers: 4 (1 recursive)
│  │  │  ...
│  │  │
│  │  └─ level_0_results.json                # このレベルの結果
│  │     {
│  │       "depth": 0,
│  │       "workers": [...],
│  │       "recursive_workers": [
│  │         {
│  │           "worker_id": "worker_2",
│  │           "child_depth": 1,
│  │           "child_job_id": "def456"
│  │         }
│  │       ]
│  │     }
│  │
│  ├─ depth_1\                                # ★ Child Level (Worker 2が開始)
│  │  ├─ parent_info.json                     # 親への参照
│  │  │  {
│  │  │    "parent_job_id": "abc123",
│  │  │    "parent_depth": 0,
│  │  │    "parent_worker_id": "worker_2_recursive",
│  │  │    "initiated_by": "worker_2 AI decision"
│  │  │  }
│  │  │
│  │  ├─ metadata.json
│  │  │  {
│  │  │    "depth": 1,
│  │  │    "job_id": "def456",
│  │  │    "workers_count": 3
│  │  │  }
│  │  │
│  │  ├─ orchestration_plan.json
│  │  │  {
│  │  │    "parent_request": "バックエンドAPI実装",
│  │  │    "decomposed_tasks": [
│  │  │      {"id": 1, "name": "Auth API"},
│  │  │      {"id": 2, "name": "Data API"},
│  │  │      {"id": 3, "name": "Payment API"}
│  │  │    ]
│  │  │  }
│  │  │
│  │  ├─ worker_1_1\                          # Auth API Worker
│  │  │  ├─ input.txt
│  │  │  │  "認証APIを実装: JWT, OAuth2対応"
│  │  │  ├─ output.txt
│  │  │  ├─ result.json
│  │  │  │  {
│  │  │  │    "depth": 1,
│  │  │    "parent_chain": ["abc123/worker_2"],
│  │  │  │    "ancestry": "Job abc123 > Worker 2 > Job def456 > Worker 1_1"
│  │  │  │  }
│  │  │  └─ artifacts\
│  │  │     ├─ auth_api.py
│  │  │     ├─ jwt_handler.py
│  │  │     ├─ oauth2_provider.py
│  │  │     └─ tests\
│  │  │
│  │  ├─ worker_1_2\                          # Data API Worker
│  │  │  └─ ...
│  │  │
│  │  ├─ worker_1_3\                          # Payment API Worker
│  │  │  └─ ...
│  │  │
│  │  ├─ LEVEL_1_REPORT.md                    # 子レベルのレポート
│  │  │  # Level 1 オーケストレーション レポート
│  │  │  ## 親からの指示
│  │  │  - Parent Job: abc123
│  │  │  - Parent Worker: worker_2_recursive
│  │  │  - Request: バックエンドAPI実装
│  │  │  ...
│  │  │
│  │  └─ level_1_results.json
│  │     {
│  │       "depth": 1,
│  │       "parent_job_id": "abc123",
│  │       "workers": [...]
│  │     }
│  │
│  ├─ logs\                                    # 統合ログディレクトリ
│  │  ├─ orchestrator.log                     # メインオーケストレーターログ
│  │  ├─ depth_0_orchestrator.jsonl           # Depth 0の構造化ログ
│  │  ├─ depth_0_worker_1.log
│  │  ├─ depth_0_worker_2.log                 # 再帰呼び出しログ含む
│  │  ├─ depth_0_worker_3.log
│  │  ├─ depth_0_worker_4.log
│  │  ├─ depth_1_orchestrator.jsonl           # Depth 1の構造化ログ
│  │  ├─ depth_1_worker_1_1.log
│  │  ├─ depth_1_worker_1_2.log
│  │  └─ depth_1_worker_1_3.log
│  │
│  ├─ reports\                                 # 統合レポートディレクトリ
│  │  ├─ tree_view.txt                        # ASCII tree構造
│  │  │  Job abc123 - EC Site Implementation
│  │  │  │
│  │  │  ├─ [Depth 0]
│  │  │  │  ├─ worker_1 (Frontend) ✓
│  │  │  │  ├─ worker_2 (Backend, RECURSIVE) ⚡
│  │  │  │  │  └─ [Depth 1]
│  │  │  │  │     ├─ worker_1_1 (Auth) ✓
│  │  │  │  │     ├─ worker_1_2 (Data) ✓
│  │  │  │  │     └─ worker_1_3 (Payment) ✓
│  │  │  │  ├─ worker_3 (Payment Integration) ✓
│  │  │  │  └─ worker_4 (Admin) ✓
│  │  │
│  │  ├─ execution_timeline.json              # タイムライン
│  │  │  [
│  │  │    {"time": "10:00:00", "event": "Job started", "depth": 0},
│  │  │    {"time": "10:05:00", "event": "Workers spawned", "depth": 0},
│  │  │    {"time": "10:45:00", "event": "Recursion initiated", "depth": 0},
│  │  │    {"time": "10:45:05", "event": "Child job started", "depth": 1},
│  │  │    ...
│  │  │  ]
│  │  │
│  │  ├─ recursion_graph.dot                  # Graphviz DOT format
│  │  │  digraph recursion {
│  │  │    "Job_abc123" -> "Worker_2";
│  │  │    "Worker_2" -> "Job_def456";
│  │  │    "Job_def456" -> "Worker_1_1";
│  │  │    "Job_def456" -> "Worker_1_2";
│  │  │    "Job_def456" -> "Worker_1_3";
│  │  │  }
│  │  │
│  │  └─ performance_breakdown.json           # パフォーマンス分析
│  │     {
│  │       "total_time_seconds": 7200,
│  │       "by_depth": {
│  │         "0": {"time": 7200, "workers": 4},
│  │         "1": {"time": 3600, "workers": 3}
│  │       },
│  │       "parallelization_efficiency": 0.85
│  │     }
│  │
│  ├─ FINAL_RESULT.md                          # ★ 最終統合レポート
│  │  # 🎯 Job abc123 - 最終統合レポート
│  │  ## エグゼクティブサマリー
│  │  - **Total Duration**: 2時間00分
│  │  - **Total Workers**: 7 (4 at depth 0, 3 at depth 1)
│  │  - **Recursion Depth**: 1 level
│  │  - **Success Rate**: 100%
│  │
│  │  ## 再帰構造
│  │  [Depth 0] Root
│  │  ├─ Worker 1: Frontend ✓
│  │  ├─ Worker 2: Backend (RECURSIVE) ⚡
│  │  │  └─ [Depth 1] Child
│  │  │     ├─ Worker 1_1: Auth API ✓
│  │  │     ├─ Worker 1_2: Data API ✓
│  │  │     └─ Worker 1_3: Payment API ✓
│  │  ├─ Worker 3: Payment Integration ✓
│  │  └─ Worker 4: Admin Dashboard ✓
│  │  ...
│  │
│  ├─ complete_results.json                    # 全結果の統合JSON
│  │  {
│  │    "job_id": "abc123",
│  │    "status": "completed",
│  │    "hierarchy": {
│  │      "depth_0": {
│  │        "workers": [...],
│  │        "children": {
│  │          "worker_2": {
│  │            "depth_1": {
│  │              "workers": [...]
│  │            }
│  │          }
│  │        }
│  │      }
│  │    }
│  │  }
│  │
│  └─ artifacts\                               # 全成果物の統合
│     ├─ frontend\        (from depth_0/worker_1)
│     ├─ backend\
│     │  ├─ auth\         (from depth_1/worker_1_1)
│     │  ├─ data\         (from depth_1/worker_1_2)
│     │  └─ payment\      (from depth_1/worker_1_3)
│     ├─ payment_integration\  (from depth_0/worker_3)
│     └─ admin\           (from depth_0/worker_4)
│
└─ job_ghi789_20251021_140000\                # 別のJob
   └─ ...
```

## 🔍 レポートの参照方法

### ユーザーがレポートを読む順序

```
1. まず FINAL_RESULT.md を開く
   ↓
   "Job全体のサマリーと再帰構造を確認"

2. 興味のある部分の詳細を見る
   ↓
   例: Backend部分の詳細が知りたい
   ↓
   depth_0/LEVEL_0_REPORT.md を開く
   ↓
   Worker 2 (Backend) のセクションを読む
   ↓
   "参照: depth_1/LEVEL_1_REPORT.md" というリンクを辿る
   ↓
   depth_1/LEVEL_1_REPORT.md を開く
   ↓
   3つのAPIの実装詳細を確認

3. 具体的な成果物を確認
   ↓
   depth_1/worker_1_1/artifacts/auth_api.py を開く
   ↓
   実装コードを確認
```

## 📊 リアルタイム進捗確認

実行中もディレクトリ構造から進捗確認可能：

```bash
# Job全体の状態確認
$ cat workspace/job_abc123/job_metadata.json

# 現在のレベルの状態
$ ls workspace/job_abc123/depth_0/
# まだ完了していないworkerは result.json がない

# 個別Workerの進捗
$ tail -f workspace/job_abc123/logs/depth_0_worker_2.log

# 再帰が発生したか確認
$ ls workspace/job_abc123/depth_0/worker_2_recursive/
# recursive_call.json があれば再帰発生

# 子の状態確認
$ ls workspace/job_abc123/depth_1/
# depth_1 ディレクトリが存在すれば子が実行中/完了
```

## 🎨 レポート生成のタイミング

```
Workers 実行
    ↓
Worker完了 → result.json 生成
    ↓
全Worker完了
    ↓
Orchestrator が集約
    ↓
LEVEL_N_REPORT.md 生成  ← このレベルのレポート
    ↓
親に結果を返す (再帰の場合)
    ↓
親のWorkerが完了
    ↓
親のOrchestratorが集約
    ↓
LEVEL_(N-1)_REPORT.md 生成
    ↓
... (Depth 0 まで繰り返し)
    ↓
Root Orchestrator が全体を統合
    ↓
FINAL_RESULT.md 生成  ← 最終レポート
```

## 💡 設計の優れた点

### 1. **完全なトレーサビリティ**
- どの成果物も `ancestry` フィールドで作成者を追跡可能
- Git commit との連携で変更履歴も完全

### 2. **段階的な可視化**
- 各レベルで独立したレポート
- ユーザーは興味のあるレベルだけ詳細確認可能

### 3. **並行実行の安全性**
- Job IDベースのディレクトリ分離
- 複数Jobの同時実行が可能

### 4. **デバッグの容易性**
- ログが階層ごとに分離
- 問題のあるレベルを特定しやすい

### 5. **拡張性**
- 新しいメトリクスを `reports/` に追加可能
- カスタムレポート生成ツールを簡単に追加

これで**どんなに深い再帰でも完全に可視化・追跡可能**なシステムになります！🎯