/**
 * Message Component
 *
 * Displays a single dialogue entry between worker and orchestrator.
 *
 * Features:
 * - Color-coded by direction (worker=blue, orchestrator=purple)
 * - Timestamp formatting
 * - Confirmation badge display
 * - Syntax highlighting for code content
 * - Responsive design
 */

import type { DialogueEntry } from '../types/dialogue';

interface MessageProps {
  entry: DialogueEntry;
  /** Optional CSS class name */
  className?: string;
}

/**
 * Format Unix timestamp to human-readable time
 */
function formatTime(timestamp: number): string {
  const date = new Date(timestamp * 1000);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

/**
 * Get confirmation badge color based on type
 */
function getConfirmationBadgeColor(type: string | null): string {
  switch (type) {
    case 'bash':
      return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
    case 'write_file':
      return 'bg-green-500/20 text-green-300 border-green-500/30';
    case 'read_file':
      return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
    default:
      return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
  }
}

export function Message({ entry, className = '' }: MessageProps) {
  const isWorker = entry.direction === 'worker→orchestrator';
  const isOrchestrator = entry.direction === 'orchestrator→worker';

  // Determine message colors
  const borderColor = isWorker
    ? 'border-l-worker'
    : isOrchestrator
    ? 'border-l-orchestrator'
    : 'border-l-gray-500';

  const headerBg = isWorker
    ? 'bg-worker/10'
    : isOrchestrator
    ? 'bg-orchestrator/10'
    : 'bg-gray-500/10';

  const directionColor = isWorker
    ? 'text-worker'
    : isOrchestrator
    ? 'text-orchestrator'
    : 'text-gray-400';

  return (
    <div
      className={`border-l-4 ${borderColor} bg-gray-800 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow message-enter ${className}`}
    >
      {/* Header */}
      <div className={`${headerBg} px-4 py-2 flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          {/* Direction Icon */}
          <span className={`${directionColor} font-semibold text-sm`}>
            {isWorker ? '→' : '←'}
          </span>

          {/* Direction Label */}
          <span className={`${directionColor} font-medium text-sm`}>
            {isWorker ? 'Worker' : 'Orchestrator'}
          </span>

          {/* Confirmation Badge */}
          {entry.confirmation_type && (
            <span
              className={`px-2 py-0.5 rounded text-xs font-mono border ${getConfirmationBadgeColor(
                entry.confirmation_type
              )}`}
            >
              {entry.confirmation_type}
            </span>
          )}
        </div>

        {/* Timestamp */}
        <span className="text-xs text-gray-400 font-mono">
          {formatTime(entry.timestamp)}
        </span>
      </div>

      {/* Content */}
      <div className="px-4 py-3">
        {/* Confirmation Message */}
        {entry.confirmation_message && (
          <div className="mb-2 text-sm text-yellow-300 italic">
            {entry.confirmation_message}
          </div>
        )}

        {/* Main Content */}
        <pre className="text-sm text-gray-100 whitespace-pre-wrap font-mono leading-relaxed">
          {entry.content}
        </pre>
      </div>
    </div>
  );
}
