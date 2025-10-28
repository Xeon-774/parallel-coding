/**
 * Metrics Type Definitions
 *
 * TypeScript types for hybrid engine metrics and dashboard data.
 */

/**
 * Hybrid engine metrics snapshot
 */
export interface HybridMetrics {
  /** Total number of decisions made */
  total_decisions: number;

  /** Number of decisions made by rules */
  rules_decisions: number;

  /** Number of decisions made by AI */
  ai_decisions: number;

  /** Number of template fallbacks */
  template_fallbacks: number;

  /** Average latency in milliseconds */
  average_latency_ms: number;

  /** Percentage of decisions made by rules */
  rules_percentage: number;
}

/**
 * Decision event from history
 */
export interface DecisionEvent {
  /** Unix timestamp */
  timestamp: number;

  /** Worker identifier */
  worker_id: string;

  /** Decision type (approve/deny) */
  decision_type: string;

  /** Who made the decision (rules/ai/template) */
  decided_by: 'rules' | 'ai' | 'template';

  /** Latency in milliseconds */
  latency_ms: number;

  /** Whether this was a fallback */
  is_fallback: boolean;

  /** Confirmation type */
  confirmation_type: string;

  /** Decision reasoning */
  reasoning: string;
}

/**
 * Chart data for pie chart
 */
export interface PieChartData {
  name: string;
  value: number;
  color: string;
  [key: string]: string | number;  // Index signature for recharts compatibility
}

/**
 * Chart data for trend/line chart
 */
export interface TrendChartData {
  timestamp: number;
  time: string;
  rules: number;
  ai: number;
  template: number;
}

/**
 * Metrics API response for current metrics
 */
export interface MetricsResponse {
  total_decisions: number;
  rules_decisions: number;
  ai_decisions: number;
  template_fallbacks: number;
  average_latency_ms: number;
  rules_percentage: number;
}

/**
 * Decisions API response
 */
export interface DecisionsResponse {
  decisions: DecisionEvent[];
  count: number;
}
