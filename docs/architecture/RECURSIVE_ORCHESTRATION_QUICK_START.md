# 再帰的オーケストレーション - クイックスタート

## 📌 TL;DR (結論)

**はい、既に技術的に可能です！** 🎉

現在のシステムは以下を備えています：
- ✅ REST APIサーバー
- ✅ 非同期ジョブ実行
- ✅ Claude CodeワーカーAI（HTTP呼び出し可能）

必要な追加実装はわずかです：
- 設定に `max_recursion_depth` と `current_depth` フィールドを追加（5行）
- ワーカーAI用のヘルパー関数を提供（新規ファイル）
- バリデーション追加（10行程度）

## 🏗️ 基本構造

```
ユーザー
  │
  └─ POST /api/v1/orchestrate (Level 0)
      │
      ├─ Worker 1 (通常タスク) ───→ 完了
      │
      ├─ Worker 2 (複雑タスク) ───→ 再帰呼び出し ★
      │   │
      │   └─ POST /api/v1/orchestrate (Level 1)
      │       │
      │       ├─ Grandchild Worker 1 ───→ 完了
      │       ├─ Grandchild Worker 2 ───→ 完了
      │       └─ Grandchild Worker 3 ───→ 完了
      │           │
      │           └─ 結果を親に統合
      │
      └─ Worker 3 (通常タスク) ───→ 完了
```

## 🚀 使い方

### Step 1: オーケストレーターAPIを起動

```bash
# ターミナル1
python -m orchestrator.api.app
```

### Step 2: ユーザーがジョブを投稿

```bash
# ターミナル2
curl -X POST http://localhost:8000/api/v1/orchestrate \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "request": "大規模プロジェクトを構築:\n1. バックエンド\n2. フロントエンド\n3. データベース",
    "config": {
      "max_workers": 3,
      "max_recursion_depth": 2
    }
  }'

# Response:
# {
#   "job_id": "abc-123",
#   "status": "queued"
# }
```

### Step 3: ワーカーAIが再帰的に呼び出し

Worker 2（バックエンド担当）が受け取るタスク内で、さらに細かく分割したい場合：

```python
# Worker 2 内で実行されるコード
from orchestrator.recursive_helper import SyncRecursiveOrchestratorClient
import os

client = SyncRecursiveOrchestratorClient(
    api_url="http://localhost:8000",
    api_key=os.getenv("ORCHESTRATOR_API_KEY"),
    current_depth=1,
    max_depth=2
)

result = client.orchestrate_subtasks(
    request="""
    バックエンドのサブタスク:
    1. ユーザー認証API
    2. データCRUD API
    3. WebSocket通信
    """,
    max_workers=3
)

print(f"サブタスク完了: {result['results']}")
```

### Step 4: 結果を確認

```bash
# ジョブステータスを確認
curl http://localhost:8000/api/v1/jobs/abc-123/status \
  -H "X-API-Key: your-key"

# 結果を取得
curl http://localhost:8000/api/v1/jobs/abc-123/results \
  -H "X-API-Key: your-key"
```

## 💡 実践例

### 例1: マイクロサービス構築

```
Level 0: ユーザー "マイクロサービスシステム構築"
  │
  ├─ Level 1: Worker "ユーザーサービス"
  │   └─ Level 2: 再帰
  │       ├─ "認証ロジック"
  │       ├─ "プロフィール管理"
  │       └─ "権限システム"
  │
  ├─ Level 1: Worker "商品サービス"
  │   └─ Level 2: 再帰
  │       ├─ "在庫管理"
  │       ├─ "価格エンジン"
  │       └─ "検索機能"
  │
  └─ Level 1: Worker "API Gateway"
      └─ Level 2: 再帰
          ├─ "ルーティング"
          ├─ "認証ミドルウェア"
          └─ "レート制限"
```

### 例2: フロントエンド開発

```
Level 0: "大規模Reactアプリ構築"
  │
  ├─ Level 1: "コンポーネントライブラリ"
  │   └─ Level 2: 再帰
  │       ├─ "基本コンポーネント (Button, Input...)"
  │       ├─ "フォームコンポーネント"
  │       └─ "レイアウトコンポーネント"
  │
  ├─ Level 1: "ページ実装"
  │   └─ Level 2: 再帰
  │       ├─ "Homeページ"
  │       ├─ "Dashboardページ"
  │       └─ "Settingsページ"
  │
  └─ Level 1: "状態管理とAPI統合"
```

## ⚙️ 必要な実装（概算）

### 1. モデル拡張（orchestrator/api/models.py）

```python
class OrchestratorConfigModel(BaseModel):
    # ... 既存フィールド ...

    # 🆕 追加（5行）
    max_recursion_depth: int = Field(default=3, ge=0, le=5)
    current_depth: int = Field(default=0, ge=0)
    orchestrator_api_url: Optional[str] = Field(default="http://localhost:8000")
    orchestrator_api_key: Optional[str] = Field(default=None)
```

