# ハイブリッドエンジンメトリクスダッシュボード - 詳細ロードマップ

**機能名**: ハイブリッドエンジン決定統計のリアルタイム表示
**優先度**: 🔴 最高
**期間**: 2日
**担当**: Backend + Frontend
**Phase**: 1.2

---

## 📋 概要

### 目的
ハイブリッドエンジンの決定統計をリアルタイムでダッシュボードに表示し、システムのパフォーマンスと動作を可視化する。ユーザーがルールベース決定とAI判断のバランス、レスポンスタイム、フォールバック率などを即座に把握できるようにする。

### 現状と問題点

**現状**:
- ✅ ハイブリッドエンジンは完全実装済み
- ✅ 統計収集機能あり（`hybrid_engine.get_stats()`）
- ✅ 以下のメトリクスを追跡：
  ```python
  {
      'total_decisions': 6,
      'rules_decisions': 5,
      'ai_decisions': 1,
      'template_fallbacks': 0,
      'average_latency_ms': 1234.5,
      'rules_percentage': 83.3
  }
  ```

**問題点**:
- ❌ 統計はPython出力でしか見られない
- ❌ リアルタイムで変化が見えない
- ❌ 決定履歴が追跡できない
- ❌ トレンド分析ができない
- ❌ アラート機能がない

### 期待される成果

**ユーザー体験**:
```
ダッシュボードを開くと：
1. リアルタイムメトリクスカードが表示される
   - 総決定数
   - ルール決定比率（円グラフ）
   - AI決定比率
   - フォールバック率
   - 平均レスポンス時間

2. レスポンスタイム分布グラフ
   - ヒストグラム
   - ルール（<1ms）とAI（~7s）の分布

3. 決定履歴テーブル
   - 最新100件
   - フィルタリング可能
   - 詳細表示

4. トレンドグラフ（過去24時間）
   - 決定数の推移
   - レスポンスタイムの推移
   - フォールバック率の推移

5. アラート表示
   - フォールバック率 > 10%
   - 平均レスポンス > 10s
   - エラー率 > 5%
```

---

## 🏗️ 技術設計

### アーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│                  Web Dashboard                      │
│  ┌──────────────────────────────────────────────┐  │
│  │         Metrics Dashboard Component          │  │
│  │  ┌────────────┐  ┌────────────┐             │  │
│  │  │ Real-time  │  │ Historical │             │  │
│  │  │ Metrics    │  │ Trends     │             │  │
│  │  └────────────┘  └────────────┘             │  │
│  │  ┌────────────┐  ┌────────────┐             │  │
│  │  │ Decision   │  │ Alert      │             │  │
│  │  │ History    │  │ Panel      │             │  │
│  │  └────────────┘  └────────────┘             │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                    ↕ REST API + WebSocket
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend                        │
│  ┌──────────────────────────────────────────────┐  │
│  │  GET /api/metrics/current                    │  │
│  │  GET /api/metrics/history?range=24h          │  │
│  │  GET /api/decisions/recent?limit=100         │  │
│  │  WS /ws/metrics (リアルタイム配信)            │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  MetricsCollector                            │  │
│  │  - 決定イベント収集                           │  │
│  │  - 統計計算                                   │  │
│  │  - 履歴保存（TimescaleDB/SQLite）            │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                        ↕ Hook
┌─────────────────────────────────────────────────────┐
│         Hybrid Engine Integration                   │
│  hybrid_engine.decide() が呼ばれるたびに            │
│  MetricsCollector にイベント送信                    │
└─────────────────────────────────────────────────────┘
```

### データモデル

**Decision Event**:
```python
@dataclass
class DecisionEvent:
    timestamp: float
    worker_id: str
    decision_type: str  # "approve" or "deny"
    decided_by: str     # "rules", "ai", "template"
    latency_ms: float
    is_fallback: bool
    confirmation_type: str  # "file_write", "file_delete", etc.
    reasoning: str
```

**Metrics Snapshot**:
```python
@dataclass
class MetricsSnapshot:
    timestamp: float
    total_decisions: int
    rules_decisions: int
    ai_decisions: int
    template_fallbacks: int
    average_latency_ms: float
    rules_percentage: float
    ai_percentage: float
    fallback_percentage: float
```

### データフロー

```
1. hybrid_engine.decide() が決定を下す
   ↓
2. MetricsCollector.record_decision(event) を呼び出し
   ↓
3. イベントをデータベースに保存
   ↓
4. リアルタイム統計を更新
   ↓
5. WebSocket経由でフロントエンドに配信
   ↓
