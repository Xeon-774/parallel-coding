/**
 * MetricsDashboard Component
 *
 * Displays hybrid engine decision metrics in real-time.
 *
 * Features:
 * - Real-time metrics cards (total decisions, avg latency, rules efficiency)
 * - Pie chart showing decision distribution (rules/AI/template)
 * - Decision history table with filtering
 * - Auto-refresh every 5 seconds
 *
 * Usage:
 *   <MetricsDashboard />
 */

import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import type { HybridMetrics, DecisionEvent, PieChartData } from '../types/metrics';

const API_BASE_URL = 'http://localhost:8000';
const REFRESH_INTERVAL = 5000; // 5 seconds

/**
 * Format number with K/M suffix
 */
function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

/**
 * Format latency in milliseconds
 */
function formatLatency(ms: number): string {
  if (ms < 1) {
    return '<1ms';
  }
  if (ms >= 1000) {
    return (ms / 1000).toFixed(2) + 's';
  }
  return ms.toFixed(1) + 'ms';
}

/**
 * MetricCard Component
 */
interface MetricCardProps {
  title: string;
  value: string | number;
  icon: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  color?: string;
}

function MetricCard({ title, value, icon, trend, trendValue, color = 'blue' }: MetricCardProps) {
  const trendColors = {
    up: 'text-green-400',
    down: 'text-red-400',
    neutral: 'text-gray-400'
  };

  const trendIcons = {
    up: '↑',
    down: '↓',
    neutral: '→'
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-400">{title}</h3>
        <span className="text-2xl">{icon}</span>
      </div>
      <div className="flex items-baseline justify-between">
        <div className={`text-3xl font-bold text-${color}-400`}>
          {value}
        </div>
        {trend && trendValue && (
          <div className={`text-sm ${trendColors[trend]} flex items-center gap-1`}>
            <span>{trendIcons[trend]}</span>
            <span>{trendValue}</span>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Main MetricsDashboard Component
 */
export function MetricsDashboard() {
  const [metrics, setMetrics] = useState<HybridMetrics | null>(null);
  const [decisions, setDecisions] = useState<DecisionEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  /**
   * Fetch current metrics from API
   */
  const fetchMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/metrics/current`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data: HybridMetrics = await response.json();
      setMetrics(data);
      setError(null);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Fetch recent decisions from API
   */
  const fetchDecisions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/decisions/recent?limit=100`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data: DecisionEvent[] = await response.json();
      setDecisions(data);
    } catch (err) {
      console.error('Failed to fetch decisions:', err);
    }
  };

  // Initial fetch and auto-refresh
  useEffect(() => {
    fetchMetrics();
    fetchDecisions();

    const interval = setInterval(() => {
      fetchMetrics();
      fetchDecisions();
    }, REFRESH_INTERVAL);

    return () => clearInterval(interval);
  }, []);

  // Prepare pie chart data
  const pieData: PieChartData[] = metrics
    ? [
        { name: 'Rules', value: metrics.rules_decisions, color: '#10b981' },
        { name: 'AI', value: metrics.ai_decisions, color: '#3b82f6' },
        { name: 'Template', value: metrics.template_fallbacks, color: '#f59e0b' }
      ]
    : [];

  // Loading state
  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-900">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-gray-600 border-t-blue-500 mb-4"></div>
          <p className="text-gray-400">Loading metrics...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !metrics) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-900">
        <div className="text-center max-w-md">
          <div className="text-red-400 text-5xl mb-4">⚠</div>
          <p className="text-red-400 text-lg font-semibold mb-2">Failed to Load Metrics</p>
          <p className="text-gray-400 mb-4">{error}</p>
          <button
            onClick={() => {
              setLoading(true);
              fetchMetrics();
              fetchDecisions();
            }}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return null;
  }

  const aiPercentage = metrics.total_decisions > 0
    ? ((metrics.ai_decisions / metrics.total_decisions) * 100).toFixed(1)
    : '0.0';

  const fallbackPercentage = metrics.total_decisions > 0
    ? ((metrics.template_fallbacks / metrics.total_decisions) * 100).toFixed(1)
    : '0.0';

  return (
    <div className="flex flex-col h-full bg-gray-900 p-6 space-y-6 overflow-y-auto custom-scrollbar">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Hybrid Engine Metrics</h1>
          <p className="text-sm text-gray-400 mt-1">
            Real-time decision statistics and performance monitoring
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-xs text-gray-500">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </div>
          <span className="inline-block w-2 h-2 bg-green-500 rounded-full live-pulse"></span>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Decisions"
          value={formatNumber(metrics.total_decisions)}
          icon="📊"
          color="blue"
        />
        <MetricCard
          title="Avg Response Time"
          value={formatLatency(metrics.average_latency_ms)}
          icon="⏱️"
          color="purple"
        />
        <MetricCard
          title="Rules Efficiency"
          value={`${metrics.rules_percentage.toFixed(1)}%`}
          icon="⚡"
          trend={metrics.rules_percentage > 80 ? 'up' : metrics.rules_percentage < 50 ? 'down' : 'neutral'}
          trendValue={`${metrics.rules_decisions} decisions`}
          color="green"
        />
        <MetricCard
          title="AI Decisions"
          value={`${aiPercentage}%`}
          icon="🤖"
          trendValue={`${metrics.ai_decisions} decisions`}
          color="blue"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Decision Distribution Pie Chart */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-lg font-semibold text-white mb-4">Decision Distribution</h2>
          {metrics.total_decisions > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(props: any) => `${props.name} ${(props.percent * 100).toFixed(1)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '0.5rem'
                  }}
                />
                <Legend
                  wrapperStyle={{ color: '#9ca3af' }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-500">
              <p>No decisions yet</p>
            </div>
          )}
        </div>

        {/* Statistics Panel */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-lg font-semibold text-white mb-4">Performance Statistics</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Rules Decisions</span>
              <span className="text-green-400 font-semibold">{metrics.rules_decisions}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">AI Decisions</span>
              <span className="text-blue-400 font-semibold">{metrics.ai_decisions}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Template Fallbacks</span>
              <span className="text-yellow-400 font-semibold">
                {metrics.template_fallbacks} ({fallbackPercentage}%)
              </span>
            </div>
            <div className="pt-4 border-t border-gray-700">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Average Latency</span>
                <span className="text-purple-400 font-semibold">
                  {formatLatency(metrics.average_latency_ms)}
                </span>
              </div>
            </div>
            <div className="pt-4 border-t border-gray-700">
              <div className="text-sm text-gray-500">
                <p>Rules provide fast responses (&lt;1ms)</p>
                <p className="mt-1">AI decisions average ~7 seconds</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Decision History Table */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-lg font-semibold text-white mb-4">
          Recent Decisions ({decisions.length})
        </h2>
        {decisions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b border-gray-700">
                  <th className="pb-3 text-gray-400 font-medium">Time</th>
                  <th className="pb-3 text-gray-400 font-medium">Worker</th>
                  <th className="pb-3 text-gray-400 font-medium">Type</th>
                  <th className="pb-3 text-gray-400 font-medium">Decided By</th>
                  <th className="pb-3 text-gray-400 font-medium">Latency</th>
                  <th className="pb-3 text-gray-400 font-medium">Result</th>
                </tr>
              </thead>
              <tbody>
                {decisions.slice(0, 20).map((decision, idx) => (
                  <tr key={idx} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                    <td className="py-3 text-gray-300">
                      {new Date(decision.timestamp * 1000).toLocaleTimeString()}
                    </td>
                    <td className="py-3 text-gray-300 font-mono text-xs">
                      {decision.worker_id}
                    </td>
                    <td className="py-3 text-gray-300">{decision.confirmation_type}</td>
                    <td className="py-3">
                      <span
                        className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                          decision.decided_by === 'rules'
                            ? 'bg-green-900 text-green-300'
                            : decision.decided_by === 'ai'
                            ? 'bg-blue-900 text-blue-300'
                            : 'bg-yellow-900 text-yellow-300'
                        }`}
                      >
                        {decision.decided_by}
                      </span>
                    </td>
                    <td className="py-3 text-gray-300">{formatLatency(decision.latency_ms)}</td>
                    <td className="py-3">
                      <span
                        className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                          decision.decision_type === 'approve'
                            ? 'bg-green-900 text-green-300'
                            : 'bg-red-900 text-red-300'
                        }`}
                      >
                        {decision.decision_type}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p>No decision history available</p>
            <p className="text-sm mt-2">Decisions will appear here as workers make them</p>
          </div>
        )}
      </div>
    </div>
  );
}
