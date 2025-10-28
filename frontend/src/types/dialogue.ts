/**
 * Type definitions for the dialogue visualization frontend
 *
 * These types correspond to the Python backend API defined in:
 * orchestrator/api/dialogue_ws.py
 */

/**
 * Direction of dialogue communication
 */
export type DialogueDirection = 'worker→orchestrator' | 'orchestrator→worker';

/**
 * Type of dialogue entry
 */
export type DialogueEntryType = 'output' | 'response';

/**
 * Confirmation type for operations requiring approval
 */
export type ConfirmationType = 'bash' | 'write_file' | 'read_file' | null;

/**
 * A single dialogue entry between worker and orchestrator
 */
export interface DialogueEntry {
  timestamp: number;
  direction: DialogueDirection;
  content: string;
  type: DialogueEntryType;
  confirmation_type: ConfirmationType;
  confirmation_message: string | null;
}

/**
 * WebSocket message type discriminator
 */
export type MessageType = 'historical' | 'entry' | 'ready' | 'error';

/**
 * Base WebSocket message
 */
export interface BaseWebSocketMessage {
  type: MessageType;
}

/**
 * Historical entry message (sent on connection)
 */
export interface HistoricalMessage extends BaseWebSocketMessage {
  type: 'historical';
  data: DialogueEntry;
}

/**
 * Real-time entry message (sent as entries are added)
 */
export interface EntryMessage extends BaseWebSocketMessage {
  type: 'entry';
  data: DialogueEntry;
}

/**
 * Ready message (sent after historical entries are loaded)
 */
export interface ReadyMessage extends BaseWebSocketMessage {
  type: 'ready';
  message: string;
}

/**
 * Error message (sent when an error occurs)
 */
export interface ErrorMessage extends BaseWebSocketMessage {
  type: 'error';
  message: string;
}

/**
 * Union type of all possible WebSocket messages
 */
export type WebSocketMessage =
  | HistoricalMessage
  | EntryMessage
  | ReadyMessage
  | ErrorMessage;

/**
 * Worker information from REST API
 */
export interface Worker {
  worker_id: string;
  workspace_path: string;
  has_dialogue: boolean;
  dialogue_size: number;
}

/**
 * Worker list response from REST API
 */
export interface WorkersResponse {
  workers: Worker[];
  count: number;
}

/**
 * WebSocket connection status
 */
export type ConnectionStatus =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'reconnecting'
  | 'error';

/**
 * WebSocket hook state
 */
export interface UseWebSocketState {
  messages: DialogueEntry[];
  status: ConnectionStatus;
  error: string | null;
  isReady: boolean;
  disconnect: () => void;
  reconnect: () => void;
}
