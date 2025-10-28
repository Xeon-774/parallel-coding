# AI対話可視化 - 詳細ロードマップ

**機能名**: AI対話のリアルタイムGUI表示
**優先度**: 🔴 最高
**期間**: 3日
**担当**: Frontend + Backend
**Phase**: 1.1

---

## 📋 概要

### 目的
ユーザーがワーカーAI⇔オーケストレーターAIの対話をリアルタイムでGUIから視覚的に確認できるようにする。これにより、真のAI-to-AI通信を「見える化」し、システムの透明性と信頼性を向上させる。

### 現状と問題点

**現状**:
- ✅ 対話ログはファイルに完全保存されている
  - `workspace/worker_XXX/dialogue_transcript.jsonl` (機械可読)
  - `workspace/worker_XXX/dialogue_transcript.txt` (人間可読)
- ✅ ログには以下が記録されている：
  - タイムスタンプ
  - 方向（worker→orchestrator / orchestrator→worker）
  - コンテンツ（実際の対話内容）
  - タイプ（output / response）
  - 確認タイプ（file_write, file_delete など）
  - 確認メッセージ

**問題点**:
- ❌ ファイルを直接開かないと見られない
- ❌ リアルタイムで進行中の対話が見えない
- ❌ 複数ワーカーの対話を同時に確認できない
- ❌ ハイブリッドエンジンの決定理由が見えない

### 期待される成果

**ユーザー体験**:
```
ユーザーがWebダッシュボードを開くと：
1. 現在実行中の全ワーカーのリストが見える
2. 各ワーカーをクリックすると対話ビューが開く
3. チャット形式で対話がリアルタイム表示される
4. 確認要求はハイライト表示される
5. オーケストレーターの決定理由が添えられる
6. 過去の対話履歴も遡れる
```

**技術成果**:
- WebSocket経由のリアルタイムストリーミング
- スケーラブルなアーキテクチャ（8ワーカー同時対応）
- 検索・フィルタリング機能
- エクスポート機能（対話ログのダウンロード）

---

## 🏗️ 技術設計

### アーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│                  Web Dashboard                      │
│  ┌──────────────────────────────────────────────┐  │
│  │         React/Vue Component                  │  │
│  │  ┌────────────┐  ┌────────────┐             │  │
│  │  │ Worker     │  │ Dialogue   │             │  │
│  │  │ List       │  │ View       │             │  │
│  │  └────────────┘  └────────────┘             │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                        ↕ WebSocket
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend                        │
│  ┌──────────────────────────────────────────────┐  │
│  │  /ws/dialogue/{worker_id}                    │  │
│  │  - WebSocketエンドポイント                    │  │
│  │  - リアルタイムストリーミング                  │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  DialogueMonitor                             │  │
│  │  - ファイル監視（watchdog）                   │  │
│  │  - JSONL解析                                 │  │
│  │  - WebSocket配信                             │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                        ↕ File Watch
┌─────────────────────────────────────────────────────┐
│         Worker Workspace                            │
│  workspace/worker_001/dialogue_transcript.jsonl     │
│  workspace/worker_002/dialogue_transcript.jsonl     │
│  workspace/worker_XXX/dialogue_transcript.jsonl     │
└─────────────────────────────────────────────────────┘
```

### 技術スタック

**Backend**:
- FastAPI (WebSocket サポート)
- watchdog (ファイル監視)
- asyncio (非同期処理)
- Python 3.11+

**Frontend**:
- React または Vue.js
- WebSocket client
- Tailwind CSS (スタイリング)
- React Query / VueX (状態管理)

**データフォーマット**:
```json
{
  "timestamp": 1698123456.789,
  "direction": "worker→orchestrator",
  "content": "I need to create a file...",
  "type": "output",
  "confirmation_type": "file_write",
  "confirmation_message": "Create models/user.py?"
}
```

### データフロー

```
1. Worker Manager が対話を記録
   ↓
2. dialogue_transcript.jsonl に追記
   ↓
3. DialogueMonitor がファイル変更を検知
   ↓
4. 新しいエントリーを解析
   ↓
5. WebSocket経由でフロントエンドに配信
   ↓