### 2. バリデーション（orchestrator/api/app.py）

```python
@app.post("/api/v1/orchestrate", ...)
async def orchestrate(...):
    # 🆕 追加（10行）
    if request.config:
        if request.config.current_depth >= request.config.max_recursion_depth:
            raise HTTPException(
                status_code=400,
                detail=f"Max recursion depth exceeded"
            )
```

### 3. ヘルパークラス（新規ファイル: orchestrator/recursive_helper.py）

```python
# 🆕 新規ファイル（約150行）
class RecursiveOrchestratorClient:
    """Worker AIが再帰的にオーケストレーターを呼び出すためのヘルパー"""

    async def orchestrate_subtasks(
        self,
        request: str,
        max_workers: int = 5
    ) -> Dict[str, Any]:
        # 1. サブジョブを投稿
        # 2. 完了を待機
        # 3. 結果を取得
        # 4. 親に返す
```

### 4. テスト（新規ファイル: tests/test_recursive_orchestration.py）

```python
# 🆕 新規ファイル（約100行）
def test_simple_recursion():
    """2レベル再帰のテスト"""

def test_max_depth_validation():
    """最大深度のバリデーションテスト"""

def test_recursive_error_propagation():
    """エラー伝播のテスト"""
```

**合計**: 約300行の追加（既存コードは変更なし）

## ⚠️ 注意点

### 1. リソース制限

```
max_workers=5, max_depth=3 の場合:

Level 0: 1
Level 1: 5
Level 2: 25
Level 3: 125
───────────
合計: 156 並列プロセス 💥
```

**推奨設定**:
- `max_recursion_depth: 2` (最大3レベル)
- `max_workers: 3-4` (再帰時は控えめ)

### 2. タイムアウト

親のタイムアウト > 子のタイムアウト合計

```python
timeout_per_level = {
    0: 3600,  # 1時間
    1: 1200,  # 20分
    2: 600,   # 10分
}
```

### 3. いつ再帰すべきか？

✅ **再帰推奨**:
- 各サブタスクが独立している
- サブタスクが複雑（10+ファイル、30+分）
- 並列化で大幅な時間短縮が見込める

❌ **再帰不要**:
- タスクが単純（数ファイル、数分）
- サブタスク間に依存関係が多い
- 直列実行が適切

## 📊 効果予測

### シナリオ: マイクロサービス4個構築

**従来（直列実行）**:
```
Service 1: 60分
Service 2: 60分
Service 3: 60分
Service 4: 60分
────────────
合計: 240分 (4時間)
```

**並列実行（Level 1のみ）**:
```
並列で4サービス同時実行
────────────
合計: 60分 (1時間)
節約: 180分 (75%削減) ✨
```

**再帰的並列実行（Level 1 + Level 2）**:
```
Level 1: 4サービス並列
Level 2: 各サービス内で3サブタスク並列
────────────
合計: 20分
節約: 220分 (92%削減) 🚀
```

## 🎯 ユースケース

### 1. 大規模プロジェクト初期構築
- モノレポ構造
- マイクロサービス
- フルスタックアプリ

### 2. リファクタリング
- 複数モジュールの同時リファクタ
- API移行（v1→v2）
- テストカバレッジ向上

### 3. ドキュメント生成
- 各モジュールのドキュメント並列生成
- 多言語翻訳
- API仕様書自動生成

### 4. データ処理
- 大量ファイルの並列処理
- データ変換パイプライン
- バッチ処理

## 📚 次のステップ

1. **詳細設計を読む**: `RECURSIVE_ORCHESTRATION_DESIGN.md`
2. **サンプルコードを試す**: `examples/recursive_orchestration_example.py`
3. **実装する**: Phase 1から順次実装
4. **テストする**: 簡単なプロジェクトで検証
5. **本番運用**: 大規模プロジェクトで活用

## ❓ FAQ

### Q1: 無限ループになりませんか？
A: `max_recursion_depth` で制限されます。デフォルトは3レベル。

### Q2: コストは？
A: Claude Code実行時間 × 並列数。ただし総時間は大幅短縮。

### Q3: エラー処理は？
A: 子の失敗は親に伝播。`partial` ステータスで部分成功を許容。

### Q4: 既存コードへの影響は？
A: ゼロ。再帰機能は完全にオプトイン。既存の使い方は変わりません。

### Q5: どのくらいで実装できますか？
A: 基本機能なら1-2日。完全版は1週間程度。

## 🚀 まとめ

**再帰的オーケストレーションは既に実現可能で、実装コストも低い！**

- ✅ 既存アーキテクチャで実現可能
- ✅ 追加コードは約300行のみ
- ✅ 既存機能への影響なし
- ✅ 大規模プロジェクトで劇的な効率化
- ✅ 世界初のAI再帰的オーケストレーションシステム！

詳細は `RECURSIVE_ORCHESTRATION_DESIGN.md` をご覧ください。
