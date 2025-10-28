/**
 * WorkerStatusCard Component
 *
 * Displays individual worker execution status with real-time updates.
 * Milestone 1.3: Worker Status UI
 *
 * Features:
 * - Worker ID and current task display
 * - Progress bar with percentage
 * - Color-coded state indicators
 * - Elapsed time tracking
 * - Health status monitoring
 * - Output and confirmation metrics
 */

import type { WorkerStatus } from '../types/worker-status';

interface WorkerStatusCardProps {
  status: WorkerStatus;
  onClick?: () => void;
}

interface StateConfig {
  label: string;
  color: string;
  bgColor: string;
  borderColor: string;
  icon: string;
}

interface HealthConfig {
  color: string;
  icon: string;
  tooltip: string;
}

const STATE_CONFIG: Record<WorkerStatus['state'], StateConfig> = {
  spawning: {
    label: 'Spawning',
    color: 'text-blue-400',
    bgColor: 'bg-blue-900/20',
    borderColor: 'border-blue-500/50',
    icon: '◐',
  },
  running: {
    label: 'Running',
    color: 'text-green-400',
    bgColor: 'bg-green-900/20',
    borderColor: 'border-green-500/50',
    icon: '▶',
  },
  waiting: {
    label: 'Waiting',
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-900/20',
    borderColor: 'border-yellow-500/50',
    icon: '⏸',
  },
  completed: {
    label: 'Completed',
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-900/20',
    borderColor: 'border-emerald-500/50',
    icon: '✓',
  },
  error: {
    label: 'Error',
    color: 'text-red-400',
    bgColor: 'bg-red-900/20',
    borderColor: 'border-red-500/50',
    icon: '✕',
  },
  terminated: {
    label: 'Terminated',
    color: 'text-gray-400',
    bgColor: 'bg-gray-900/20',
    borderColor: 'border-gray-500/50',
    icon: '⊗',
  },
};

const HEALTH_CONFIG: Record<WorkerStatus['health'], HealthConfig> = {
  healthy: {
    color: 'text-green-400',
    icon: '●',
    tooltip: 'Worker is healthy and active',
  },
  idle: {
    color: 'text-yellow-400',
    icon: '◐',
    tooltip: 'Worker has been idle for 30+ seconds',
  },
  stalled: {
    color: 'text-orange-400',
    icon: '◑',
    tooltip: 'Worker has been stalled for 2+ minutes',
  },
  unhealthy: {
    color: 'text-red-400',
    icon: '○',
    tooltip: 'Worker is unhealthy',
  },
};

function formatElapsedTime(seconds: number): string {
  if (seconds < 60) return `${Math.floor(seconds)}s`;
  if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  }
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${mins}m`;
}

export function WorkerStatusCard({ status, onClick }: WorkerStatusCardProps) {
  const stateConfig = STATE_CONFIG[status.state];
  const healthConfig = HEALTH_CONFIG[status.health];
  const isActive = ['running', 'waiting', 'spawning'].includes(status.state);

  return (
    <div
      className={`relative bg-gray-800 rounded-lg border-2 ${stateConfig.borderColor} p-4 transition-all hover:shadow-lg ${
        onClick ? 'cursor-pointer hover:scale-[1.02]' : ''
      }`}
      onClick={onClick}
    >
      {/* Header: Worker ID + State */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-white">{status.worker_id}</h3>
          <span
            className={`px-2 py-1 rounded text-xs font-medium ${stateConfig.bgColor} ${stateConfig.color} border ${stateConfig.borderColor}`}
          >
            <span className={isActive ? 'animate-pulse' : ''}>{stateConfig.icon}</span>{' '}
            {stateConfig.label}
          </span>
        </div>

        {/* Health Indicator */}
        <div className="group relative">
          <span className={`${healthConfig.color} text-sm`} title={healthConfig.tooltip}>
            {healthConfig.icon}
          </span>
          <div className="absolute bottom-full right-0 mb-2 hidden group-hover:block w-48 px-2 py-1 bg-gray-900 text-white text-xs rounded border border-gray-700 shadow-lg whitespace-nowrap">
            {healthConfig.tooltip}
          </div>
        </div>
      </div>

      {/* Current Task */}
      <div className="mb-3">
        <div className="text-xs text-gray-400 mb-1">Current Task</div>
        <div className="text-sm text-gray-200 truncate" title={status.current_task}>
          {status.current_task}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Progress</span>
          <span className="font-mono">{status.progress}%</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${
              status.state === 'completed'
                ? 'bg-emerald-500'
                : status.state === 'error'
                  ? 'bg-red-500'
                  : 'bg-blue-500'
            }`}
            style={{ width: `${status.progress}%` }}
          />
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-2 text-center">
        {/* Elapsed Time */}
        <div className="bg-gray-900/50 rounded p-2">
          <div className="text-xs text-gray-400">Time</div>
          <div className="text-sm font-mono text-white">
            {formatElapsedTime(status.elapsed_time)}
          </div>
        </div>

        {/* Output Lines */}
        <div className="bg-gray-900/50 rounded p-2">
          <div className="text-xs text-gray-400">Output</div>
          <div className="text-sm font-mono text-white">{status.output_lines}</div>
        </div>

        {/* Confirmations */}
        <div className="bg-gray-900/50 rounded p-2">
          <div className="text-xs text-gray-400">Confirms</div>
          <div className="text-sm font-mono text-white">{status.confirmation_count}</div>
        </div>
      </div>

      {/* Performance Metrics (if available) */}
      {(status.memory_mb || status.cpu_percent) && (
        <div className="grid grid-cols-2 gap-2 mt-2 text-center">
          {status.memory_mb && (
            <div className="bg-gray-900/50 rounded p-2">
              <div className="text-xs text-gray-400">Memory</div>
              <div className="text-sm font-mono text-white">{status.memory_mb.toFixed(1)} MB</div>
            </div>
          )}
          {status.cpu_percent && (
            <div className="bg-gray-900/50 rounded p-2">
              <div className="text-xs text-gray-400">CPU</div>
              <div className="text-sm font-mono text-white">{status.cpu_percent.toFixed(1)}%</div>
            </div>
          )}
        </div>
      )}

      {/* Error Message (if present) */}
      {status.error_message && status.state === 'error' && (
        <div className="mt-3 p-2 bg-red-900/20 border border-red-500/50 rounded">
          <div className="text-xs text-red-400 font-semibold mb-1">Error</div>
          <div className="text-xs text-red-300 break-words">{status.error_message}</div>
        </div>
      )}
    </div>
  );
}
