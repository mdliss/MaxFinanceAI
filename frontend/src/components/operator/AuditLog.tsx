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
      return <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">Approve</span>;
    }
    if (actionLower.includes('flag')) {
      return <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs">Flag</span>;
    }
    if (actionLower.includes('override')) {
      return <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">Override</span>;
    }
    if (actionLower.includes('reject')) {
      return <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs">Reject</span>;
    }
    return <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">{action}</span>;
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            {userId ? `Audit Log for User ${userId}` : 'All Audit Logs'}
          </h2>
          <p className="text-sm text-gray-600 mt-1">{logs.length} log entries</p>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-600">Show:</label>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          >
            <option value={50}>50 entries</option>
            <option value={100}>100 entries</option>
            <option value={250}>250 entries</option>
            <option value={500}>500 entries</option>
          </select>

          <button
            onClick={loadLogs}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 text-sm"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && <div className="text-center py-12 text-gray-500">Loading audit logs...</div>}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>
      )}

      {/* Audit Logs Table */}
      {!loading && !error && logs.length === 0 && (
        <div className="text-center py-12 text-gray-500">No audit logs found</div>
      )}

      {!loading && !error && logs.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">
                    Timestamp
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">
                    Action
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">
                    Actor
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">
                    User ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {logs.map((log) => (
                  <tr key={log.log_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-sm">{getActionBadge(log.action)}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">{log.actor}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {log.user_id || <span className="text-gray-400">—</span>}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 max-w-md truncate">
                      {log.details || <span className="text-gray-400">—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Stats */}
          <div className="bg-gray-50 px-4 py-3 border-t border-gray-200">
            <div className="flex items-center justify-between text-xs text-gray-600">
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
