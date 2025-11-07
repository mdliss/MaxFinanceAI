'use client'

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { EvaluationMetrics as MetricsType } from '@/types';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

export default function EvaluationMetrics() {
  const [metrics, setMetrics] = useState<MetricsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getEvaluationMetrics();
      setMetrics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load metrics');
    } finally {
      setLoading(false);
    }
  };

  const exportToJSON = () => {
    if (!metrics) return;
    const dataStr = JSON.stringify(metrics, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `evaluation-metrics-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const exportToCSV = () => {
    if (!metrics) return;

    const csvRows = [
      ['Metric Category', 'Metric Name', 'Value'],
      ['Coverage', 'Total Users', metrics.coverage.total_users],
      ['Coverage', 'Users with Persona', metrics.coverage.users_with_persona],
      ['Coverage', 'Users with 3+ Behaviors', metrics.coverage.users_with_3plus_behaviors],
      ['Coverage', 'Coverage %', metrics.coverage.coverage_percentage],
      ['Explainability', 'Total Recommendations', metrics.explainability.total_recommendations],
      ['Explainability', 'With Rationale', metrics.explainability.recommendations_with_rationale],
      ['Explainability', 'Explainability %', metrics.explainability.explainability_percentage],
      ['Latency', 'Average (ms)', metrics.latency.avg_recommendation_generation_ms],
      ['Latency', 'P50 (ms)', metrics.latency.p50_ms],
      ['Latency', 'P95 (ms)', metrics.latency.p95_ms],
      ['Latency', 'P99 (ms)', metrics.latency.p99_ms],
      ['Auditability', 'Total Recommendations', metrics.auditability.total_recommendations],
      ['Auditability', 'With Traces', metrics.auditability.recommendations_with_traces],
      ['Auditability', 'Auditability %', metrics.auditability.auditability_percentage],
      ['Quality', 'Avg Behaviors per User', metrics.quality.avg_behaviors_per_user],
      ['Quality', 'Personas Assigned', metrics.quality.personas_assigned],
      ['Quality', 'Flagged', metrics.quality.recommendations_flagged],
      ['Quality', 'Flag Rate %', metrics.quality.flag_rate_percentage],
    ];

    const csvContent = csvRows.map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `evaluation-metrics-${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="card-dark p-8 transition-smooth">
        <div className="animate-pulse space-y-6">
          <div className="h-6 bg-[var(--bg-tertiary)] rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="h-32 bg-[var(--bg-tertiary)] rounded"></div>
            <div className="h-32 bg-[var(--bg-tertiary)] rounded"></div>
            <div className="h-32 bg-[var(--bg-tertiary)] rounded"></div>
            <div className="h-32 bg-[var(--bg-tertiary)] rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="card-dark p-8 transition-smooth border-l-4 border-red-500">
        <p className="text-red-700">{error || 'Unable to load evaluation metrics'}</p>
        <button onClick={loadMetrics} className="mt-4 btn-accent transition-smooth">
          Retry
        </button>
      </div>
    );
  }

  const getStatusColor = (percentage: number, target: number = 100) => {
    if (percentage >= target) return 'text-slate-700 bg-slate-500/10';
    if (percentage >= target * 0.8) return 'text-amber-700 bg-amber-500/10';
    return 'text-red-700 bg-red-500/10';
  };

  const getLatencyColor = (ms: number) => {
    if (ms < 2000) return 'text-slate-700 bg-slate-500/10';
    if (ms < 5000) return 'text-amber-700 bg-amber-500/10';
    return 'text-red-700 bg-red-500/10';
  };

  // Prepare data for charts
  const coverageData = [
    { name: 'With Persona & 3+ Behaviors', value: metrics.coverage.users_with_3plus_behaviors },
    { name: 'Missing Criteria', value: metrics.coverage.total_users - metrics.coverage.users_with_3plus_behaviors },
  ];

  const explainabilityData = [
    { name: 'With Rationale', value: metrics.explainability.recommendations_with_rationale },
    { name: 'Without Rationale', value: metrics.explainability.total_recommendations - metrics.explainability.recommendations_with_rationale },
  ];

  const latencyData = [
    { name: 'P50', value: metrics.latency.p50_ms },
    { name: 'P95', value: metrics.latency.p95_ms },
    { name: 'P99', value: metrics.latency.p99_ms },
    { name: 'Avg', value: metrics.latency.avg_recommendation_generation_ms },
  ];

  const CHART_COLORS = ['#2c3e50', '#cbd5e1'];

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-semibold mb-2">System Evaluation Metrics</h2>
          <p className="text-sm text-[var(--text-secondary)]">
            Performance metrics required by rubric • Last updated: {new Date(metrics.timestamp).toLocaleString()}
          </p>
        </div>
        <div className="flex gap-3">
          <button onClick={exportToJSON} className="btn-secondary transition-smooth">
            Export JSON
          </button>
          <button onClick={exportToCSV} className="btn-accent transition-smooth">
            Export CSV
          </button>
          <button onClick={loadMetrics} className="btn-secondary transition-smooth">
            Refresh
          </button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {/* Coverage */}
        <div className="card-dark p-6 transition-smooth">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase">Coverage</h3>
            <span className={`px-3 py-1 rounded-full text-xs font-medium transition-smooth ${getStatusColor(metrics.coverage.coverage_percentage)}`}>
              {metrics.coverage.coverage_percentage.toFixed(1)}%
            </span>
          </div>
          <p className="text-3xl font-bold mb-2">{metrics.coverage.users_with_3plus_behaviors}</p>
          <p className="text-sm text-[var(--text-secondary)]">
            of {metrics.coverage.total_users} users with persona + ≥3 behaviors
          </p>
          <div className="mt-4 text-xs text-[var(--text-muted)]">
            Target: 100%
          </div>
        </div>

        {/* Explainability */}
        <div className="card-dark p-6 transition-smooth">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase">Explainability</h3>
            <span className={`px-3 py-1 rounded-full text-xs font-medium transition-smooth ${getStatusColor(metrics.explainability.explainability_percentage)}`}>
              {metrics.explainability.explainability_percentage.toFixed(1)}%
            </span>
          </div>
          <p className="text-3xl font-bold mb-2">{metrics.explainability.recommendations_with_rationale}</p>
          <p className="text-sm text-[var(--text-secondary)]">
            of {metrics.explainability.total_recommendations} recommendations with rationales
          </p>
          <div className="mt-4 text-xs text-[var(--text-muted)]">
            Target: 100%
          </div>
        </div>

        {/* Latency */}
        <div className="card-dark p-6 transition-smooth">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase">Latency</h3>
            <span className={`px-3 py-1 rounded-full text-xs font-medium transition-smooth ${getLatencyColor(metrics.latency.avg_recommendation_generation_ms)}`}>
              {(metrics.latency.avg_recommendation_generation_ms / 1000).toFixed(2)}s
            </span>
          </div>
          <p className="text-3xl font-bold mb-2">{metrics.latency.p95_ms}</p>
          <p className="text-sm text-[var(--text-secondary)]">
            P95 latency (ms)
          </p>
          <div className="mt-4 text-xs text-[var(--text-muted)]">
            Target: &lt;5s avg
          </div>
        </div>

        {/* Auditability */}
        <div className="card-dark p-6 transition-smooth">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase">Auditability</h3>
            <span className={`px-3 py-1 rounded-full text-xs font-medium transition-smooth ${getStatusColor(metrics.auditability.auditability_percentage)}`}>
              {metrics.auditability.auditability_percentage.toFixed(1)}%
            </span>
          </div>
          <p className="text-3xl font-bold mb-2">{metrics.auditability.recommendations_with_traces}</p>
          <p className="text-sm text-[var(--text-secondary)]">
            of {metrics.auditability.total_recommendations} with decision traces
          </p>
          <div className="mt-4 text-xs text-[var(--text-muted)]">
            Target: 100%
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Coverage Chart */}
        <div className="card-dark p-6 transition-smooth">
          <h3 className="text-sm font-semibold mb-4 uppercase tracking-wide">Coverage Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={coverageData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {coverageData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={CHART_COLORS[index]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Explainability Chart */}
        <div className="card-dark p-6 transition-smooth">
          <h3 className="text-sm font-semibold mb-4 uppercase tracking-wide">Explainability Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={explainabilityData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {explainabilityData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={CHART_COLORS[index]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Latency Chart */}
        <div className="card-dark p-6 transition-smooth">
          <h3 className="text-sm font-semibold mb-4 uppercase tracking-wide">Latency Percentiles (ms)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={latencyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#d4d4d2" opacity={0.5} />
              <XAxis dataKey="name" stroke="#6b6b6b" tick={{ fill: '#6b6b6b', fontSize: 12 }} />
              <YAxis stroke="#6b6b6b" tick={{ fill: '#6b6b6b', fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#2c3e50" className="transition-smooth" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Quality Metrics */}
      <div className="card-dark p-6 transition-smooth">
        <h3 className="text-lg font-semibold mb-4">Quality Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div>
            <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide mb-1">Avg Behaviors/User</p>
            <p className="text-2xl font-bold">{metrics.quality.avg_behaviors_per_user.toFixed(1)}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide mb-1">Personas Assigned</p>
            <p className="text-2xl font-bold">{metrics.quality.personas_assigned}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide mb-1">Recommendations Flagged</p>
            <p className="text-2xl font-bold">{metrics.quality.recommendations_flagged}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide mb-1">Flag Rate</p>
            <p className="text-2xl font-bold">{metrics.quality.flag_rate_percentage.toFixed(1)}%</p>
          </div>
        </div>
      </div>

      {/* Rubric Compliance */}
      <div className="mt-6 card-dark p-6 transition-smooth border-l-4 border-[var(--accent-primary)]">
        <h3 className="text-lg font-semibold mb-4">Rubric Compliance Summary</h3>
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span>Coverage (users with persona + ≥3 behaviors)</span>
            <span className={`font-semibold ${metrics.coverage.coverage_percentage >= 100 ? 'text-slate-700' : 'text-red-700'}`}>
              {metrics.coverage.coverage_percentage >= 100 ? 'PASS' : 'FAIL'} ({metrics.coverage.coverage_percentage.toFixed(1)}% / 100%)
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>Explainability (recommendations with rationales)</span>
            <span className={`font-semibold ${metrics.explainability.explainability_percentage >= 100 ? 'text-slate-700' : 'text-red-700'}`}>
              {metrics.explainability.explainability_percentage >= 100 ? 'PASS' : 'FAIL'} ({metrics.explainability.explainability_percentage.toFixed(1)}% / 100%)
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>Latency (avg time to generate recommendations)</span>
            <span className={`font-semibold ${metrics.latency.avg_recommendation_generation_ms < 5000 ? 'text-slate-700' : 'text-red-700'}`}>
              {metrics.latency.avg_recommendation_generation_ms < 5000 ? 'PASS' : 'FAIL'} ({(metrics.latency.avg_recommendation_generation_ms / 1000).toFixed(2)}s / &lt;5s)
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>Auditability (recommendations with decision traces)</span>
            <span className={`font-semibold ${metrics.auditability.auditability_percentage >= 100 ? 'text-slate-700' : 'text-red-700'}`}>
              {metrics.auditability.auditability_percentage >= 100 ? 'PASS' : 'FAIL'} ({metrics.auditability.auditability_percentage.toFixed(1)}% / 100%)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
