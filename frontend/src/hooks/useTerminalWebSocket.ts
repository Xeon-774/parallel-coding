/**
 * useTerminalWebSocket Hook
 *
 * Custom React hook for managing WebSocket connection to raw terminal output stream.
 * Similar to useWebSocket but for raw terminal lines.
 *
 * Features:
 * - Auto-reconnect with exponential backoff
 * - Real-time terminal line streaming
 * - Connection state management
 * - Type-safe message handling
 */

import { useState, useEffect, useRef } from 'react';

export interface TerminalLine {
  content: string;
  timestamp: number; // Added locally
}

export type TerminalConnectionStatus =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'reconnecting'
  | 'error';

export interface UseTerminalWebSocketOptions {
  baseUrl?: string;
  maxReconnectAttempts?: number;
  reconnectDelay?: number;
  maxReconnectDelay?: number;
  autoReconnect?: boolean;
  terminalType?: 'worker' | 'orchestrator';
}

export interface UseTerminalWebSocketState {
  lines: TerminalLine[];
  status: TerminalConnectionStatus;
  error: string | null;
  isReady: boolean;
  disconnect: () => void;
  reconnect: () => void;
  clearLines: () => void;
}

export function useTerminalWebSocket(
  workerId: string | null,
  options: UseTerminalWebSocketOptions = {}
): UseTerminalWebSocketState {
  const {
    baseUrl = 'ws://localhost:8000',
    maxReconnectAttempts = Infinity,
    reconnectDelay = 1000,
    maxReconnectDelay = 30000,
    autoReconnect = true,
    terminalType = 'worker',
  } = options;

  const [lines, setLines] = useState<TerminalLine[]>([]);
  const [status, setStatus] = useState<TerminalConnectionStatus>('disconnected');
  const [error, setError] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const currentDelayRef = useRef(reconnectDelay);
  const isManualDisconnectRef = useRef(false);

  const connect = () => {
    if (!workerId) {
      setStatus('disconnected');
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    // Clear any pending reconnect
    if (reconnectTimeoutRef.current) {
      window.clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setStatus(
      reconnectAttemptsRef.current > 0 ? 'reconnecting' : 'connecting'
    );
    setError(null);

    try {
      const ws = new WebSocket(`${baseUrl}/ws/terminal/${workerId}?terminal_type=${terminalType}`);

      ws.onopen = () => {
        setStatus('connected');
        setError(null);
        reconnectAttemptsRef.current = 0;
        currentDelayRef.current = reconnectDelay;
        isManualDisconnectRef.current = false;
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          switch (message.type) {
            case 'ready':
              setIsReady(true);
              break;

            case 'line':
              setLines((prev) => [
                ...prev,
                {
                  content: message.content,
                  timestamp: Date.now(),
                },
              ]);
              break;

            case 'error':
              setError(message.message || 'Unknown error');
              setStatus('error');
              break;

            default:
              console.warn('Unknown terminal message type:', message.type);
          }
        } catch (err) {
          console.error('Failed to parse terminal message:', err);
        }
      };

      ws.onerror = () => {
        console.error('Terminal WebSocket error');
        setStatus('error');
        setError('Connection error');
      };

      ws.onclose = () => {
        setStatus('disconnected');
        setIsReady(false);

        // Auto-reconnect if not manual disconnect
        if (
          !isManualDisconnectRef.current &&
          autoReconnect &&
          reconnectAttemptsRef.current < maxReconnectAttempts
        ) {
          const delay = Math.min(currentDelayRef.current, maxReconnectDelay);

          reconnectTimeoutRef.current = window.setTimeout(() => {
            reconnectAttemptsRef.current += 1;
            currentDelayRef.current *= 2; // Exponential backoff
            connect();
          }, delay);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to create terminal WebSocket:', err);
      setStatus('error');
      setError('Failed to connect');
    }
  };

  const disconnect = () => {
    isManualDisconnectRef.current = true;

    if (reconnectTimeoutRef.current) {
      window.clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setStatus('disconnected');
    setIsReady(false);
  };

  const reconnect = () => {
    disconnect();
    isManualDisconnectRef.current = false;
    reconnectAttemptsRef.current = 0;
    currentDelayRef.current = reconnectDelay;
    connect();
  };

  const clearLines = () => {
    setLines([]);
  };

  // Auto-connect when workerId or terminalType changes
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workerId, terminalType]);

  return {
    lines,
    status,
    error,
    isReady,
    disconnect,
    reconnect,
    clearLines,
  };
}
