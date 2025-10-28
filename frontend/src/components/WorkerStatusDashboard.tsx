/**
 * WorkerStatusDashboard Component
 *
 * Displays real-time status monitoring for all workers.
 * Milestone 1.3: Worker Status UI
 *
 * Features:
 * - Summary statistics (total, active, completed, errors)
 * - Grid layout of worker status cards (responsive)
 * - Auto-refresh every 2 seconds
 * - Empty state handling
 * - Error handling with retry
 * - Click worker cards for details
 *
 * Usage:
 *   <WorkerStatusDashboard onWorkerClick={(workerId) => console.log(workerId)} />
 */

import { WorkerStatusCard } from './WorkerStatusCard';
import { useWorkerStatusList } from '../hooks/useWorkerStatusList';

interface WorkerStatusDashboardProps {
  /**
   * Callback when a worker card is clicked
   */
  onWorkerClick?: (workerId: string) => void;

  /**
   * Base URL for API
   * @default 'http://localhost:8000'
   */
  baseUrl?: string;

  /**
   * Auto-refresh interval in milliseconds
   * @default 2000
   */
  refreshInterval?: number;
}

/**
 * Summary Card Component
 */
interface SummaryCardProps {
  label: string;
  value: number;
  icon: string;
  color: string;
  bgColor: string;
}

function SummaryCard({ label, value, icon, color, bgColor }: SummaryCardProps) {
  return (
    <div className={`${bgColor} rounded-lg p-4 border border-gray-700`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-400">{label}</span>
        <span className="text-xl">{icon}</span>
      </div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
    </div>
  );
}

/**
 * Main WorkerStatusDashboard Component
 */
export function WorkerStatusDashboard({
  onWorkerClick,
  baseUrl = 'http://localhost:8000',
  refreshInterval = 2000,
}: WorkerStatusDashboardProps) {
  const { workers, summary, isLoading, error, refresh } = useWorkerStatusList({
    baseUrl,
    autoRefresh: true,
    refreshInterval,
    fetchSummary: true,
  });

  const handleWorkerClick = (workerId: string) => {
    if (onWorkerClick) {
      onWorkerClick(workerId);
    }
  };

  // Loading state
  if (isLoading && workers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <div className="animate-spin text-4xl mb-4">◐</div>
        <div className="text-gray-400">Loading worker status...</div>
      </div>
    );
  }

  // Error state
  if (error && workers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <div className="text-red-400 text-4xl mb-4">✕</div>
        <div className="text-gray-400 mb-4">Failed to load worker status</div>
        <div className="text-sm text-red-400 mb-4">{error}</div>
        <button
          onClick={refresh}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  // Empty state
  if (workers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <div className="text-gray-500 text-4xl mb-4">○</div>
        <div className="text-gray-400 mb-2">No active workers</div>
        <div className="text-sm text-gray-500">Workers will appear here when they start executing</div>
      </div>
    );
  }

  // Sort workers: active first, then by worker_id
  const sortedWorkers = [...workers].sort((a, b) => {
    const aActive = ['running', 'waiting', 'spawning'].includes(a.state);
    const bActive = ['running', 'waiting', 'spawning'].includes(b.state);

    if (aActive && !bActive) return -1;
    if (!aActive && bActive) return 1;

    return a.worker_id.localeCompare(b.worker_id);
  });

  return (
    <div className="space-y-6">
      {/* Summary Statistics */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <SummaryCard
            label="Total Workers"
            value={summary.total_workers}
            icon="◎"
            color="text-blue-400"
            bgColor="bg-gray-800"
          />
          <SummaryCard
            label="Active"
            value={summary.active_workers}
            icon="▶"
            color="text-green-400"
            bgColor="bg-gray-800"
          />
          <SummaryCard
            label="Completed"
            value={summary.completed_workers}
            icon="✓"
            color="text-emerald-400"
            bgColor="bg-gray-800"
          />
          <SummaryCard
            label="Errors"
            value={summary.error_workers}
            icon="✕"
            color="text-red-400"
            bgColor="bg-gray-800"
          />
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">
          Worker Status
          <span className="ml-2 text-sm text-gray-400">({workers.length} workers)</span>
        </h2>
        <button
          onClick={refresh}
          className="px-3 py-1 text-sm bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
          title="Refresh now"
        >
          ⟳ Refresh
        </button>
      </div>

      {/* Worker Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {sortedWorkers.map((worker) => (
          <WorkerStatusCard
            key={worker.worker_id}
            status={worker}
            onClick={() => handleWorkerClick(worker.worker_id)}
          />
        ))}
      </div>

      {/* Error Banner (if error occurs during refresh) */}
      {error && workers.length > 0 && (
        <div className="p-3 bg-red-900/20 border border-red-500/50 rounded text-sm text-red-400">
          ⚠ Error refreshing: {error}
        </div>
      )}
    </div>
  );
}