6. ダッシュボードが即座に更新
```

---

## 📅 実装計画（2日間）

### Day 1: Backend実装（8時間）

**午前（4時間）**:
- [ ] MetricsCollectorクラス実装
  - イベント収集ロジック
  - 統計計算
  - データベーススキーマ設計
  - SQLite実装（シンプル化）

**午後（4時間）**:
- [ ] REST APIエンドポイント実装
  - GET /api/metrics/current
  - GET /api/metrics/history
  - GET /api/decisions/recent
- [ ] WebSocketエンドポイント
  - リアルタイムメトリクス配信
  - イベント駆動型更新

**成果物**:
```python
# orchestrator/metrics/collector.py
from dataclasses import dataclass
from typing import List
import sqlite3
import time

@dataclass
class DecisionEvent:
    timestamp: float
    worker_id: str
    decision_type: str
    decided_by: str
    latency_ms: float
    is_fallback: bool
    confirmation_type: str
    reasoning: str

class MetricsCollector:
    def __init__(self, db_path: str = "metrics.db"):
        self.db_path = db_path
        self._init_db()
        self.listeners = []  # WebSocket listeners

    def _init_db(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                worker_id TEXT,
                decision_type TEXT,
                decided_by TEXT,
                latency_ms REAL,
                is_fallback INTEGER,
                confirmation_type TEXT,
                reasoning TEXT
            )
        """)
        conn.commit()
        conn.close()

    def record_decision(self, event: DecisionEvent):
        """決定イベントを記録"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO decisions
            (timestamp, worker_id, decision_type, decided_by,
             latency_ms, is_fallback, confirmation_type, reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.timestamp, event.worker_id, event.decision_type,
            event.decided_by, event.latency_ms, int(event.is_fallback),
            event.confirmation_type, event.reasoning
        ))
        conn.commit()
        conn.close()

        # WebSocketリスナーに通知
        self._notify_listeners(event)

    def get_current_metrics(self) -> dict:
        """現在のメトリクス取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 総決定数
        cursor.execute("SELECT COUNT(*) FROM decisions")
        total = cursor.fetchone()[0]

        # 決定タイプ別カウント
        cursor.execute("""
            SELECT decided_by, COUNT(*)
            FROM decisions
            GROUP BY decided_by
        """)
        counts = dict(cursor.fetchall())

        # 平均レイテンシー
        cursor.execute("SELECT AVG(latency_ms) FROM decisions")
        avg_latency = cursor.fetchone()[0] or 0

        conn.close()

        rules_count = counts.get('rules', 0)
        ai_count = counts.get('ai', 0)
        template_count = counts.get('template', 0)

        return {
            'total_decisions': total,
            'rules_decisions': rules_count,
            'ai_decisions': ai_count,
            'template_fallbacks': template_count,
            'average_latency_ms': avg_latency,
            'rules_percentage': (rules_count / total * 100) if total > 0 else 0
        }

    def get_recent_decisions(self, limit: int = 100) -> List[dict]:
        """最近の決定履歴取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM decisions
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'timestamp': row[1],
                'worker_id': row[2],
                'decision_type': row[3],
                'decided_by': row[4],
                'latency_ms': row[5],
                'is_fallback': bool(row[6]),
                'confirmation_type': row[7],
                'reasoning': row[8]
            }
            for row in rows
        ]

# orchestrator/api/metrics.py
from fastapi import APIRouter
from orchestrator.metrics.collector import MetricsCollector

router = APIRouter()
collector = MetricsCollector()

@router.get("/api/metrics/current")
async def get_current_metrics():
    return collector.get_current_metrics()

@router.get("/api/decisions/recent")
async def get_recent_decisions(limit: int = 100):
    return collector.get_recent_decisions(limit)

@router.websocket("/ws/metrics")
async def metrics_websocket(websocket: WebSocket):
    await websocket.accept()

    # リスナー登録
    async def listener(event):
        await websocket.send_json({
            'type': 'decision',
            'data': event.__dict__
        })

    collector.listeners.append(listener)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        collector.listeners.remove(listener)
