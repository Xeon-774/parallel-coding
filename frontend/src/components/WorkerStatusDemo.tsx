/**
 * WorkerStatusDemo Component
 *
 * Standalone demo page for testing the Worker Status Dashboard.
 * This can be integrated into App.tsx as a new view mode.
 *
 * Usage:
 *   Import and use in App.tsx:
 *   import { WorkerStatusDemo } from './components/WorkerStatusDemo';
 *
 *   Then add to view modes:
 *   <WorkerStatusDemo />
 */

import { WorkerStatusDashboard } from './WorkerStatusDashboard';

export function WorkerStatusDemo() {
  return (
    <div className="min-h-screen bg-gray-950 p-6">
      <div className="max-w-screen-2xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">
            Worker Status Dashboard
          </h1>
          <p className="text-gray-400">
            Real-time monitoring of all AI coding workers
          </p>
        </div>

        {/* Dashboard */}
        <WorkerStatusDashboard
          onWorkerClick={(workerId) => console.log('Selected worker:', workerId)}
        />
      </div>
    </div>
  );
}
