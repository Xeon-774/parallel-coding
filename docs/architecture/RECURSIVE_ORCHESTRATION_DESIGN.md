# 再帰的オーケストレーション設計書

## 📋 概要

このドキュメントでは、オーケストレーターAI → ワーカーAI → 子オーケストレーターAI → 孫ワーカーAIという再帰的な構造を実現する設計を説明します。

## ✅ 実現可能性

**結論: 既に技術的に実現可能です！**

現在のシステムには以下の要素が揃っています：

1. ✅ **REST APIサーバー** (`/api/v1/orchestrate` エンドポイント)
2. ✅ **Claude CodeワーカーAI** (HTTP APIを呼び出し可能)
3. ✅ **非同期ジョブ実行** (ジョブID、ステータス確認)
4. ✅ **認証機構** (API Key)
5. ✅ **設定の柔軟性** (OrchestratorConfigModel)

## 🏗️ アーキテクチャ

### レベル構造

```
[Level 0] ユーザー
    │
    ├─ HTTP POST /api/v1/orchestrate
    │
    ▼
[Level 1] 親オーケストレーターAPI (localhost:8000)
    │
    ├─ Task 1.1 → Worker AI 1 (Claude Code)
    │                │
    │                ├─ 通常のコーディング作業
    │                └─ 完了
    │
    ├─ Task 1.2 → Worker AI 2 (Claude Code) ★ 再帰呼び出し
    │                │
    │                ├─ HTTP POST localhost:8000/api/v1/orchestrate
    │                │
    │                ▼
    │           [Level 2] 子オーケストレーター (同じAPIサーバー)
    │                │
    │                ├─ Task 2.1 → Grandchild Worker AI 1
    │                ├─ Task 2.2 → Grandchild Worker AI 2
    │                └─ Task 2.3 → Grandchild Worker AI 3
    │                     │
    │                     └─ 結果を統合して親に返す
    │
    └─ Task 1.3 → Worker AI 3 (Claude Code)
         │
         └─ 完了
```

### データフロー

```
ユーザー
  │
  │ 1. POST /api/v1/orchestrate
  │    { request: "大規模なタスク", config: {...} }
  │
  ▼
親オーケストレーターAPI
  │
  │ 2. タスク分割 (Task 1.1, 1.2, 1.3)
  │
  ├─────────────┬─────────────┐
  ▼             ▼             ▼
Worker 1     Worker 2      Worker 3
(通常)       (再帰)        (通常)
  │             │
  │             │ 3. Worker 2 が API 呼び出し
  │             │    POST localhost:8000/api/v1/orchestrate
  │             │    { request: "サブタスク群",
  │             │      config: { max_depth: 1 } }
  │             ▼
  │        子オーケストレーター
  │             │
  │             │ 4. サブタスク分割
  │             │
  │        ┌────┼────┐
  │        ▼    ▼    ▼
  │      GW1  GW2  GW3  (孫ワーカー)
  │        │    │    │
  │        └────┴────┘
  │             │
  │             │ 5. 結果統合
  │             ▼
  │        子の結果
  │             │
  ▼             ▼
結果1         結果2      結果3
  │             │         │
  └─────────────┴─────────┘
                │
                │ 6. 最終結果統合
                ▼
           統合された成果物
```

## 🔧 実装要件

### 1. ネストレベル制限の追加

無限再帰を防ぐため、最大ネストレベルを設定します。

**orchestrator/api/models.py に追加:**

```python
class OrchestratorConfigModel(BaseModel):
    """Configuration for orchestration job"""
    max_workers: int = Field(default=5, ge=1, le=10)
    default_timeout: int = Field(default=300, ge=60, le=3600)
    max_retries: int = Field(default=2, ge=0, le=5)
    enable_ai_analysis: bool = Field(default=True)
    task_complexity: str = Field(default="medium")
    execution_mode: str = Field(default="wsl")
    enable_worktree: bool = Field(default=False)
    enable_visible_workers: bool = Field(default=False)
    enable_realtime_monitoring: bool = Field(default=True)

    # 🆕 再帰的オーケストレーション設定
    max_recursion_depth: int = Field(
        default=3,
        ge=0,
        le=5,
        description="Maximum recursion depth (0=no recursion)"
    )
    current_depth: int = Field(
        default=0,
        ge=0,
        description="Current recursion level (internal)"
    )
    orchestrator_api_url: Optional[str] = Field(
        default="http://localhost:8000",
        description="URL of orchestrator API for recursive calls"
    )
    orchestrator_api_key: Optional[str] = Field(
        default=None,
        description="API key for recursive orchestrator calls"
    )
```

