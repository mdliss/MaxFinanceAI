'use client'

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { AuditLog as AuditLogType } from '@/types';

interface AuditLogProps {
  userId: string | null;
}

export default function AuditLog({ userId }: AuditLogProps) {
  const [logs, setLogs] = useState<AuditLogType[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [limit, setLimit] = useState(100);

  useEffect(() => {
    loadLogs();
  }, [userId, limit]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getAuditLogs(userId || undefined, limit);
      setLogs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  const getActionBadge = (action: string) => {
    const actionLower = action.toLowerCase();
    if (actionLower.includes('approve')) {
      return <span className="px-2 py-1 bg-green-900/30 text-green-400 rounded text-xs transition-smooth">Approve</span>;
    }
    if (actionLower.includes('flag')) {
      return <span className="px-2 py-1 bg-orange-900/30 text-orange-400 rounded text-xs transition-smooth">Flag</span>;
    }
    if (actionLower.includes('override')) {
      return <span className="px-2 py-1 bg-blue-900/30 text-blue-400 rounded text-xs transition-smooth">Override</span>;
    }
    if (actionLower.includes('reject')) {
      return <span className="px-2 py-1 bg-red-900/30 text-red-400 rounded text-xs transition-smooth">Reject</span>;
    }
    return <span className="px-2 py-1 bg-gray-700/30 text-gray-400 rounded text-xs transition-smooth">{action}</span>;
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold">
            {userId ? `Audit Log for User ${userId}` : 'All Audit Logs'}
          </h2>
          <p className="text-sm text-[var(--text-secondary)] mt-1">{logs.length} log entries</p>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-sm text-[var(--text-secondary)]">Show:</label>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-sm focus:ring-2 focus:ring-[var(--accent-primary)] transition-smooth"
          >
            <option value={50}>50 entries</option>
            <option value={100}>100 entries</option>
            <option value={250}>250 entries</option>
            <option value={500}>500 entries</option>
          </select>

          <button
            onClick={loadLogs}
            className="btn-accent text-sm transition-smooth"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && <div className="text-center py-12 text-[var(--text-secondary)]">Loading audit logs...</div>}

      {error && (
        <div className="card-dark border border-red-500 p-4 text-red-400 transition-smooth">{error}</div>
      )}

      {/* Audit Logs Table */}
      {!loading && !error && logs.length === 0 && (
        <div className="text-center py-12 text-[var(--text-secondary)]">No audit logs found</div>
      )}

      {!loading && !error && logs.length > 0 && (
        <div className="card-dark overflow-hidden transition-smooth">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-[var(--bg-secondary)] border-b border-[var(--border-color)]">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[var(--text-muted)] uppercase">
                    Timestamp
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[var(--text-muted)] uppercase">
                    Action
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[var(--text-muted)] uppercase">
                    Actor
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[var(--text-muted)] uppercase">
                    User ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[var(--text-muted)] uppercase">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-color)]">
                {logs.map((log) => (
                  <tr key={log.log_id} className="hover:bg-[var(--bg-tertiary)] transition-smooth">
                    <td className="px-4 py-3 text-sm">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-sm">{getActionBadge(log.action)}</td>
                    <td className="px-4 py-3 text-sm">{log.actor}</td>
                    <td className="px-4 py-3 text-sm text-[var(--text-secondary)]">
                      {log.user_id || <span className="text-[var(--text-muted)]">—</span>}
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--text-secondary)] max-w-md truncate">
                      {log.details || <span className="text-[var(--text-muted)]">—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Stats */}
          <div className="bg-[var(--bg-secondary)] px-4 py-3 border-t border-[var(--border-color)]">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)]">
              <span>Total Entries: {logs.length}</span>
              <span>
                Latest:{' '}
                {logs.length > 0
                  ? new Date(logs[0].timestamp).toLocaleString()
                  : 'No logs'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
