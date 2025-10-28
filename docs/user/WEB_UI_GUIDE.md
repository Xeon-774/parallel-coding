# Web UI ダッシュボード ガイド 🌐

**Claude Orchestrator v5.0 統括Webインターフェース**

オーケストレーターAIとワーカーAIの動きをリアルタイムで可視化します。

---

## 📋 目次

1. [概要](#概要)
2. [機能](#機能)
3. [セットアップ](#セットアップ)
4. [使用方法](#使用方法)
5. [APIリファレンス](#apiリファレンス)
6. [カスタマイズ](#カスタマイズ)
7. [トラブルシューティング](#トラブルシューティング)

---

## 概要

### v5.0 新機能

- **リアルタイムダッシュボード**: オーケストレーターと全ワーカーの状態を一画面で表示
- **WebSocket通信**: 自動更新（5秒ごと）でリアルタイムに状況を把握
- **ログストリーミング**: 構造化ログをフィルタリング可能
- **スクリーンショット表示**: ワーカーウィンドウのキャプチャを確認
- **ワーカー詳細ビュー**: タスク内容・出力・スクリーンショットを詳細表示

### アーキテクチャ

```
┌─────────────────────────────────────────────────┐
│         ブラウザ (Frontend)                      │
│  ┌───────────────────────────────────────┐     │
│  │  HTML/CSS/JavaScript                  │     │
│  │  - ダッシュボードUI                    │     │
│  │  - WebSocket通信                       │     │
│  │  - リアルタイム更新                    │     │
│  └───────────────┬───────────────────────┘     │
└──────────────────┼─────────────────────────────┘
                   │ WebSocket/HTTP
┌──────────────────▼─────────────────────────────┐
│         FastAPI (Backend)                       │
│  ┌───────────────────────────────────────┐     │
│  │  API Endpoints:                       │     │
│  │  - GET /api/status                    │     │
│  │  - GET /api/logs/{log_file}           │     │
│  │  - GET /api/screenshots/{file}        │     │
│  │  - GET /api/worker/{id}/output        │     │
│  │  - WebSocket /ws                      │     │
│  └───────────────┬───────────────────────┘     │
└──────────────────┼─────────────────────────────┘
                   │
┌──────────────────▼─────────────────────────────┐
│         Workspace (Data Source)                 │
│  ┌───────────────────────────────────────┐     │
│  │  workspace/                           │     │
│  │    ├── worker_1/                      │     │
│  │    │   ├── task.txt                   │     │
│  │    │   ├── output.txt                 │     │
│  │    │   └── error.txt                  │     │
│  │    ├── logs/                          │     │
│  │    │   └── orchestrator_*.jsonl       │     │
│  │    └── screenshots/                   │     │
│  │        └── worker_1_*.png             │     │
│  └───────────────────────────────────────┘     │
└─────────────────────────────────────────────────┘
```

---

## 機能

### 1. システム概要ダッシュボード

- **システムステータス**: 全体の稼働状態（idle/running）
- **アクティブワーカー数**: 現在実行中のワーカー数
- **ワークスペースパス**: データの保存場所
- **最終更新時刻**: 最後にデータが更新された時刻

### 2. ワーカー可視化

各ワーカーカードには以下が表示されます：

- **ワーカーID**: 識別子（例: worker_1）
- **ステータス**: running / pending / completed
- **タスク内容**: 実行中のタスク（最初の100文字）
- **最近の出力**: 最新の5行
- **スクリーンショット**: ワーカーウィンドウのキャプチャ（利用可能な場合）

### 3. ログビューアー

- **リアルタイム表示**: 最新のログを自動更新
- **フィルタリング**: INFO / WARNING / ERROR でフィルタ可能
- **構造化表示**: タイムスタンプ・レベル・メッセージを整形
- **手動更新**: 「🔄 更新」ボタンで即座にリフレッシュ

### 4. ワーカー詳細モーダル

ワーカーカードをクリックすると、詳細が表示されます：

- **完全なタスク内容**: task.txtの全文
- **完全な出力**: output.txtの全文
- **フルサイズスクリーンショット**: 拡大表示

---

## セットアップ

### 必須要件

- Python 3.9+
- Claude Orchestrator v4.2+

### インストール

1. **Web UI依存パッケージをインストール**

```bash
pip install -e ".[web]"
```

これにより以下がインストールされます：
- FastAPI
- uvicorn
- websockets
- aiofiles

2. **インストールの確認**

```bash
python start_dashboard.py --help
```

---

## 使用方法

### 基本的な起動

```bash
python start_dashboard.py
```

ブラウザで以下のURLにアクセス：
```
http://127.0.0.1:8000
```

### カスタムポートで起動

```bash
python start_dashboard.py --port 3000
```

### 外部からアクセス可能にする

```bash
python start_dashboard.py --host 0.0.0.0 --port 8080
```

⚠️ **セキュリティ警告**: 外部アクセスを許可する場合は、ファイアウォールやVPN経由でのアクセスを推奨します。

### ワークスペースを指定

```bash
python start_dashboard.py --workspace /path/to/custom/workspace
```

### オーケストレーターと同時起動

**ターミナル1: Webダッシュボード**
```bash
python start_dashboard.py
```

**ターミナル2: オーケストレーター実行**
```bash
python orchestrator/main.py "Todoアプリを作成してください"
```

ブラウザでリアルタイムに進捗を確認できます！

---

## APIリファレンス

### REST API Endpoints

#### `GET /api/status`

システム全体の状態を取得

**レスポンス:**
```json
{
  "status": "running",
  "workers_count": 3,
  "workers": [
    {
      "id": "worker_1",
      "task": "Todoアプリを作成",
      "status": "running",
      "recent_output": "...",
      "screenshot": "worker_1_20251020_120000.png",
      "updated_at": "2025-10-20T12:00:00"
    }
  ],
  "latest_log": "orchestrator_20251020_120000.jsonl",
  "workspace": "./workspace",
  "timestamp": "2025-10-20T12:00:00"
}
```

#### `GET /api/logs/{log_file}?lines=100`

ログファイルの内容を取得

**パラメータ:**
- `log_file`: ログファイル名
- `lines`: 取得する行数（デフォルト: 100）

**レスポンス:**
```json
{
  "logs": [
    {
      "timestamp": "2025-10-20T12:00:00",
      "level": "INFO",
      "message": "Worker started"
    }
  ],
  "total_lines": 500,
  "returned_lines": 100
}
```

#### `GET /api/screenshots/{screenshot_file}`

スクリーンショット画像を取得

**レスポンス:** PNG画像

#### `GET /api/worker/{worker_id}/output?lines=50`

ワーカーの出力を取得

**パラメータ:**
- `worker_id`: ワーカーID
- `lines`: 取得する行数（デフォルト: 50）

**レスポンス:**
```json
{
  "worker_id": "worker_1",
  "output": "...",
  "total_lines": 200
}
```

### WebSocket Endpoint

#### `WebSocket /ws`

リアルタイム更新用WebSocket接続

**送信メッセージ:**
```
"get_status"
```

**受信メッセージ:** `/api/status`と同じJSON形式

---

## カスタマイズ

### 更新間隔の変更

`web_ui/static/app.js` の以下の部分を編集：

```javascript
// 定期的に更新を要求（5秒ごと）
setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send('get_status');
    }
}, 5000);  // ← この値を変更（ミリ秒）
```

### カラースキームの変更

`web_ui/static/style.css` の`:root`セクションを編集：

```css
:root {
    --primary-color: #2563eb;  /* メインカラー */
    --bg-primary: #0f172a;     /* 背景色 */
    /* ... */
}
```

### 追加のAPIエンドポイント

`web_ui/app.py`に新しいエンドポイントを追加：

```python
@app.get("/api/custom")
async def custom_endpoint():
    return JSONResponse({"message": "Custom data"})
```

---

## トラブルシューティング

### ダッシュボードが起動しない

**問題:** `ModuleNotFoundError: No module named 'fastapi'`

**解決策:**
```bash
pip install -e ".[web]"
```

### WebSocket接続が失敗する

**問題:** コンソールに "WebSocket disconnected" が表示される

**解決策:**
1. サーバーが起動しているか確認
2. ファイアウォールがポート8000をブロックしていないか確認
3. ブラウザのコンソール（F12）でエラーを確認

### ワーカー情報が表示されない

**問題:** ダッシュボードにワーカーが表示されない

**確認事項:**
1. ワークスペースディレクトリが正しいか確認
   ```bash
   ls workspace/
   ```
2. ワーカーディレクトリが存在するか確認
   ```bash
   ls workspace/worker_*
   ```
3. `output.txt`が生成されているか確認
   ```bash
   cat workspace/worker_1/output.txt
   ```

### スクリーンショットが表示されない

**問題:** ワーカーカードにスクリーンショットが表示されない

**解決策:**
1. スクリーンショットディレクトリを確認
   ```bash
   ls workspace/screenshots/
   ```
2. `ORCHESTRATOR_VISIBLE_WORKERS=true`が設定されているか確認
3. PowerShell実行ポリシーを確認（Windows）

### ログが表示されない

**問題:** ログセクションが空

**解決策:**
1. ログディレクトリを確認
   ```bash
   ls workspace/logs/
   ```
2. 最新のログファイルを手動で確認
   ```bash
   cat workspace/logs/orchestrator_*.jsonl
   ```

---

## パフォーマンス最適化

### 大量のワーカーを扱う場合

ワーカー数が多い場合（10+）、以下を検討：

1. **ページネーション実装**
   - 一度に表示するワーカー数を制限

2. **遅延読み込み**
   - スクリーンショットをlazyloadingに

3. **更新間隔の調整**
   - WebSocket更新を10秒間隔に延長

### リソース使用量の削減

```python
# web_ui/app.py
# スクリーンショットのサムネイル生成を追加
from PIL import Image

@app.get("/api/screenshots/{screenshot_file}/thumbnail")
async def get_screenshot_thumbnail(screenshot_file: str):
    # サムネイル生成ロジック
    pass
```

---

## セキュリティ考慮事項

### 本番環境での使用

1. **認証の追加**
   - FastAPIのOAuth2/JWT認証を実装

2. **HTTPS化**
   - リバースプロキシ（nginx/Caddy）でSSL/TLS対応

3. **CORS設定**
   - 必要に応じてCORSを厳格に設定

4. **レート制限**
   - API呼び出しにレート制限を追加

---

## まとめ

Web UIダッシュボードv5.0により、Claude Orchestratorの動きを直感的に把握できるようになりました。

**主な利点:**
- ✅ リアルタイム可視化
- ✅ 複数ワーカーの一元管理
- ✅ ログの効率的な確認
- ✅ スクリーンショットによる視覚的確認

**今後の拡張:**
- タスクの手動追加UI
- パフォーマンスメトリクス表示
- ワーカーの手動停止/再起動
- 統計グラフの追加

---

**Made with ❤️ by AI Parallel Coding Project**

*プロフェッショナルな可視化で、AIオーケストレーションを次のレベルへ*
