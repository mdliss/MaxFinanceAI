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
            <div key={i} className="bg-white p-6 rounded-lg shadow-sm">
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="h-8 bg-gray-200 rounded w-3/4"></div>
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
        <div className="bg-white p-6 rounded-lg shadow-sm border-l-4 border-red-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Needs Review</p>
              <p className="text-3xl font-bold text-red-600 mt-1">{reviewCount}</p>
              <p className="text-xs text-gray-500 mt-1">Flagged for attention</p>
            </div>
            <div className="text-red-500 text-4xl">🚩</div>
          </div>
        </div>

        {/* Pending */}
        <div className="bg-white p-6 rounded-lg shadow-sm border-l-4 border-yellow-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Pending</p>
              <p className="text-3xl font-bold text-yellow-600 mt-1">{pendingCount}</p>
              <p className="text-xs text-gray-500 mt-1">Awaiting approval</p>
            </div>
            <div className="text-yellow-500 text-4xl">⏳</div>
          </div>
        </div>

        {/* Approved */}
        <div className="bg-white p-6 rounded-lg shadow-sm border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Approved</p>
              <p className="text-3xl font-bold text-green-600 mt-1">
                {stats.approved_recommendations}
              </p>
              <p className="text-xs text-gray-500 mt-1">Ready for delivery</p>
            </div>
            <div className="text-green-500 text-4xl">✅</div>
          </div>
        </div>

        {/* Total Users */}
        <div className="bg-white p-6 rounded-lg shadow-sm border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Users</p>
              <p className="text-3xl font-bold text-blue-600 mt-1">
                {stats.users_with_consent}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                of {stats.total_users} total
              </p>
            </div>
            <div className="text-blue-500 text-4xl">👥</div>
          </div>
        </div>
      </div>

      {/* Workflow Guide */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg shadow-sm mb-6 border border-blue-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Operator Workflow</h3>
            <p className="text-sm text-gray-600 mt-1">
              Follow these steps to review recommendations efficiently
            </p>
          </div>
          <button
            onClick={handleAutoFlag}
            disabled={autoFlagging}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {autoFlagging ? (
              <>
                <span className="animate-spin">⚙️</span> Auto-Flagging...
              </>
            ) : (
              <>
                <span>🤖</span> Run Auto-Flag
              </>
            )}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {priorityQueue.workflow_steps.map((step: any) => (
            <div
              key={step.step}
              className="bg-white p-4 rounded-lg border-2 border-blue-200"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold">
                  {step.step}
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">{step.title}</h4>
                  <p className="text-sm text-gray-600">
                    {step.count} item{step.count !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>
              {step.count > 0 && (
                <div className="mt-2">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
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
        <div className="bg-white p-4 rounded-lg shadow-sm">
          <p className="text-sm text-gray-600">Total Recommendations</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {stats.total_recommendations}
          </p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm">
          <p className="text-sm text-gray-600">Behavioral Signals</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {stats.total_signals}
          </p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm">
          <p className="text-sm text-gray-600">Recent Consent Changes</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {stats.recent_consent_changes} (7 days)
          </p>
        </div>
      </div>
    </div>
  );
}
