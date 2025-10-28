/**
 * Type definitions for worker status monitoring
 *
 * These types correspond to the Python backend API defined in:
 * orchestrator/api/worker_status_api.py
 * orchestrator/core/worker_status_monitor.py
 */

/**
 * Worker execution state
 */
export type WorkerState =
  | 'spawning'    // Worker process is being created
  | 'running'     // Worker is actively executing
  | 'waiting'     // Worker is waiting for orchestrator response
  | 'completed'   // Worker finished successfully
  | 'error'       // Worker encountered an error
  | 'terminated'; // Worker was forcefully stopped

/**
 * Worker health status
 */
export type HealthStatus =
  | 'healthy'     // Normal operation
  | 'idle'        // No activity for moderate duration (30+ seconds)
  | 'stalled'     // No activity for extended duration (2+ minutes)
  | 'unhealthy';  // Critical issue detected

/**
 * Complete status information for a single worker
 */
export interface WorkerStatus {
  worker_id: string;
  state: WorkerState;
  current_task: string;
  progress: number; // 0-100 percentage
  elapsed_time: number; // Seconds since spawn
  output_lines: number; // Total output lines captured
  confirmation_count: number; // Number of confirmations handled
  last_activity: number; // Unix timestamp of last activity
  health: HealthStatus;

  // Optional detailed metrics
  memory_mb?: number;
  cpu_percent?: number;
  error_message?: string;

  // Timestamps
  started_at: number;
  completed_at?: number;
}

/**
 * WebSocket message type discriminator for worker status
 */
export type StatusMessageType = 'status' | 'error';

/**
 * Base WebSocket message for worker status
 */
export interface BaseStatusMessage {
  type: StatusMessageType;
}

/**
 * Status update message
 */
export interface StatusUpdateMessage extends BaseStatusMessage {
  type: 'status';
  data: WorkerStatus;
}

/**
 * Status error message
 */
export interface StatusErrorMessage extends BaseStatusMessage {
  type: 'error';
  message: string;
}

/**
 * Union type of all possible status WebSocket messages
 */
export type StatusWebSocketMessage = StatusUpdateMessage | StatusErrorMessage;

/**
 * Workers list response from REST API
 */
export interface WorkerStatusListResponse {
  workers: WorkerStatus[];
  count: number;
}

/**
 * Status summary response from REST API
 */
export interface StatusSummaryResponse {
  total_workers: number;
  active_workers: number;
  completed_workers: number;
  error_workers: number;
  avg_progress: number;
  total_confirmations: number;
}

/**
 * WebSocket connection status for worker status
 */
export type StatusConnectionStatus =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'reconnecting'
  | 'error';

/**
 * Worker status hook state
 */
export interface UseWorkerStatusState {
  status: WorkerStatus | null;
  connectionStatus: StatusConnectionStatus;
  error: string | null;
  isReady: boolean;
  disconnect: () => void;
  reconnect: () => void;
}