```

---

### Day 2: Frontend実装とテスト（8時間）

**午前（4時間）**:
- [ ] メトリクスカードコンポーネント
  - リアルタイムメトリクス表示
  - 円グラフ（Chart.js/Recharts）
  - カウンターアニメーション

- [ ] 決定履歴テーブル
  - テーブル表示
  - ソート・フィルター
  - ページネーション

**午後（4時間）**:
- [ ] トレンドグラフコンポーネント
  - 時系列グラフ
  - 24時間/7日間表示切替

- [ ] 統合テスト
  - E2Eテスト
  - パフォーマンス確認
  - UI/UX調整

**成果物**:
```tsx
// components/MetricsDashboard.tsx
import { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { PieChart, Pie, Cell, LineChart, Line } from 'recharts';

interface Metrics {
  total_decisions: number;
  rules_decisions: number;
  ai_decisions: number;
  template_fallbacks: number;
  average_latency_ms: number;
  rules_percentage: number;
}

export function MetricsDashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const { messages } = useWebSocket('ws://localhost:8000/ws/metrics');

  useEffect(() => {
    // 初期メトリクス取得
    fetch('/api/metrics/current')
      .then(res => res.json())
      .then(data => setMetrics(data));
  }, []);

  useEffect(() => {
    // リアルタイム更新
    if (messages.length > 0) {
      // メトリクス再取得
      fetch('/api/metrics/current')
        .then(res => res.json())
        .then(data => setMetrics(data));
    }
  }, [messages]);

  if (!metrics) return <div>Loading...</div>;

  const pieData = [
    { name: 'Rules', value: metrics.rules_decisions, color: '#10b981' },
    { name: 'AI', value: metrics.ai_decisions, color: '#3b82f6' },
    { name: 'Template', value: metrics.template_fallbacks, color: '#f59e0b' }
  ];

  return (
    <div className="metrics-dashboard">
      {/* メトリクスカード */}
      <div className="metrics-cards">
        <MetricCard
          title="Total Decisions"
          value={metrics.total_decisions}
          icon="📊"
        />
        <MetricCard
          title="Avg Response Time"
          value={`${metrics.average_latency_ms.toFixed(1)}ms`}
          icon="⏱️"
        />
        <MetricCard
          title="Rules Efficiency"
          value={`${metrics.rules_percentage.toFixed(1)}%`}
          icon="⚡"
          trend={metrics.rules_percentage > 80 ? 'up' : 'down'}
        />
      </div>

      {/* 円グラフ */}
      <div className="decision-distribution">
        <h3>Decision Distribution</h3>
        <PieChart width={300} height={300}>
          <Pie
            data={pieData}
            cx={150}
            cy={150}
            outerRadius={80}
            label
            dataKey="value"
          >
            {pieData.map((entry, index) => (
              <Cell key={index} fill={entry.color} />
            ))}
          </Pie>
        </PieChart>
        <div className="legend">
          {pieData.map(item => (
            <div key={item.name} className="legend-item">
              <span style={{ color: item.color }}>●</span>
              {item.name}: {item.value}
            </div>
          ))}
        </div>
      </div>

      {/* 決定履歴テーブル */}
      <DecisionHistoryTable />
    </div>
  );
}

