# App.tsx Integration Guide - Worker Status Dashboard

## 統合完了版のApp.tsx

以下のコードをApp.tsxに適用することで、Worker Status Dashboardが完全に統合されます。

```typescript
/**
 * Main Application Component
 *
 * Entry point for the Dialogue Visualization Frontend
 *
 * Features:
 * - Multi-worker selection
 * - Real-time dialogue monitoring
 * - Worker status dashboard (NEW)
 * - Responsive layout
 */

import { useState } from 'react';
import { DialogueView } from './components/DialogueView';
import { WorkerSelector } from './components/WorkerSelector';
import { TerminalGridLayout } from './components/TerminalGridLayout';
import { MetricsDashboard } from './components/MetricsDashboard';
import { WorkerStatusDashboard } from './components/WorkerStatusDashboard';
import './App.css';

type ViewMode = 'worker-status' | 'dialogue' | 'terminal' | 'metrics';

function App() {
  const [selectedWorkerId, setSelectedWorkerId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('worker-status');
  const [allWorkerIds, setAllWorkerIds] = useState<string[]>([]);

  const handleWorkerCardClick = (workerId: string) => {
    setSelectedWorkerId(workerId);
    setViewMode('dialogue');
  };

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-4">
        <div className="max-w-full mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">
              AI Parallel Coding - Monitor
            </h1>
            <p className="text-gray-400 text-sm mt-1">
              Real-time worker monitoring and communication
            </p>
          </div>

          {/* View Mode Toggle */}
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('worker-status')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                viewMode === 'worker-status'
                  ? 'bg-orange-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              ⚡ Worker Status
            </button>
            <button
              onClick={() => setViewMode('dialogue')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                viewMode === 'dialogue'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              📝 Dialogue
            </button>
            <button
              onClick={() => setViewMode('terminal')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                viewMode === 'terminal'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              💻 Terminal
            </button>
            <button
              onClick={() => setViewMode('metrics')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                viewMode === 'metrics'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              📊 Metrics
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Only show for dialogue/terminal views */}
        {viewMode !== 'worker-status' && viewMode !== 'metrics' && (
          <aside className="w-80 bg-gray-900 border-r border-gray-800 overflow-y-auto custom-scrollbar">
            <div className="p-4">
              <WorkerSelector
                selectedWorkerId={selectedWorkerId}
                onWorkerSelect={setSelectedWorkerId}
                onWorkersChange={setAllWorkerIds}
              />
            </div>
          </aside>
        )}

        {/* Right Panel - Content View */}
        <div className="flex-1 overflow-hidden">
          {viewMode === 'worker-status' ? (
            <div className="h-full p-6 overflow-y-auto custom-scrollbar">
              <WorkerStatusDashboard onWorkerClick={handleWorkerCardClick} />
            </div>
          ) : viewMode === 'dialogue' ? (
            selectedWorkerId ? (
              <div className="h-full p-6">
                <DialogueView workerId={selectedWorkerId} className="h-full" />
              </div>
            ) : (
              <div className="h-full flex items-center justify-center p-6">
                <div className="text-center text-gray-400">
                  <div className="text-6xl mb-4">👈</div>
                  <div className="text-xl font-semibold mb-2">Select a Worker</div>
                  <div className="text-sm text-gray-500">
                    Choose a worker from the left panel or Worker Status dashboard
                  </div>
                </div>
              </div>
            )
          ) : viewMode === 'terminal' ? (
            allWorkerIds.length > 0 ? (
              <TerminalGridLayout workerIds={allWorkerIds} />
            ) : (
              <div className="h-full flex items-center justify-center p-6">
                <div className="text-center text-gray-400">
                  <div className="text-6xl mb-4">👈</div>
                  <div className="text-xl font-semibold mb-2">No Workers Found</div>
                  <div className="text-sm text-gray-500">
                    Start a worker to view terminal output
                  </div>
                </div>
              </div>
            )
          ) : (
            <div className="h-full">
              <MetricsDashboard />
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 border-t border-gray-800 px-6 py-3">
        <div className="max-w-full mx-auto text-center text-sm text-gray-500">
          <p>Powered by FastAPI + WebSocket | React + TypeScript + Vite</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
```

