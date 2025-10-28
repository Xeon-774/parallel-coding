# Ecosystem Dashboard Architecture - 統合ダッシュボード設計

**作成日**: 2025-10-24
**ステータス**: 🚧 **設計中**
**優先度**: 🔴 **最高**

---

## 🎯 コンセプト

**AI_Investor エコシステム全体を1つのダッシュボードで管理する統合プラットフォーム**

---

## 🏗️ エコシステム全体像

```
┌─────────────────────────────────────────────────────────────────┐
│  AI_Investor Ecosystem Dashboard                                │
│  http://localhost:3000/ ★統合ダッシュボード★                   │
│                                                                  │
│  ┌────────────────┬────────────────┬────────────────┐          │
│  │ Parallel Coder │ Manager AI     │ MT4 Integration│          │
│  │ Status         │ Status         │ Status         │          │
│  └────────────────┴────────────────┴────────────────┘          │
│                                                                  │
│  Navigation:                                                     │
│  [🤖 Parallel Coding] [👁️ Manager AI] [📈 MT4] [💹 Trading]   │
└─────────────────────────────────────────────────────────────────┘
         │                    │                │
         ▼                    ▼                ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
│ Parallel Coding  │  │ Manager AI   │  │ MT4 App      │
│ App              │  │ (統合)       │  │ (将来)       │
│ localhost:5173   │  │ (統合)       │  │ localhost:??? │
│ ★既存★          │  │ ★新規★      │  │              │
└──────────────────┘  └──────────────┘  └──────────────┘
```

---

## 📊 実装方針

### オプション1: Micro-Frontend (推奨) ⭐

各アプリは独立したフロントエンドを持ち、エコシステムダッシュボードが統合。

```
ecosystem-dashboard/ (Port 3000)
├── src/
│   ├── App.tsx                    # メインダッシュボード
│   ├── components/
│   │   ├── EcosystemOverview.tsx  # 全体概要
│   │   ├── AppSelector.tsx        # アプリ切替
│   │   └── StatusCards.tsx        # 各アプリのステータスカード
│   │
│   └── integrations/              # 各アプリ統合
│       ├── ParallelCodingFrame.tsx  # iframe or Module Federation
│       ├── ManagerAIFrame.tsx
│       └── MT4Frame.tsx
│
└── package.json

parallel-coding/frontend/ (Port 5173)
├── ★既存のフロントエンド★
└── 独立して動作可能

mt4-integration/frontend/ (Port 5174)
└── 将来実装
```

**技術スタック**:
- **Module Federation** (Webpack 5) - 推奨
- iframe (シンプルだが制約あり)
- Single-SPA (マイクロフロントエンド専用)

**メリット**:
- ✅ 各アプリが完全に独立
- ✅ 異なるReactバージョンも可能
- ✅ 独立したデプロイ
- ✅ 段階的な実装が可能

**デメリット**:
- ⚠️ 若干の複雑さ
- ⚠️ Module Federation の学習コスト

---

### オプション2: Monorepo (Alternative)

全てのフロントエンドを1つのプロジェクトに統合。

```
frontend/ (Port 3000)
├── src/
│   ├── App.tsx                    # ルーティング
│   ├── pages/
│   │   ├── Dashboard.tsx          # エコシステム概要
│   │   ├── ParallelCoding/        # 並列コーダー
│   │   ├── ManagerAI/             # Manager AI
│   │   └── MT4/                   # MT4連携
│   │
│   └── components/
│       └── shared/                # 共通コンポーネント
│
└── package.json (統一)
```

**メリット**:
- ✅ シンプル
- ✅ コンポーネント共有が容易
- ✅ 統一されたビルド

**デメリット**:
- ⚠️ 全てが密結合
- ⚠️ デプロイが一括のみ
- ⚠️ 大規模化すると遅い

---

## 🎯 推奨: Micro-Frontend (Module Federation)

### 理由

1. **並列モノリスの理念に合致**
   - 各アプリは独立
   - ダッシュボードは統合

2. **段階的実装が可能**
   - 既存のparallel-codingはそのまま
   - 新しいアプリを追加していく

3. **技術的柔軟性**
   - 各アプリが独自の技術スタック使用可能

---

## 📐 Micro-Frontend実装設計

### Ecosystem Dashboard (Port 3000)

```typescript
// ecosystem-dashboard/src/App.tsx
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

// Dynamic imports from remote apps
const ParallelCodingApp = React.lazy(() =>
  import('parallelCoding/App')  // Module Federation
);
const ManagerAIView = React.lazy(() =>
  import('parallelCoding/ManagerAI')  // Manager AIは統合済み
);

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <EcosystemNav />

      <Routes>
        <Route path="/" element={<EcosystemDashboard />} />
        <Route path="/parallel-coding/*" element={
          <React.Suspense fallback={<Loading />}>
            <ParallelCodingApp />
          </React.Suspense>
        } />
        <Route path="/manager-ai/*" element={
          <React.Suspense fallback={<Loading />}>
            <ManagerAIView />
          </React.Suspense>
        } />
        <Route path="/mt4/*" element={<ComingSoon />} />
      </Routes>
    </BrowserRouter>
  );
};
```

### Webpack Module Federation設定

```javascript
// ecosystem-dashboard/webpack.config.js
module.exports = {
  plugins: [
    new ModuleFederationPlugin({
      name: 'ecosystem',
      remotes: {
        parallelCoding: 'parallelCoding@http://localhost:5173/remoteEntry.js',
        // 将来追加
        // mt4: 'mt4@http://localhost:5174/remoteEntry.js',
      },
      shared: {
        react: { singleton: true },
        'react-dom': { singleton: true },
      },
    }),
  ],
};

// parallel-coding/frontend/webpack.config.js
module.exports = {
  plugins: [
    new ModuleFederationPlugin({
      name: 'parallelCoding',
      filename: 'remoteEntry.js',
      exposes: {
        './App': './src/App',
        './ManagerAI': './src/components/ManagerAI/ManagerAIDashboard',
        './WorkerStatus': './src/components/WorkerStatus/WorkerStatusDashboard',
      },
      shared: {
        react: { singleton: true },
        'react-dom': { singleton: true },
      },
    }),
  ],
};
```