function MetricCard({ title, value, icon, trend }: any) {
  return (
    <div className="metric-card">
      <div className="metric-icon">{icon}</div>
      <div className="metric-content">
        <h4>{title}</h4>
        <div className="metric-value">
          {value}
          {trend && (
            <span className={`trend ${trend}`}>
              {trend === 'up' ? '↑' : '↓'}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function DecisionHistoryTable() {
  const [decisions, setDecisions] = useState([]);

  useEffect(() => {
    fetch('/api/decisions/recent?limit=100')
      .then(res => res.json())
      .then(data => setDecisions(data));
  }, []);

  return (
    <div className="decision-history">
      <h3>Recent Decisions</h3>
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Worker</th>
            <th>Type</th>
            <th>Decided By</th>
            <th>Latency</th>
            <th>Result</th>
          </tr>
        </thead>
        <tbody>
          {decisions.map((dec: any, idx: number) => (
            <tr key={idx}>
              <td>{new Date(dec.timestamp * 1000).toLocaleTimeString()}</td>
              <td>{dec.worker_id}</td>
              <td>{dec.confirmation_type}</td>
              <td>
                <span className={`badge ${dec.decided_by}`}>
                  {dec.decided_by}
                </span>
              </td>
              <td>{dec.latency_ms.toFixed(1)}ms</td>
              <td>
                <span className={`result ${dec.decision_type}`}>
                  {dec.decision_type}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## ✅ タスク分解（詳細）

### Backend Tasks

- [ ] **MetricsCollectorクラス実装** (3時間)
  - データベーススキーマ設計
  - イベント記録ロジック
  - 統計計算ロジック
  - WebSocketリスナー管理

- [ ] **REST APIエンドポイント** (2時間)
  - GET /api/metrics/current
  - GET /api/decisions/recent
  - クエリパラメータ処理

- [ ] **WebSocketエンドポイント** (1時間)
  - リアルタイム配信
  - イベント駆動型更新

- [ ] **Hybrid Engine統合** (2時間)
  - decide()メソッドにフック追加
  - イベント送信ロジック
  - エラーハンドリング

### Frontend Tasks

- [ ] **メトリクスカードコンポーネント** (2時間)
  - カード表示
  - カウンターアニメーション
  - トレンドインジケーター

- [ ] **円グラフコンポーネント** (2時間)
  - Chart.js/Recharts統合
  - レジェンド表示
  - レスポンシブ対応

- [ ] **決定履歴テーブル** (2時間)
  - テーブル表示
  - ソート機能
  - フィルター機能

- [ ] **統合とテスト** (2時間)
  - E2Eテスト
  - パフォーマンステスト
  - UI/UX最終調整

---

## 🧪 検証基準

### 機能検証

**基本機能**:
- ✅ リアルタイムでメトリクスが更新される
- ✅ 決定履歴が正しく表示される
- ✅ 円グラフが正確なデータを表示
- ✅ フィルタリングが動作する

**高度な機能**:
- ✅ WebSocket接続が安定
- ✅ データベースパフォーマンスが良好
- ✅ アラート機能が動作
- ✅ 履歴データをエクスポートできる

### パフォーマンス検証

**レスポンステスト**:
- ✅ API応答時間 < 100ms
- ✅ メトリクス更新レイテンシー < 200ms
- ✅ 10,000決定記録でもスムーズ動作

**負荷テスト**:
- ✅ 100 decisions/秒でもパフォーマンス維持
- ✅ データベースサイズ制限（1GB以下）
- ✅ メモリ使用量 < 500MB

### 自動テスト

```python
# tests/test_metrics_collector.py
def test_record_decision():
    collector = MetricsCollector(":memory:")

    event = DecisionEvent(
        timestamp=time.time(),
        worker_id="worker_001",
        decision_type="approve",
        decided_by="rules",
        latency_ms=0.5,
        is_fallback=False,
        confirmation_type="file_write",
        reasoning="Safe operation"
    )

    collector.record_decision(event)

    metrics = collector.get_current_metrics()
    assert metrics['total_decisions'] == 1
    assert metrics['rules_decisions'] == 1

def test_get_recent_decisions():
    collector = MetricsCollector(":memory:")

    # 10個の決定を記録
    for i in range(10):
        collector.record_decision(...)

    recent = collector.get_recent_decisions(limit=5)
    assert len(recent) == 5
```

---

## 🔗 依存関係

### 前提条件
- ✅ Hybrid Engine実装 - **完了**
- ✅ FastAPI backend - **要確認**
- ✅ SQLite - **標準ライブラリ**
- ✅ Chart.js または Recharts - **要インストール**

### ブロッカー
- ❌ なし

### 並行作業可能な項目
- ✅ AI対話可視化（別機能）
- ✅ ワーカー状態表示（別機能）

---

## ⚠️ リスクと対策

### リスク1: データベースパフォーマンス
**影響**: 大量決定でDB肥大化
**確率**: 中
**対策**:
- 古いデータの自動削除（30日以上）
- インデックス最適化
- 必要に応じてTimescaleDB検討

### リスク2: WebSocket接続の不安定性
**影響**: リアルタイム更新が途切れる
**確率**: 低
**対策**:
- 自動再接続
- ポーリングフォールバック
- 接続状態表示

### リスク3: グラフ描画のパフォーマンス
**影響**: 大量データでUIがラグる
**確率**: 低
**対策**:
- データポイント間引き
- 仮想化
- WebWorker使用

---

## 📦 成果物

### コード
- `orchestrator/metrics/collector.py` - メトリクス収集
- `orchestrator/api/metrics.py` - REST/WebSocket API
- `dashboard/src/components/MetricsDashboard.tsx` - ダッシュボード
- `tests/test_metrics_*.py` - テスト

### データベース
- `metrics.db` - SQLiteデータベース
- スキーマ定義SQL

### テスト
- ユニットテスト（カバレッジ > 80%）
- 統合テスト
- パフォーマンステスト結果

### ドキュメント
- メトリクスAPI仕様
- ユーザーガイド更新
- トラブルシューティング

---

## 🎯 成功の定義

1. ✅ リアルタイムでメトリクスが表示される
2. ✅ 決定の分布と傾向が明確に見える
3. ✅ パフォーマンス基準を満たす
4. ✅ すべてのテストが合格する
5. ✅ ドキュメントが完備されている

---

## 📊 進捗トラッキング

### Day 1
- [ ] MetricsCollector実装
- [ ] REST API実装
- [ ] WebSocket実装
- [ ] Hybrid Engine統合

### Day 2
- [ ] メトリクスカード実装
- [ ] 円グラフ実装
- [ ] 決定履歴テーブル実装
- [ ] 統合テスト

**進捗率**: 0% → 100%

---

**作成日**: 2025-10-23
**ステータス**: Draft
**担当者**: TBD
