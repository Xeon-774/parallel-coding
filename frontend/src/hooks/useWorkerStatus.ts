/**
 * useWorkerStatus Hook
 *
 * Manages WebSocket connection to the worker status API with automatic reconnection,
 * error handling, and real-time status updates.
 *
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Real-time status updates via WebSocket
 * - Type-safe message handling
 * - Connection status tracking
 * - Cleanup on unmount
 *
 * Usage:
 *   const { status, connectionStatus, error, isReady } = useWorkerStatus('worker_001');
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type {
  WorkerStatus,
  StatusWebSocketMessage,
  StatusConnectionStatus,
  UseWorkerStatusState,
} from '../types/worker-status';

interface UseWorkerStatusOptions {
  /**
   * Base URL for the WebSocket server
   * @default 'ws://localhost:8000'
   */
  baseUrl?: string;

  /**
   * Maximum number of reconnection attempts
   * @default Infinity
   */
  maxReconnectAttempts?: number;

  /**
   * Initial reconnection delay in milliseconds
   * @default 1000
   */
  reconnectDelay?: number;

  /**
   * Maximum reconnection delay in milliseconds
   * @default 30000
   */
  maxReconnectDelay?: number;

  /**
   * Whether to automatically reconnect on connection loss
   * @default true
   */
  autoReconnect?: boolean;
}

/**
 * Custom hook for managing WebSocket connections to worker status API
 */
export function useWorkerStatus(
  workerId: string | null,
  options: UseWorkerStatusOptions = {}
): UseWorkerStatusState {
  const {
    baseUrl = 'ws://localhost:8000',
    maxReconnectAttempts = Infinity,
    reconnectDelay = 1000,
    maxReconnectDelay = 30000,
    autoReconnect = true,
  } = options;

  // State
  const [status, setStatus] = useState<WorkerStatus | null>(null);
  const [connectionStatus, setConnectionStatus] =
    useState<StatusConnectionStatus>('disconnected');
  const [error, setError] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);

  // Refs (don't cause re-renders)
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const currentDelayRef = useRef(reconnectDelay);
  const shouldReconnectRef = useRef(true);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    if (!workerId) {
      setConnectionStatus('disconnected');
      return;
    }

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    try {
      const url = `${baseUrl}/api/v1/status/ws/${workerId}`;
      console.log(`[WorkerStatus] Connecting to ${url}...`);

      setConnectionStatus('connecting');
      setError(null);

      const ws = new WebSocket(url);
      wsRef.current = ws;

      // Connection opened
      ws.onopen = () => {
        console.log(`[WorkerStatus] Connected to ${workerId}`);
        setConnectionStatus('connected');
        setError(null);
        setIsReady(true);
        reconnectAttemptsRef.current = 0;
        currentDelayRef.current = reconnectDelay;
      };

      // Message received
      ws.onmessage = (event) => {
        try {
          const message: StatusWebSocketMessage = JSON.parse(event.data);

          switch (message.type) {
            case 'status':
              setStatus(message.data);
              break;

            case 'error':
              console.error(`[WorkerStatus] Server error: ${message.message}`);
              setError(message.message);
              break;

            default:
              console.warn(`[WorkerStatus] Unknown message type:`, message);
          }
        } catch (err) {
          console.error('[WorkerStatus] Failed to parse message:', err);
        }
      };

      // Connection closed
      ws.onclose = (event) => {
        console.log(`[WorkerStatus] Connection closed (code: ${event.code})`);
        wsRef.current = null;
        setIsReady(false);

        if (shouldReconnectRef.current && autoReconnect) {
          // Check if worker is in terminal state - don't reconnect
          if (
            status &&
            (status.state === 'completed' ||
              status.state === 'error' ||
              status.state === 'terminated')
          ) {
            console.log(
              `[WorkerStatus] Worker ${workerId} is in terminal state, not reconnecting`
            );
            setConnectionStatus('disconnected');
            return;
          }

          if (reconnectAttemptsRef.current < maxReconnectAttempts) {
            setConnectionStatus('reconnecting');

            const delay = Math.min(currentDelayRef.current, maxReconnectDelay);

            console.log(
              `[WorkerStatus] Reconnecting in ${delay}ms (attempt ${
                reconnectAttemptsRef.current + 1
              })`
            );

            reconnectTimeoutRef.current = window.setTimeout(() => {
              reconnectAttemptsRef.current += 1;
              currentDelayRef.current *= 2; // Exponential backoff
              connect();
            }, delay);
          } else {
            console.error(
              `[WorkerStatus] Max reconnect attempts (${maxReconnectAttempts}) reached`
            );
            setConnectionStatus('error');
            setError('Connection failed after multiple attempts');
          }
        } else {
          setConnectionStatus('disconnected');
        }
      };

      // Connection error
      ws.onerror = (event) => {
        console.error('[WorkerStatus] Error:', event);
        setError('Connection error');
        setConnectionStatus('error');
      };
    } catch (err) {
      console.error('[WorkerStatus] Failed to create connection:', err);
      setConnectionStatus('error');
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  }, [
    workerId,
    baseUrl,
    autoReconnect,
    maxReconnectAttempts,
    reconnectDelay,
    maxReconnectDelay,
    status,
  ]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    console.log('[WorkerStatus] Disconnecting...');
    shouldReconnectRef.current = false;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setConnectionStatus('disconnected');
    setIsReady(false);
  }, []);

  /**
   * Manually trigger reconnection
   */
  const reconnect = useCallback(() => {
    console.log('[WorkerStatus] Manual reconnect triggered');
    reconnectAttemptsRef.current = 0;
    currentDelayRef.current = reconnectDelay;
    shouldReconnectRef.current = true;
    disconnect();
    connect();
  }, [connect, disconnect, reconnectDelay]);

  // Connect on mount or workerId change
  useEffect(() => {
    shouldReconnectRef.current = true;
    setStatus(null); // Clear previous status
    setIsReady(false);
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    status,
    connectionStatus,
    error,
    isReady,
    disconnect,
    reconnect,
  };
}