## 変更点の説明

### 1. Import追加
```typescript
import { WorkerStatusDashboard } from './components/WorkerStatusDashboard';
```

### 2. ViewMode型の拡張
```typescript
type ViewMode = 'worker-status' | 'dialogue' | 'terminal' | 'metrics';
```
- `'worker-status'`を追加（最初に配置）

### 3. デフォルトviewModeの変更
```typescript
const [viewMode, setViewMode] = useState<ViewMode>('worker-status');
```
- 起動時にWorker Status Dashboardを表示

### 4. Worker カードクリックハンドラー
```typescript
const handleWorkerCardClick = (workerId: string) => {
  setSelectedWorkerId(workerId);
  setViewMode('dialogue');
};
```
- Worker Status Dashboardからワーカーをクリックすると、自動的にDialogue Viewに遷移

### 5. ナビゲーションボタンの追加
```typescript
<button
  onClick={() => setViewMode('worker-status')}
  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
    viewMode === 'worker-status'
      ? 'bg-orange-600 text-white'
      : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
  }`}
>
  ⚡ Worker Status
</button>
```
- オレンジ色のボタン（`bg-orange-600`）
- ⚡アイコン

### 6. サイドバーの条件付き表示
```typescript
{viewMode !== 'worker-status' && viewMode !== 'metrics' && (
  <aside className="w-80 bg-gray-900 border-r border-gray-800 overflow-y-auto custom-scrollbar">
    ...
  </aside>
)}
```
- Worker StatusとMetricsビューではサイドバーを非表示
- 全画面を利用

### 7. Worker Status Dashboard のマウント
```typescript
{viewMode === 'worker-status' ? (
  <div className="h-full p-6 overflow-y-auto custom-scrollbar">
    <WorkerStatusDashboard onWorkerClick={handleWorkerCardClick} />
  </div>
) : ...}
```
- パディングとスクロールサポート付き
- クリックハンドラーを渡してDialogue Viewへの遷移を実現

## 統合後の動作フロー

1. **起動時**: Worker Status Dashboardが表示される
2. **ワーカーカードクリック**: 自動的にDialogue Viewに遷移し、そのワーカーの対話が表示される
3. **ナビゲーション**: 4つのビュー間を自由に切り替え可能
4. **レイアウト**: Worker StatusとMetricsは全画面、DialogueとTerminalは2カラム

## 動作確認手順

1. Frontend開発サーバー起動
   ```bash
   cd frontend && npm run dev
   ```

2. Backend API起動
   ```bash
   python -m uvicorn orchestrator.api.main:app --reload --port 8000
   ```

3. ブラウザで確認
   - http://localhost:5173/
   - Worker Status Dashboardが表示されることを確認
   - ナビゲーションボタンが4つ表示されることを確認
   - 各ビューに切り替わることを確認

## トラブルシューティング

### Vite HMRが反応しない場合
```bash
# Frontend開発サーバーを再起動
cd frontend
npm run dev
```

### TypeScriptエラーが出る場合
```bash
# 型チェック
cd frontend
npm run type-check
```

### コンポーネントが見つからない場合
```bash
# ファイルが存在することを確認
ls -la src/components/WorkerStatus*.tsx
ls -la src/hooks/useWorkerStatus*.ts
ls -la src/types/worker-status.ts
```

## 次のステップ

1. ✅ App.tsx統合完了
2. ⏭️ ブラウザで動作確認
3. ⏭️ スクリーンショット取得
4. ⏭️ 統合テストの実装
5. ⏭️ Git commit

---

**統合完了日**: 2025-10-24
**Milestone**: 1.3 - Worker Status UI完全統合
