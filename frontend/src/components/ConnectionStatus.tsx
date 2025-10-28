/**
 * ConnectionStatus Component
 *
 * Displays WebSocket connection status with visual indicators.
 *
 * Features:
 * - Color-coded status badges
 * - Reconnect button for errors
 * - Animated indicators
 * - Tooltips with error details
 */

import type { ConnectionStatus as Status } from '../types/dialogue';

interface ConnectionStatusProps {
  status: Status;
  error: string | null;
  onReconnect: () => void;
}

interface StatusConfig {
  label: string;
  color: string;
  bgColor: string;
  borderColor: string;
  icon: string;
  animated?: boolean;
}

const STATUS_CONFIG: Record<Status, StatusConfig> = {
  disconnected: {
    label: 'Disconnected',
    color: 'text-gray-400',
    bgColor: 'bg-gray-700',
    borderColor: 'border-gray-600',
    icon: '○',
  },
  connecting: {
    label: 'Connecting',
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-900/30',
    borderColor: 'border-yellow-500/50',
    icon: '◐',
    animated: true,
  },
  connected: {
    label: 'Connected',
    color: 'text-green-400',
    bgColor: 'bg-green-900/30',
    borderColor: 'border-green-500/50',
    icon: '●',
  },
  reconnecting: {
    label: 'Reconnecting',
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-900/30',
    borderColor: 'border-yellow-500/50',
    icon: '◐',
    animated: true,
  },
  error: {
    label: 'Error',
    color: 'text-red-400',
    bgColor: 'bg-red-900/30',
    borderColor: 'border-red-500/50',
    icon: '✕',
  },
};

export function ConnectionStatus({
  status,
  error,
  onReconnect,
}: ConnectionStatusProps) {
  const config = STATUS_CONFIG[status];

  return (
    <div className="flex items-center gap-3">
      {/* Status Badge */}
      <div
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${config.bgColor} ${config.borderColor}`}
        title={error || undefined}
      >
        {/* Status Icon */}
        <span
          className={`${config.color} ${
            config.animated ? 'animate-spin' : ''
          }`}
        >
          {config.icon}
        </span>

        {/* Status Label */}
        <span className={`text-sm font-medium ${config.color}`}>
          {config.label}
        </span>
      </div>

      {/* Reconnect Button (only show on error) */}
      {status === 'error' && (
        <button
          onClick={onReconnect}
          className="px-3 py-1.5 bg-worker hover:bg-blue-600 text-white text-sm font-medium rounded-lg transition-colors"
          title="Attempt to reconnect"
        >
          Reconnect
        </button>
      )}

      {/* Error Tooltip */}
      {error && status === 'error' && (
        <div className="group relative">
          <span className="text-red-400 cursor-help">ⓘ</span>
          <div className="absolute bottom-full right-0 mb-2 hidden group-hover:block w-64 px-3 py-2 bg-gray-800 text-white text-xs rounded-lg shadow-lg border border-gray-700">
            <div className="font-semibold mb-1">Error Details:</div>
            <div className="text-gray-300">{error}</div>
          </div>
        </div>
      )}
    </div>
  );
}
