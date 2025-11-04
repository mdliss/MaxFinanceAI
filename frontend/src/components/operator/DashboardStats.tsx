'use client'

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export default function DashboardStats() {
  const [stats, setStats] = useState<any>(null);
  const [priorityQueue, setPriorityQueue] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [autoFlagging, setAutoFlagging] = useState(false);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const [dashboardStats, queueStats] = await Promise.all([
        api.getDashboardStats(),
        api.getPriorityQueue(),
      ]);
      setStats(dashboardStats);
      setPriorityQueue(queueStats);
    } catch (err) {
      console.error('Failed to load stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAutoFlag = async () => {
    try {
      setAutoFlagging(true);
      const result = await api.autoFlagRecommendations();

      // Improved feedback message with better context
      const feedbackMessage = `${result.message}\n\n` +
        `📊 Summary:\n` +
        `• Newly flagged: ${result.newly_flagged_count}\n` +
        `• Total in review queue: ${result.total_in_review}\n` +
        `• Total scanned: ${result.total_scanned}\n\n` +
        `🔍 Rules applied:\n${result.rules_applied.map((r: string) => `  • ${r}`).join('\n')}`;

      alert(feedbackMessage);
      await loadStats(); // Refresh stats
    } catch (err) {
      alert('Failed to auto-flag recommendations');
      console.error(err);
    } finally {
      setAutoFlagging(false);
    }
  };

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card-dark p-6">
              <div className="h-4 bg-[var(--bg-tertiary)] rounded w-1/2 mb-4"></div>
              <div className="h-8 bg-[var(--bg-tertiary)] rounded w-3/4"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!stats || !priorityQueue) {
    return null;
  }

  const reviewCount = priorityQueue.flagged_count || 0;
  const pendingCount = priorityQueue.pending_count || 0;
  const highRiskCount = priorityQueue.high_risk_approved_count || 0;

  return (
    <div>
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Needs Review */}
        <div className="card-dark p-6 border-l-4 border-red-500 transition-smooth">
          <p className="text-sm font-medium text-[var(--text-secondary)]">Needs Review</p>
          <p className="text-3xl font-bold text-red-500 mt-1">{reviewCount}</p>
          <p className="text-xs text-[var(--text-muted)] mt-1">Flagged for attention</p>
        </div>

        {/* Pending */}
        <div className="card-dark p-6 border-l-4 border-yellow-500 transition-smooth">
          <p className="text-sm font-medium text-[var(--text-secondary)]">Pending</p>
          <p className="text-3xl font-bold text-yellow-500 mt-1">{pendingCount}</p>
          <p className="text-xs text-[var(--text-muted)] mt-1">Awaiting approval</p>
        </div>

        {/* Approved */}
        <div className="card-dark p-6 border-l-4 border-green-500 transition-smooth">
          <p className="text-sm font-medium text-[var(--text-secondary)]">Approved</p>
          <p className="text-3xl font-bold text-green-500 mt-1">
            {stats.approved_recommendations}
          </p>
          <p className="text-xs text-[var(--text-muted)] mt-1">Ready for delivery</p>
        </div>

        {/* Total Users */}
        <div className="card-dark p-6 border-l-4 border-[var(--accent-primary)] transition-smooth">
          <p className="text-sm font-medium text-[var(--text-secondary)]">Active Users</p>
          <p className="text-3xl font-bold text-[var(--accent-primary)] mt-1">
            {stats.users_with_consent}
          </p>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            of {stats.total_users} total
          </p>
        </div>
      </div>

      {/* Workflow Guide */}
      <div className="card-dark p-6 mb-6 border-l-4 border-[var(--accent-primary)] transition-smooth">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold">Operator Workflow</h3>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              Follow these steps to review recommendations efficiently
            </p>
          </div>
          <button
            onClick={handleAutoFlag}
            disabled={autoFlagging}
            className="btn-accent transition-smooth disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {autoFlagging ? 'Auto-Flagging...' : 'Run Auto-Flag'}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {priorityQueue.workflow_steps.map((step: any) => (
            <div
              key={step.step}
              className="bg-[var(--bg-secondary)] p-4 rounded-lg border-2 border-[var(--border-color)] transition-smooth hover:border-[var(--accent-primary)]"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-8 rounded-full bg-[var(--accent-primary)] text-[var(--bg-primary)] flex items-center justify-center font-bold">
                  {step.step}
                </div>
                <div>
                  <h4 className="font-semibold">{step.title}</h4>
                  <p className="text-sm text-[var(--text-secondary)]">
                    {step.count} item{step.count !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>
              {step.count > 0 && (
                <div className="mt-2">
                  <div className="w-full bg-[var(--bg-tertiary)] rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-smooth ${
                        step.status === 'review'
                          ? 'bg-red-500'
                          : step.status === 'pending'
                          ? 'bg-yellow-500'
                          : 'bg-green-500'
                      }`}
                      style={{ width: '100%' }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card-dark p-4 transition-smooth">
          <p className="text-sm text-[var(--text-secondary)]">Total Recommendations</p>
          <p className="text-2xl font-bold mt-1">
            {stats.total_recommendations}
          </p>
        </div>
        <div className="card-dark p-4 transition-smooth">
          <p className="text-sm text-[var(--text-secondary)]">Behavioral Signals</p>
          <p className="text-2xl font-bold mt-1">
            {stats.total_signals}
          </p>
        </div>
        <div className="card-dark p-4 transition-smooth">
          <p className="text-sm text-[var(--text-secondary)]">Recent Consent Changes</p>
          <p className="text-2xl font-bold mt-1">
            {stats.recent_consent_changes} <span className="text-sm text-[var(--text-muted)]">(7 days)</span>
          </p>
        </div>
      </div>
    </div>
  );
}
