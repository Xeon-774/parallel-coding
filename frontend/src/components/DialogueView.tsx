/**
 * DialogueView Component
 *
 * Main container for displaying worker-orchestrator dialogue in real-time.
 *
 * Features:
 * - Real-time WebSocket connection
 * - Auto-scroll to latest message
 * - Connection status indicator
 * - Loading states
 * - Error handling
 * - Worker selection
 */

import { useEffect, useRef } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { Message } from './Message';
import { ConnectionStatus } from './ConnectionStatus';

interface DialogueViewProps {
  /** Worker ID to monitor */
  workerId: string;
  /** Optional CSS class name */
  className?: string;
}

export function DialogueView({ workerId, className = '' }: DialogueViewProps) {
  const { messages, status, error, isReady, reconnect } = useWebSocket(workerId);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages.length]);

  return (
    <div
      className={`flex flex-col h-full bg-gray-900 rounded-lg shadow-xl overflow-hidden ${className}`}
    >
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-white">
              Worker Dialogue
            </h2>
            <p className="text-sm text-gray-400 mt-1">
              Monitoring: <span className="font-mono text-worker">{workerId}</span>
            </p>
          </div>

          <ConnectionStatus
            status={status}
            error={error}
            onReconnect={reconnect}
          />
        </div>
      </div>

      {/* Messages Container */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto px-6 py-4 space-y-3 custom-scrollbar"
      >
        {/* Loading State */}
        {status === 'connecting' && messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-600 border-t-worker mb-4"></div>
              <p className="text-gray-400">Connecting to {workerId}...</p>
            </div>
          </div>
        )}

        {/* Error State */}
        {status === 'error' && messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md">
              <div className="text-red-400 text-5xl mb-4">⚠</div>
              <p className="text-red-400 text-lg font-semibold mb-2">
                Connection Error
              </p>
              <p className="text-gray-400 mb-4">
                {error || 'Failed to connect to the dialogue API'}
              </p>
              <button
                onClick={reconnect}
                className="px-4 py-2 bg-worker text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                Retry Connection
              </button>
            </div>
          </div>
        )}

        {/* Empty State (Connected but no messages) */}
        {status === 'connected' && isReady && messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-gray-500 text-6xl mb-4">💬</div>
              <p className="text-gray-400">No dialogue entries yet</p>
              <p className="text-gray-500 text-sm mt-2">
                Waiting for worker activity...
              </p>
            </div>
          </div>
        )}

        {/* Messages List */}
        {messages.map((entry, index) => (
          <Message key={`${entry.timestamp}-${index}`} entry={entry} />
        ))}

        {/* Loading indicator (while connected and receiving historical) */}
        {status === 'connected' && !isReady && messages.length > 0 && (
          <div className="text-center py-4">
            <span className="inline-block animate-pulse text-gray-400 text-sm">
              Loading historical entries...
            </span>
          </div>
        )}

        {/* Auto-scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* Footer */}
      <div className="bg-gray-800 border-t border-gray-700 px-6 py-3">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>
            {messages.length} {messages.length === 1 ? 'entry' : 'entries'}
          </span>
          {isReady && (
            <span className="flex items-center gap-2">
              <span className="inline-block w-2 h-2 bg-green-500 rounded-full live-pulse"></span>
              Live
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