6. UIが即座に更新
```

---

## 📅 実装計画（3日間）

### Day 1: Backend実装（8時間）

**午前（4時間）**:
- [ ] WebSocketエンドポイント実装
  - `/ws/dialogue/{worker_id}` エンドポイント作成
  - WebSocket接続管理
  - 切断処理

**午後（4時間）**:
- [ ] DialogueMonitor実装
  - watchdogでファイル監視
  - JSONL解析ロジック
  - WebSocket配信ロジック
- [ ] 複数ワーカー対応
  - 同時接続管理
  - ワーカー別ストリーム分離

**成果物**:
```python
# orchestrator/api/dialogue_ws.py
from fastapi import WebSocket
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DialogueMonitor(FileSystemEventHandler):
    def __init__(self, worker_id: str, websocket: WebSocket):
        self.worker_id = worker_id
        self.websocket = websocket
        self.last_position = 0

    def on_modified(self, event):
        """ファイル変更時に新しいエントリーを配信"""
        if event.src_path.endswith('dialogue_transcript.jsonl'):
            # 新しい行を読み込み
            new_entries = self._read_new_entries()
            # WebSocket経由で配信
            asyncio.create_task(self._send_entries(new_entries))

@app.websocket("/ws/dialogue/{worker_id}")
async def dialogue_websocket(websocket: WebSocket, worker_id: str):
    await websocket.accept()

    # 監視開始
    monitor = DialogueMonitor(worker_id, websocket)
    observer = Observer()
    observer.schedule(monitor, f"workspace/{worker_id}", recursive=False)
    observer.start()

    try:
        # 接続維持
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        observer.stop()
```

---

### Day 2: Frontend実装（8時間）

**午前（4時間）**:
- [ ] WebSocketクライアント実装
  - 接続管理
  - 再接続ロジック
  - エラーハンドリング
- [ ] 対話メッセージコンポーネント
  - Worker→Orchestratorメッセージ
  - Orchestrator→Workerメッセージ
  - タイムスタンプ表示

**午後（4時間）**:
- [ ] 対話ビューコンポーネント
  - チャット形式レイアウト
  - スクロール管理
  - 確認要求のハイライト
- [ ] ワーカーリストコンポーネント
  - 全ワーカー表示
  - 選択機能
  - 状態インジケーター

**成果物**:
```tsx
// components/DialogueView.tsx
import { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

interface DialogueEntry {
  timestamp: number;
  direction: string;
  content: string;
  type: string;
  confirmation_type?: string;
}

export function DialogueView({ workerId }: { workerId: string }) {
  const [entries, setEntries] = useState<DialogueEntry[]>([]);
  const { messages, isConnected } = useWebSocket(
    `ws://localhost:8000/ws/dialogue/${workerId}`
  );

  useEffect(() => {
    if (messages.length > 0) {
      setEntries(prev => [...prev, ...messages]);
    }
  }, [messages]);

  return (
    <div className="dialogue-container">
      <div className="dialogue-header">
        <h2>{workerId}</h2>
        <span className={isConnected ? 'connected' : 'disconnected'}>
          {isConnected ? '🟢 Live' : '🔴 Disconnected'}
        </span>
      </div>

      <div className="dialogue-messages">
        {entries.map((entry, idx) => (
          <DialogueMessage key={idx} entry={entry} />
        ))}
      </div>
    </div>
  );
}

function DialogueMessage({ entry }: { entry: DialogueEntry }) {
  const isWorker = entry.direction === 'worker→orchestrator';
  const isConfirmation = entry.confirmation_type !== undefined;

  return (
    <div className={`message ${isWorker ? 'worker' : 'orchestrator'} ${isConfirmation ? 'highlight' : ''}`}>
      <div className="message-header">
        <span className="direction">{entry.direction}</span>
        <span className="timestamp">{new Date(entry.timestamp * 1000).toLocaleTimeString()}</span>
      </div>
      <div className="message-content">{entry.content}</div>
      {isConfirmation && (
        <div className="confirmation-badge">
          {entry.confirmation_type}
        </div>
      )}
    </div>
  );
}
```

---

### Day 3: 統合とテスト（8時間）

**午前（4時間）**:
- [ ] 統合テスト
  - Backend + Frontend接続テスト
  - 複数ワーカー同時表示テスト
  - リアルタイム更新確認
- [ ] パフォーマンステスト
  - 8ワーカー同時実行
  - WebSocket負荷テスト
  - メモリリーク確認

**午後（4時間）**:
- [ ] UI/UX改善
  - スタイリング調整
  - レスポンシブ対応
  - アクセシビリティ
- [ ] ドキュメント作成
  - API文書
  - ユーザーガイド更新
  - トラブルシューティング

**成果物**:
- 完全に動作するAI対話可視化機能
- テストレポート
- 更新されたドキュメント

---

## ✅ タスク分解（詳細）

### Backend Tasks

- [ ] **WebSocketエンドポイント実装** (3時間)
  - FastAPI WebSocketルート作成
  - 接続/切断管理
  - エラーハンドリング

- [ ] **DialogueMonitor実装** (4時間)
  - watchdog FileSystemEventHandler継承
  - JSONL解析ロジック
  - 増分読み込み（最後の位置から）
  - WebSocket配信ロジック

- [ ] **複数ワーカー対応** (2時間)
  - WebSocket接続プール管理
  - ワーカー別ストリーム分離
  - 接続数制限

- [ ] **テスト** (3時間)
  - ユニットテスト
  - 統合テスト
  - WebSocketクライアントモックテスト

### Frontend Tasks

- [ ] **WebSocketクライアント** (2時間)
  - useWebSocketカスタムフック
  - 再接続ロジック
  - エラーハンドリング

- [ ] **対話メッセージコンポーネント** (3時間)
  - メッセージレイアウト
  - 方向別スタイリング
  - タイムスタンプフォーマット
  - 確認要求バッジ

- [ ] **対話ビューコンポーネント** (3時間)
  - チャットレイアウト
  - 自動スクロール
  - フィルタリング機能
  - 検索機能

- [ ] **ワーカーリストコンポーネント** (2時間)
  - リスト表示
  - 選択機能
  - 状態インジケーター

- [ ] **テストとUI改善** (4時間)
  - E2Eテスト
  - レスポンシブ対応
  - スタイリング最終調整

---

## 🧪 検証基準

### 機能検証

**基本機能**:
- ✅ WebSocketが正常に接続される
- ✅ リアルタイムで対話が表示される
- ✅ 複数ワーカーの対話を同時表示できる
- ✅ 過去の対話履歴が読み込まれる

**高度な機能**:
- ✅ 確認要求がハイライト表示される
- ✅ ワーカー別にフィルタリングできる
- ✅ 対話を検索できる
- ✅ 対話ログをエクスポートできる

### パフォーマンス検証

**負荷テスト**:
- ✅ 8ワーカー同時実行でもスムーズ
- ✅ 1000メッセージ表示でもラグなし
- ✅ WebSocket接続が安定（99%以上）
- ✅ メモリリークなし（24時間稼働テスト）

**レスポンステスト**:
- ✅ メッセージ表示レイテンシー < 100ms
- ✅ UI操作応答時間 < 50ms
- ✅ スクロール滑らか（60fps維持）

### ユーザビリティ検証

**ユーザーテスト**:
- ✅ 初見ユーザーが5分以内に使い方を理解
- ✅ AI対話の流れが直感的に理解できる
- ✅ 確認要求と応答の関係が明確
- ✅ エラー発生時のメッセージがわかりやすい

### 自動テスト

```python
# tests/test_dialogue_visualization.py
import pytest
from fastapi.testclient import TestClient
from orchestrator.api.dialogue_ws import app

@pytest.mark.asyncio
async def test_websocket_connection():
    """WebSocket接続テスト"""
    client = TestClient(app)
    with client.websocket_connect("/ws/dialogue/worker_001") as websocket:
        # 接続成功を確認
        assert websocket is not None

@pytest.mark.asyncio
async def test_realtime_streaming():
    """リアルタイムストリーミングテスト"""
    client = TestClient(app)
    with client.websocket_connect("/ws/dialogue/worker_001") as websocket:
        # ファイルに書き込み
        write_dialogue_entry(...)

        # メッセージ受信を確認
        data = websocket.receive_json()
        assert data['content'] is not None

@pytest.mark.asyncio
async def test_multiple_workers():
    """複数ワーカー同時接続テスト"""
    # 8ワーカー同時接続
    connections = []
    for i in range(8):
        ws = websocket_connect(f"/ws/dialogue/worker_{i:03d}")
        connections.append(ws)

    # 全接続が正常
    assert len(connections) == 8
```

---

## 🔗 依存関係

### 前提条件
- ✅ 対話ログ記録機能（worker_manager.py）- **既存**
- ✅ JSONL形式の対話ログ - **既存**
- ✅ FastAPI backend基盤 - **要確認/実装**
- ✅ Frontend開発環境 - **要セットアップ**

### ブロッカー
- ❌ なし（すべての依存が満たされている）

### 並行作業可能な項目
- ✅ メトリクスダッシュボード開発（別チーム）
- ✅ ワーカー状態表示開発（別チーム）
- ✅ ドキュメント作成（別チーム）

---

## ⚠️ リスクと対策

### リスク1: WebSocket接続の不安定性
**影響**: リアルタイム表示が途切れる
**確率**: 中
**対策**:
- 自動再接続ロジック実装
- 接続状態の明示的表示
- バッファリング機構

### リスク2: 大量メッセージでのパフォーマンス劣化
**影響**: UIがラグる、メモリ不足
**確率**: 低
**対策**:
- 仮想スクロール実装
- 古いメッセージの自動削除
- ページネーション導入

### リスク3: ファイル監視の遅延
**影響**: リアルタイム性が損なわれる
**確率**: 低
**対策**:
- watchdogの設定最適化
- ポーリング間隔調整
- OS別の最適化

### リスク4: フロントエンド開発の遅延
**影響**: 全体スケジュール遅延
**確率**: 中
**対策**:
- シンプルなUIから開始
- Backend先行完成
- MVP定義の明確化

---

## 📦 成果物

### コード

**Backend**:
- `orchestrator/api/dialogue_ws.py` - WebSocketエンドポイント
- `orchestrator/monitors/dialogue_monitor.py` - ファイル監視
- `tests/test_dialogue_ws.py` - テスト

**Frontend**:
- `dashboard/src/components/DialogueView.tsx` - 対話ビュー
- `dashboard/src/components/DialogueMessage.tsx` - メッセージ
- `dashboard/src/hooks/useWebSocket.ts` - WebSocketフック
- `dashboard/src/tests/DialogueView.test.tsx` - テスト

### テスト
- ユニットテスト（カバレッジ > 80%）
- 統合テスト
- E2Eテスト（Playwright/Cypress）
- パフォーマンステスト結果

### ドキュメント
- API仕様書（OpenAPI）
- ユーザーガイド更新
- 開発者ガイド
- トラブルシューティングガイド

---

## 🎯 成功の定義

この機能は以下がすべて達成されたときに「完成」とみなされる：

1. ✅ ユーザーがWebダッシュボードからAI対話をリアルタイムで見られる
2. ✅ 8ワーカー同時実行でもスムーズに動作する
3. ✅ すべての自動テストが合格する
4. ✅ ドキュメントが完備されている
5. ✅ ユーザーフィードバックが肯定的（80%以上満足）

---

## 📊 進捗トラッキング

### Day 1
- [ ] WebSocketエンドポイント実装
- [ ] DialogueMonitor実装
- [ ] 複数ワーカー対応
- [ ] Backendテスト

### Day 2
- [ ] WebSocketクライアント実装
- [ ] 対話メッセージコンポーネント
- [ ] 対話ビューコンポーネント
- [ ] ワーカーリストコンポーネント

### Day 3
- [ ] 統合テスト
- [ ] パフォーマンステスト
- [ ] UI/UX改善
- [ ] ドキュメント作成

**進捗率**: 0% → 100%

---

## 📝 Notes

- 実装中に気づいたことをここに記録
- 技術的な決定事項
- 変更が必要になった要件

---

**作成日**: 2025-10-23
**最終更新**: 2025-10-23
**ステータス**: Draft → Ready → In Progress → Review → Done
**担当者**: TBD
