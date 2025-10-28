/**
 * WorkerSelector Component
 *
 * Allows users to select which worker's dialogue to monitor.
 *
 * Features:
 * - Fetches available workers from API
 * - Displays worker list with status
 * - Handles worker selection
 * - Loading and error states
 */

import { useState, useEffect } from 'react';

interface Worker {
  worker_id: string;
  workspace_path: string;
  has_dialogue: boolean;
  dialogue_size: number;
}

interface WorkersResponse {
  workers: Worker[];
  count: number;
}

interface WorkerSelectorProps {
  /** Currently selected worker ID */
  selectedWorkerId: string | null;
  /** Callback when worker is selected */
  onWorkerSelect: (workerId: string) => void;
  /** Optional callback when workers list changes */
  onWorkersChange?: (workerIds: string[]) => void;
  /** Optional CSS class name */
  className?: string;
}

export function WorkerSelector({
  selectedWorkerId,
  onWorkerSelect,
  onWorkersChange,
  className = '',
}: WorkerSelectorProps) {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch workers from API
  useEffect(() => {
    const fetchWorkers = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch('http://localhost:8000/api/v1/workers');

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data: WorkersResponse = await response.json();
        setWorkers(data.workers);

        // Notify parent of workers list
        if (onWorkersChange) {
          onWorkersChange(data.workers.map(w => w.worker_id));
        }

        // Auto-select first worker if none selected
        if (!selectedWorkerId && data.workers.length > 0) {
          onWorkerSelect(data.workers[0].worker_id);
        }
      } catch (err) {
        console.error('Failed to fetch workers:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchWorkers();

    // Refresh every 10 seconds
    const interval = setInterval(fetchWorkers, 10000);
    return () => clearInterval(interval);
  }, [selectedWorkerId, onWorkerSelect]);

  // Loading state
  if (loading && workers.length === 0) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 ${className}`}>
        <div className="flex items-center gap-2 text-gray-400">
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-600 border-t-worker"></div>
          <span className="text-sm">Loading workers...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={`bg-red-900/20 border border-red-500/50 rounded-lg p-4 ${className}`}>
        <div className="flex items-center gap-2 text-red-400">
          <span className="text-lg">⚠</span>
          <div className="flex-1">
            <div className="font-semibold text-sm">Failed to load workers</div>
            <div className="text-xs mt-1 text-red-300">{error}</div>
          </div>
        </div>
      </div>
    );
  }

  // Empty state
  if (workers.length === 0) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 ${className}`}>
        <div className="text-center text-gray-400">
          <div className="text-2xl mb-2">📂</div>
          <div className="text-sm">No workers found</div>
          <div className="text-xs text-gray-500 mt-1">
            Start a worker to see dialogue
          </div>
        </div>
      </div>
    );
  }

  // Worker list
  return (
    <div className={`bg-gray-800 rounded-lg ${className}`}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700">
        <h3 className="text-sm font-semibold text-white">Workers</h3>
        <p className="text-xs text-gray-400 mt-1">
          {workers.length} {workers.length === 1 ? 'worker' : 'workers'} available
        </p>
      </div>

      {/* Worker List */}
      <div className="divide-y divide-gray-700">
        {workers.map((worker) => {
          const isSelected = worker.worker_id === selectedWorkerId;
          const hasDialogue = worker.has_dialogue && worker.dialogue_size > 0;

          return (
            <button
              key={worker.worker_id}
              onClick={() => onWorkerSelect(worker.worker_id)}
              className={`w-full px-4 py-3 text-left transition-colors worker-item-enter focus-ring ${
                isSelected
                  ? 'bg-worker/10 border-l-4 border-worker'
                  : 'hover:bg-gray-750 border-l-4 border-transparent'
              }`}
            >
              <div className="flex items-center justify-between">
                {/* Worker ID */}
                <div className="flex-1 min-w-0">
                  <div
                    className={`text-sm font-mono truncate ${
                      isSelected ? 'text-worker font-semibold' : 'text-gray-300'
                    }`}
                  >
                    {worker.worker_id}
                  </div>

                  {/* Dialogue Status */}
                  <div className="flex items-center gap-2 mt-1">
                    {hasDialogue ? (
                      <>
                        <span className="inline-block w-2 h-2 bg-green-500 rounded-full"></span>
                        <span className="text-xs text-gray-400">
                          {(worker.dialogue_size / 1024).toFixed(1)} KB dialogue
                        </span>
                      </>
                    ) : (
                      <>
                        <span className="inline-block w-2 h-2 bg-gray-600 rounded-full"></span>
                        <span className="text-xs text-gray-500">No dialogue yet</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Selection Indicator */}
                {isSelected && (
                  <div className="ml-2">
                    <svg
                      className="w-5 h-5 text-worker"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Refresh Indicator */}
      {loading && (
        <div className="px-4 py-2 border-t border-gray-700">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <div className="animate-spin rounded-full h-3 w-3 border-2 border-gray-600 border-t-gray-400"></div>
            <span>Refreshing...</span>
          </div>
        </div>
      )}
    </div>
  );
}
