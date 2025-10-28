/**
 * useWorkerStatusList Hook
 *
 * Fetches list of all workers with their status from REST API.
 * Supports auto-refresh for real-time monitoring.
 *
 * Features:
 * - REST API polling for worker list
 * - Auto-refresh with configurable interval
 * - Error handling and loading states
 * - Summary statistics
 *
 * Usage:
 *   const { workers, summary, isLoading, error, refresh } = useWorkerStatusList({
 *     autoRefresh: true,
 *     refreshInterval: 2000
 *   });
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type {
  WorkerStatus,
  WorkerStatusListResponse,
  StatusSummaryResponse,
} from '../types/worker-status';

interface UseWorkerStatusListOptions {
  /**
   * Base URL for the API server
   * @default 'http://localhost:8000'
   */
  baseUrl?: string;

  /**
   * Enable auto-refresh
   * @default true
   */
  autoRefresh?: boolean;

  /**
   * Refresh interval in milliseconds
   * @default 2000
   */
  refreshInterval?: number;

  /**
   * Fetch summary statistics
   * @default true
   */
  fetchSummary?: boolean;
}

interface UseWorkerStatusListState {
  workers: WorkerStatus[];
  summary: StatusSummaryResponse | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Custom hook for fetching worker status list
 */
export function useWorkerStatusList(
  options: UseWorkerStatusListOptions = {}
): UseWorkerStatusListState {
  const {
    baseUrl = 'http://localhost:8000',
    autoRefresh = true,
    refreshInterval = 2000,
    fetchSummary = true,
  } = options;

  // State
  const [workers, setWorkers] = useState<WorkerStatus[]>([]);
  const [summary, setSummary] = useState<StatusSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Refs
  const refreshIntervalRef = useRef<number | null>(null);
  const isMountedRef = useRef(true);

  /**
   * Fetch worker status list from API
   */
  const fetchWorkers = useCallback(async () => {
    try {
      const response = await fetch(`${baseUrl}/api/v1/status/workers`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: WorkerStatusListResponse = await response.json();

      if (isMountedRef.current) {
        setWorkers(data.workers);
        setError(null);
      }
    } catch (err) {
      console.error('[WorkerStatusList] Error fetching workers:', err);
      if (isMountedRef.current) {
        setError(err instanceof Error ? err.message : 'Failed to fetch workers');
      }
    }
  }, [baseUrl]);

  /**
   * Fetch summary statistics from API
   */
  const fetchSummaryData = useCallback(async () => {
    try {
      const response = await fetch(`${baseUrl}/api/v1/status/summary`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: StatusSummaryResponse = await response.json();

      if (isMountedRef.current) {
        setSummary(data);
      }
    } catch (err) {
      console.error('[WorkerStatusList] Error fetching summary:', err);
      // Don't set error state for summary fetch failure
    }
  }, [baseUrl]);

  /**
   * Refresh both workers and summary
   */
  const refresh = useCallback(async () => {
    setIsLoading(true);
    await Promise.all([fetchWorkers(), fetchSummary ? fetchSummaryData() : Promise.resolve()]);
    if (isMountedRef.current) {
      setIsLoading(false);
    }
  }, [fetchWorkers, fetchSummary, fetchSummaryData]);

  // Initial fetch and auto-refresh setup
  useEffect(() => {
    isMountedRef.current = true;

    // Initial fetch
    refresh();

    // Setup auto-refresh
    if (autoRefresh) {
      refreshIntervalRef.current = window.setInterval(() => {
        fetchWorkers();
        if (fetchSummary) {
          fetchSummaryData();
        }
      }, refreshInterval);
    }

    // Cleanup
    return () => {
      isMountedRef.current = false;
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [refresh, fetchWorkers, fetchSummaryData, autoRefresh, refreshInterval, fetchSummary]);

  return {
    workers,
    summary,
    isLoading,
    error,
    refresh,
  };
}