### 2. 再帰深度のバリデーション

**orchestrator/api/app.py に追加:**

```python
@app.post("/api/v1/orchestrate", ...)
async def orchestrate(
    request: OrchestrateRequest,
    api_key: str = Depends(verify_api_key),
    _: str = Depends(check_rate_limit)
) -> OrchestrateResponse:
    """Submit orchestration job"""

    # 再帰深度チェック
    if request.config:
        current_depth = request.config.current_depth
        max_depth = request.config.max_recursion_depth

        if current_depth >= max_depth:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum recursion depth ({max_depth}) exceeded"
            )

    # ... 既存の処理
```

### 3. ワーカーAI向けのヘルパー関数

**新規ファイル: orchestrator/recursive_helper.py**

```python
"""
Recursive orchestration helper for worker AIs

This module provides utilities for worker AIs to recursively call
the orchestrator API and execute sub-tasks in parallel.
"""

import httpx
from typing import Optional, Dict, Any, List
from pathlib import Path


class RecursiveOrchestratorClient:
    """Client for worker AIs to recursively call orchestrator"""

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        current_depth: int = 0,
        max_depth: int = 3
    ):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.current_depth = current_depth
        self.max_depth = max_depth

    async def orchestrate_subtasks(
        self,
        request: str,
        max_workers: int = 5,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Recursively orchestrate sub-tasks

        Args:
            request: Task description for sub-orchestration
            max_workers: Maximum parallel workers for sub-tasks
            timeout: Timeout for each sub-worker

        Returns:
            Job result dictionary

        Raises:
            ValueError: If max recursion depth reached
            httpx.HTTPError: If API request fails
        """
        if self.current_depth >= self.max_depth:
            raise ValueError(
                f"Cannot recurse: max depth {self.max_depth} reached"
            )

        # Prepare request
        payload = {
            "request": request,
            "config": {
                "max_workers": max_workers,
                "default_timeout": timeout,
                "current_depth": self.current_depth + 1,
                "max_recursion_depth": self.max_depth,
                "orchestrator_api_url": self.api_url,
                "orchestrator_api_key": self.api_key
            }
        }

        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Submit job
            response = await client.post(
                f"{self.api_url}/api/v1/orchestrate",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            job_data = response.json()
            job_id = job_data["job_id"]

            # Poll for completion
            while True:
                status_response = await client.get(
                    f"{self.api_url}/api/v1/jobs/{job_id}/status",
                    headers=headers
                )
                status_response.raise_for_status()
                status_data = status_response.json()

                if status_data["status"] in ["completed", "failed", "partial"]:
                    break

                await asyncio.sleep(5)  # Poll every 5 seconds

            # Get results
            if status_data["status"] == "completed":
                results_response = await client.get(
                    f"{self.api_url}/api/v1/jobs/{job_id}/results",
                    headers=headers
                )
                results_response.raise_for_status()
                return results_response.json()
            else:
                raise RuntimeError(
                    f"Sub-orchestration failed: {status_data.get('error')}"
                )


# Synchronous wrapper for easier use
class SyncRecursiveOrchestratorClient:
    """Synchronous client for recursive orchestration"""

    def __init__(self, **kwargs):
        self.async_client = RecursiveOrchestratorClient(**kwargs)

    def orchestrate_subtasks(
        self,
        request: str,
        max_workers: int = 5,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """Synchronous version of orchestrate_subtasks"""
        import asyncio
        return asyncio.run(
            self.async_client.orchestrate_subtasks(
                request=request,
                max_workers=max_workers,
                timeout=timeout
            )
        )
```

## 📝 使用例