---

## 🎨 UI/UX設計

### Ecosystem Dashboard メイン画面

```
┌─────────────────────────────────────────────────────────────┐
│ 🏠 AI_Investor Ecosystem                          [⚙️ Settings] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 System Overview                                          │
│  ┌──────────────┬──────────────┬──────────────┬───────────┐│
│  │ 🤖 Parallel  │ 👁️ Manager   │ 📈 MT4       │ 💹 Trading││
│  │ Coding       │ AI           │ Integration  │ Dashboard ││
│  │              │              │              │           ││
│  │ ✅ Active    │ ✅ Monitoring│ ⏳ Coming    │ ⏳ Coming ││
│  │ 3 Workers    │ 1 Session    │ Soon         │ Soon      ││
│  │ 2h runtime   │ 24h uptime   │              │           ││
│  └──────────────┴──────────────┴──────────────┴───────────┘│
│                                                              │
│  🔔 Recent Activities                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ [15:32] Parallel Coding: Worker #2 completed task    │  │
│  │ [15:30] Manager AI: Auto-approved file write         │  │
│  │ [15:28] Parallel Coding: Worker #1 started           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  📈 Performance Metrics (24h)                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ [Graph: CPU, Memory, API calls across all apps]      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  [🤖 Open Parallel Coding] [👁️ Open Manager AI]            │
└─────────────────────────────────────────────────────────────┘
```

### Navigation Bar (全ページ共通)

```
┌─────────────────────────────────────────────────────────────┐
│ 🏠 [Home] | 🤖 [Parallel] | 👁️ [Manager] | 📈 [MT4] | 💹 [Trade] │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 Backend統合

### API Gateway Pattern

```
┌─────────────────────────────────────────────────────────┐
│  API Gateway (Port 8000)                                │
│  /api/v1/                                               │
│    ├─ /parallel-coding/*    → localhost:8001           │
│    ├─ /manager-ai/*         → localhost:8001 (統合)   │
│    ├─ /mt4/*                → localhost:8002 (将来)   │
│    └─ /ecosystem/status     → 全体ステータス集約      │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 ディレクトリ構造 (最終形)

```
AI_Investor/
├── ecosystem-dashboard/          # ★新規: 統合ダッシュボード
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── EcosystemOverview.tsx
│   │   │   ├── ActivityFeed.tsx
│   │   │   └── PerformanceMetrics.tsx
│   │   └── integrations/
│   │       └── (Module Federation remotes)
│   ├── package.json
│   └── webpack.config.js
│
├── tools/
│   └── parallel-coding/          # 既存: 拡張
│       ├── orchestrator/
│       │   ├── core/
│       │   │   ├── common/       # ★新規: 共通コンポーネント
│       │   │   │   ├── ai_safety_judge.py
│       │   │   │   ├── metrics.py
│       │   │   │   └── base_manager.py
│       │   │   ├── worker/       # ★新規: Worker専用
│       │   │   │   └── worker_manager.py
│       │   │   └── supervisor/   # ★新規: Manager AI
│       │   │       ├── supervisor_manager.py
│       │   │       └── claude_monitor.py
│       │   └── api/
│       │       ├── worker_api.py
│       │       └── supervisor_api.py
│       │
│       └── frontend/              # 既存: 拡張
│           ├── src/
│           │   ├── App.tsx        # Module Federation対応
│           │   ├── components/
│           │   │   ├── worker/    # Worker関連
│           │   │   └── supervisor/ # ★新規: Manager AI関連
│           │   └── views/
│           │       ├── WorkerView.tsx
│           │       └── SupervisorView.tsx # ★新規
│           └── webpack.config.js  # Module Federation設定
│
└── apps/                          # 将来の他アプリ
    ├── mt4-integration/
    ├── trading-dashboard/
    └── backtesting-engine/
```

---

## ⏱️ 実装タイムライン

### Week 0: Parallel Coding リファクタリング (20h)

1. **モジュール分離** (8h)
   - common/, worker/, supervisor/ 作成
   - 既存コード移動

2. **BaseAIManager実装** (6h)
   - 共通基底クラス
   - Worker/Supervisor継承

3. **Module Federation対応** (4h)
   - Webpack設定
   - Expose設定

4. **ロードマップ更新** (2h)

### Week 1: Ecosystem Dashboard作成 (15h)

1. **プロジェクト作成** (3h)
   - Vite + React + TypeScript
   - Module Federation設定

2. **統合ダッシュボードUI** (8h)
   - EcosystemOverview
   - ActivityFeed
   - PerformanceMetrics

3. **Navigation統合** (4h)
   - ルーティング
   - Remote app loading

### Week 2-3: Manager AI実装 (60h)

*(既存計画通り)*

### Week 4: Production準備 (25h)

*(既存計画通り)*

---

## 🎯 次のステップ

1. ✅ **アーキテクチャ決定完了**
2. 🚧 **Week 0開始**: リファクタリング
3. ⏳ **Week 1**: Ecosystem Dashboard
4. ⏳ **Week 2-3**: Manager AI実装
5. ⏳ **Week 4**: Production

---

**作成者**: Claude (Sonnet 4.5)
**ステータス**: 🚧 実装準備完了
**開始**: 今すぐ ✅
