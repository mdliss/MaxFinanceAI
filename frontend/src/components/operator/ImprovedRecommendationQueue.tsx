'use client'

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { Recommendation } from '@/types';

export default function ImprovedRecommendationQueue() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [filteredRecs, setFilteredRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [personaFilter, setPersonaFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRec, setSelectedRec] = useState<Recommendation | null>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  useEffect(() => {
    loadRecommendations();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [recommendations, statusFilter, personaFilter, searchTerm]);

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getAllRecommendations();
      setRecommendations(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load recommendations');
      console.error('Load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...recommendations];

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(r => r.approval_status === statusFilter);
    }

    // Persona filter
    if (personaFilter !== 'all') {
      filtered = filtered.filter(r => r.persona_type === personaFilter);
    }

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        r =>
          r.title?.toLowerCase().includes(term) ||
          r.description?.toLowerCase().includes(term) ||
          r.user_id?.toLowerCase().includes(term)
      );
    }

    setFilteredRecs(filtered);
  };

  const handleApprove = async (recId: number) => {
    try {
      await api.approveRecommendation(recId);
      await loadRecommendations();
    } catch (err) {
      alert('Failed to approve recommendation');
    }
  };

  const handleFlag = async (recId: number) => {
    const reason = prompt('Enter flag reason:');
    if (!reason) return;

    const severity = prompt('Enter severity (low/medium/high):') as 'low' | 'medium' | 'high';
    if (!severity || !['low', 'medium', 'high'].includes(severity)) {
      alert('Invalid severity');
      return;
    }

    try {
      await api.flagRecommendation(recId, reason, severity);
      await loadRecommendations();
    } catch (err) {
      alert('Failed to flag recommendation');
    }
  };

  const viewDetails = async (rec: Recommendation) => {
    setSelectedRec(rec);
    try {
      const logs = await api.getAuditLogs(rec.user_id, 50);
      setAuditLogs(logs);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
      setAuditLogs([]);
    }
  };

  const getStatusBadge = (status: string) => {
    const badges: Record<string, { bg: string; text: string; icon: string }> = {
      review: { bg: 'bg-red-100', text: 'text-red-800', icon: '🚩' },
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: '⏳' },
      approved: { bg: 'bg-green-100', text: 'text-green-800', icon: '✅' },
      rejected: { bg: 'bg-gray-100', text: 'text-gray-800', icon: '❌' },
    };
    const badge = badges[status] || badges.pending;
    return (
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${badge.bg} ${badge.text}`}>
        <span>{badge.icon}</span>
        {status.toUpperCase()}
      </span>
    );
  };

  const getPersonaBadge = (persona: string) => {
    const colors: Record<string, string> = {
      financial_newcomer: 'bg-blue-100 text-blue-800',
      credit_optimizer: 'bg-purple-100 text-purple-800',
      savings_builder: 'bg-green-100 text-green-800',
      subscription_heavy: 'bg-orange-100 text-orange-800',
      variable_income: 'bg-pink-100 text-pink-800',
    };
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${colors[persona] || 'bg-gray-100 text-gray-800'}`}>
        {persona.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  const uniquePersonas = Array.from(new Set(recommendations.map(r => r.persona_type)));

  if (loading) {
    return <div className="text-center py-12">Loading recommendations...</div>;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
        <button
          onClick={loadRecommendations}
          className="mt-2 text-red-600 underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search
            </label>
            <input
              type="text"
              placeholder="Search by title, user..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Statuses</option>
              <option value="review">🚩 Flagged/Review</option>
              <option value="pending">⏳ Pending</option>
              <option value="approved">✅ Approved</option>
              <option value="rejected">❌ Rejected</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Persona
            </label>
            <select
              value={personaFilter}
              onChange={(e) => setPersonaFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Personas</option>
              {uniquePersonas.map(persona => (
                <option key={persona} value={persona}>
                  {persona.replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Results
            </label>
            <div className="px-3 py-2 bg-gray-100 rounded-lg text-center font-semibold">
              {filteredRecs.length} of {recommendations.length}
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations List */}
      <div className="space-y-4">
        {filteredRecs.length === 0 ? (
          <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
            No recommendations match your filters.
          </div>
        ) : (
          filteredRecs.map((rec) => (
            <div
              key={rec.recommendation_id}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    {getStatusBadge(rec.approval_status)}
                    {getPersonaBadge(rec.persona_type)}
                    <span className="text-xs text-gray-500">
                      {rec.content_type}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {rec.title}
                  </h3>
                  <p className="text-sm text-gray-600 mb-2">{rec.description}</p>

                  {rec.rationale && (
                    <div className="bg-blue-50 border-l-4 border-blue-400 p-3 mt-3">
                      <p className="text-sm font-medium text-blue-900">Rationale:</p>
                      <p className="text-sm text-blue-800 mt-1">{rec.rationale}</p>
                    </div>
                  )}

                  {rec.operator_notes && (
                    <div className={`mt-3 p-3 rounded ${
                      rec.operator_notes.includes('AUTO-FLAGGED') || rec.operator_notes.includes('FLAGGED')
                        ? 'bg-red-50 border-l-4 border-red-400'
                        : 'bg-gray-50 border-l-4 border-gray-400'
                    }`}>
                      <p className="text-sm font-medium text-gray-900">Operator Notes:</p>
                      <p className="text-sm text-gray-700 mt-1">{rec.operator_notes}</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <div className="text-sm text-gray-500">
                  User: <span className="font-mono">{rec.user_id}</span> •
                  Created: {new Date(rec.created_at).toLocaleDateString()}
                </div>
                <div className="flex gap-2">
                  {rec.approval_status !== 'approved' && (
                    <button
                      onClick={() => handleApprove(rec.recommendation_id)}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    >
                      ✅ Approve
                    </button>
                  )}
                  {rec.approval_status !== 'review' && (
                    <button
                      onClick={() => handleFlag(rec.recommendation_id)}
                      className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
                    >
                      🚩 Flag
                    </button>
                  )}
                  <button
                    onClick={() => viewDetails(rec)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    👁️ Details
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Details Modal */}
      {selectedRec && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">Recommendation Details</h2>
              <button
                onClick={() => setSelectedRec(null)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ✕
              </button>
            </div>

            <div className="p-6">
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-2">{selectedRec.title}</h3>
                <div className="flex gap-2 mb-4">
                  {getStatusBadge(selectedRec.approval_status)}
                  {getPersonaBadge(selectedRec.persona_type)}
                </div>
                <p className="text-gray-700 mb-4">{selectedRec.description}</p>

                {selectedRec.rationale && (
                  <div className="bg-blue-50 p-4 rounded-lg mb-4">
                    <p className="font-semibold text-blue-900">Rationale:</p>
                    <p className="text-blue-800 mt-2">{selectedRec.rationale}</p>
                  </div>
                )}

                {selectedRec.disclaimer && (
                  <div className="bg-yellow-50 p-4 rounded-lg mb-4 border-l-4 border-yellow-400">
                    <p className="font-semibold text-yellow-900">Disclaimer:</p>
                    <p className="text-yellow-800 text-sm mt-2">{selectedRec.disclaimer}</p>
                  </div>
                )}
              </div>

              {/* Audit Log */}
              <div className="border-t border-gray-200 pt-6">
                <h4 className="font-semibold text-gray-900 mb-4">Activity History</h4>
                {auditLogs.length === 0 ? (
                  <p className="text-gray-500 text-sm">No audit logs found for this user.</p>
                ) : (
                  <div className="space-y-2 max-h-64 overflow-auto">
                    {auditLogs.slice(0, 10).map((log) => (
                      <div key={log.log_id} className="bg-gray-50 p-3 rounded text-sm">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-gray-900">{log.action}</span>
                          <span className="text-gray-500 text-xs">
                            {new Date(log.timestamp).toLocaleString()}
                          </span>
                        </div>
                        {log.details && (
                          <p className="text-gray-600 text-xs">{log.details}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