### Example 1: 単純な2レベル再帰

**Level 0 (ユーザー):**

```bash
curl -X POST http://localhost:8000/api/v1/orchestrate \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "request": "大規模Webアプリケーションを構築:\n1. バックエンドAPI\n2. フロントエンド\n3. データベーススキーマ",
    "config": {
      "max_workers": 3,
      "max_recursion_depth": 2
    }
  }'
```

**Level 1 (ワーカーAI 2 - バックエンド担当):**

Worker AI 2が受け取るタスク: "バックエンドAPIを構築"

このワーカーは、さらに細かいタスクに分割したいので再帰呼び出し：

```python
# Worker AI 2 の中で実行されるコード
from orchestrator.recursive_helper import SyncRecursiveOrchestratorClient

client = SyncRecursiveOrchestratorClient(
    api_url="http://localhost:8000",
    api_key="your-api-key",
    current_depth=1,  # Level 1
    max_depth=2
)

result = client.orchestrate_subtasks(
    request="""
    バックエンドAPIのサブタスク:
    1. ユーザー認証エンドポイント実装
    2. データCRUDエンドポイント実装
    3. APIドキュメント生成
    """,
    max_workers=3,
    timeout=300
)

print(f"サブタスク完了: {result['results']}")
```

### Example 2: 実践的な複雑プロジェクト

**シナリオ**: マイクロサービスアーキテクチャの構築

```
Level 0: ユーザー
  │
  └─ "マイクロサービスシステム構築"
      │
      ├─ Level 1 Worker 1: "ユーザーサービス構築"
      │   │
      │   └─ Level 2 (再帰):
      │       ├─ Grandchild 1: "認証ロジック"
      │       ├─ Grandchild 2: "プロフィール管理"
      │       └─ Grandchild 3: "権限管理"
      │
      ├─ Level 1 Worker 2: "商品サービス構築"
      │   │
      │   └─ Level 2 (再帰):
      │       ├─ Grandchild 1: "在庫管理"
      │       ├─ Grandchild 2: "価格エンジン"
      │       └─ Grandchild 3: "検索機能"
      │
      └─ Level 1 Worker 3: "API Gateway構築"
          │
          └─ Level 2 (再帰):
              ├─ Grandchild 1: "ルーティング設定"
              ├─ Grandchild 2: "認証ミドルウェア"
              └─ Grandchild 3: "レート制限"
```

### Example 3: ワーカーAI内での実装例

**Worker AIが受け取るプロンプト:**

```
タスク: "フロントエンドアプリケーションを構築してください"

ヒント: このタスクが複雑な場合、orchestrator APIを再帰的に呼び出して
サブタスクを並列実行できます:

再帰設定:
- API URL: http://localhost:8000
- API Key: ${ORCHESTRATOR_API_KEY}
- 現在の深さ: 1
- 最大深さ: 3
```

**Worker AI (Claude Code) が実行するコード:**

```python
# check_complexity.py
import os
from orchestrator.recursive_helper import SyncRecursiveOrchestratorClient

# タスクの複雑さを判断
task_is_complex = True  # AIが判断

if task_is_complex:
    print("タスクが複雑なため、サブタスクに分割して並列実行します...")

    client = SyncRecursiveOrchestratorClient(
        api_url=os.getenv("ORCHESTRATOR_API_URL", "http://localhost:8000"),
        api_key=os.getenv("ORCHESTRATOR_API_KEY"),
        current_depth=1,
        max_depth=3
    )

    result = client.orchestrate_subtasks(
        request="""
        フロントエンドのサブタスク:
        1. コンポーネントライブラリ作成 (Button, Input, Card等)
        2. ページ実装 (Home, Dashboard, Settings)
        3. 状態管理とAPI統合 (Redux/Context + Axios)
        4. ルーティング設定 (React Router)
        """,
        max_workers=4,
        timeout=300
    )

    print("サブタスク全て完了！")
    print(f"成功: {result['summary']['successful_tasks']} タスク")
    print(f"失敗: {result['summary']['failed_tasks']} タスク")
else:
    print("タスクは単純なので、直接実装します...")
    # 通常のコーディング作業
```

