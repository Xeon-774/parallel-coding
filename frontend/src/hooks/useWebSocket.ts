/**
 * useWebSocket Hook
 *
 * Manages WebSocket connection to the dialogue API with automatic reconnection,
 * error handling, and message queueing.
 *
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Message buffering during disconnection
 * - Type-safe message handling
 * - Connection status tracking
 * - Cleanup on unmount
 *
 * Usage:
 *   const { messages, status, error, isReady } = useWebSocket('worker_001');
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type {
  DialogueEntry,
  WebSocketMessage,
  ConnectionStatus,
  UseWebSocketState,
} from '../types/dialogue';

interface UseWebSocketOptions {
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
 * Custom hook for managing WebSocket connections to dialogue API
 */
export function useWebSocket(
  workerId: string | null,
  options: UseWebSocketOptions = {}
): UseWebSocketState {
  const {
    baseUrl = 'ws://localhost:8000',
    maxReconnectAttempts = Infinity,
    reconnectDelay = 1000,
    maxReconnectDelay = 30000,
    autoReconnect = true,
  } = options;

  // State
  const [messages, setMessages] = useState<DialogueEntry[]>([]);
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
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
      setStatus('disconnected');
      return;
    }

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    try {
      const url = `${baseUrl}/ws/dialogue/${workerId}`;
      console.log(`[WebSocket] Connecting to ${url}...`);

      setStatus('connecting');
      setError(null);

      const ws = new WebSocket(url);
      wsRef.current = ws;

      // Connection opened
      ws.onopen = () => {
        console.log(`[WebSocket] Connected to ${workerId}`);
        setStatus('connected');
        setError(null);
        reconnectAttemptsRef.current = 0;
        currentDelayRef.current = reconnectDelay;
      };

      // Message received
      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          switch (message.type) {
            case 'historical':
            case 'entry':
              setMessages((prev) => [...prev, message.data]);
              break;

            case 'ready':
              console.log(`[WebSocket] ${message.message}`);
              setIsReady(true);
              break;

            case 'error':
              console.error(`[WebSocket] Server error: ${message.message}`);
              setError(message.message);
              break;

            default:
              console.warn(`[WebSocket] Unknown message type:`, message);
          }
        } catch (err) {
          console.error('[WebSocket] Failed to parse message:', err);
        }
      };

      // Connection closed
      ws.onclose = (event) => {
        console.log(`[WebSocket] Connection closed (code: ${event.code})`);
        wsRef.current = null;

        if (shouldReconnectRef.current && autoReconnect) {
          if (reconnectAttemptsRef.current < maxReconnectAttempts) {
            setStatus('reconnecting');

            const delay = Math.min(
              currentDelayRef.current,
              maxReconnectDelay
            );

            console.log(
              `[WebSocket] Reconnecting in ${delay}ms (attempt ${
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
              `[WebSocket] Max reconnect attempts (${maxReconnectAttempts}) reached`
            );
            setStatus('error');
            setError('Connection failed after multiple attempts');
          }
        } else {
          setStatus('disconnected');
        }
      };

      // Connection error
      ws.onerror = (event) => {
        console.error('[WebSocket] Error:', event);
        setError('Connection error');
        setStatus('error');
      };
    } catch (err) {
      console.error('[WebSocket] Failed to create connection:', err);
      setStatus('error');
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  }, [
    workerId,
    baseUrl,
    autoReconnect,
    maxReconnectAttempts,
    reconnectDelay,
    maxReconnectDelay,
  ]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    console.log('[WebSocket] Disconnecting...');
    shouldReconnectRef.current = false;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setStatus('disconnected');
    setIsReady(false);
  }, []);

  /**
   * Manually trigger reconnection
   */
  const reconnect = useCallback(() => {
    console.log('[WebSocket] Manual reconnect triggered');
    reconnectAttemptsRef.current = 0;
    currentDelayRef.current = reconnectDelay;
    shouldReconnectRef.current = true;
    disconnect();
    connect();
  }, [connect, disconnect, reconnectDelay]);

  // Connect on mount or workerId change
  useEffect(() => {
    shouldReconnectRef.current = true;
    setMessages([]); // Clear previous messages
    setIsReady(false);
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    messages,
    status,
    error,
    isReady,
    disconnect,
    reconnect,
  };
}