## ⚠️ 注意点と制限

### 1. リソース管理

```
Max workers per level: 5
Max depth: 3

最悪ケース:
Level 0: 1 job
Level 1: 5 workers
Level 2: 5 × 5 = 25 workers
Level 3: 5 × 5 × 5 = 125 workers

合計最大: 156 並列プロセス
```

**推奨設定:**
- `max_recursion_depth: 2` (最大3レベル)
- `max_workers: 3-4` (再帰時は少なめ)
- タイムアウトの調整（深いレベルほど長く）

### 2. エラーハンドリング

- 子の失敗は親に伝播
- `partial` ステータスで部分的成功を許容
- タイムアウトは累積的（親のタイムアウト > 子のタイムアウトの合計）

### 3. コスト考慮

- API呼び出しが増加
- Claude Code実行時間が長くなる
- トークン使用量の増加

### 4. デバッグ

- ジョブIDの階層追跡
- ログに `depth` フィールド追加
- 各レベルの結果を個別に保存

## 🎯 ベストプラクティス

### 1. 適切な粒度

✅ **Good: 本当に並列化が必要な場合のみ再帰**

```python
# 各サービスが独立している
tasks = [
    "ユーザーサービス構築",      # 再帰してもOK
    "商品サービス構築",          # 再帰してもOK
    "注文サービス構築",          # 再帰してもOK
]
```

❌ **Bad: 過度に細分化**

```python
# やりすぎ
tasks = [
    "import文を書く",     # 再帰不要
    "関数1行目を書く",    # 再帰不要
    "関数2行目を書く",    # 再帰不要
]
```

### 2. 深さの制限

```python
# 推奨設定
if current_depth == 0:  # ユーザーレベル
    max_recursion_depth = 3
elif current_depth == 1:  # 1レベル目
    max_recursion_depth = 2
else:  # 2レベル目以降
    max_recursion_depth = 1  # もう再帰しない
```

### 3. タイムアウト調整

```python
# 深さに応じてタイムアウトを調整
timeout_per_depth = {
    0: 3600,  # 1時間（トップレベル）
    1: 1200,  # 20分
    2: 600,   # 10分
    3: 300,   # 5分
}
```

## 🚀 実装ロードマップ

### Phase 1: 基本機能 (1-2日)
- [ ] `max_recursion_depth`, `current_depth` フィールド追加
- [ ] 深度バリデーション実装
- [ ] `RecursiveOrchestratorClient` ヘルパー実装
- [ ] 基本的な統合テスト

### Phase 2: 安全性とモニタリング (2-3日)
- [ ] リソース制限（最大プロセス数）
- [ ] 深度別ログ・メトリクス
- [ ] エラー伝播の改善
- [ ] タイムアウト階層管理

### Phase 3: 高度な機能 (3-5日)
- [ ] 自動深度推定（AIが判断）
- [ ] 結果のマージ戦略
- [ ] 並列度の動的調整
- [ ] コスト見積もり機能

### Phase 4: ドキュメントと例 (1-2日)
- [ ] ユーザーガイド
- [ ] サンプルプロジェクト
- [ ] ベストプラクティス集
- [ ] トラブルシューティング

## 📚 参考リソース

- `orchestrator/api/app.py`: REST APIエンドポイント
- `orchestrator/api/models.py`: リクエスト/レスポンスモデル
- `orchestrator/advanced_orchestrator.py`: コアオーケストレーションロジック
- `orchestrator/api/jobs.py`: ジョブ管理

## まとめ

**再帰的オーケストレーションは現在のアーキテクチャで実現可能です！**

主な変更点:
1. ✅ 設定モデルに `max_recursion_depth` と `current_depth` を追加（小さな変更）
2. ✅ ワーカーAI用のヘルパークラスを提供（新規ファイル）
3. ✅ バリデーションロジックの追加（数行）

既存のREST API、非同期実行、ジョブ管理システムがそのまま使えるため、
実装コストは非常に低く、大きな利益が得られます。

複雑な大規模プロジェクトを真に並列・階層的に処理できる、
世界初のAIオーケストレーションシステムになる可能性があります！🚀
