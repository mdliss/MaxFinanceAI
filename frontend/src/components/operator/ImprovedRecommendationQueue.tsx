'use client'

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { Recommendation } from '@/types';
import DecisionTraceModal from './DecisionTraceModal';

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
  const [showDecisionTrace, setShowDecisionTrace] = useState(false);
  const [selectedTraceId, setSelectedTraceId] = useState<number | null>(null);

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
    const badges: Record<string, { bg: string; text: string }> = {
      review: { bg: 'bg-red-500/10', text: 'text-red-700' },
      pending: { bg: 'bg-amber-500/10', text: 'text-amber-700' },
      approved: { bg: 'bg-slate-500/10', text: 'text-slate-700' },
      rejected: { bg: 'bg-gray-500/10', text: 'text-gray-600' },
    };
    const badge = badges[status] || badges.pending;
    return (
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${badge.bg} ${badge.text} transition-smooth`}>
        {status.toUpperCase()}
      </span>
    );
  };

  const getPersonaBadge = (persona: string) => {
    const colors: Record<string, string> = {
      financial_newcomer: 'bg-blue-500/10 text-blue-700',
      credit_optimizer: 'bg-purple-500/10 text-purple-700',
      savings_builder: 'bg-teal-500/10 text-teal-700',
      subscription_heavy: 'bg-rose-500/10 text-rose-700',
      variable_income: 'bg-indigo-500/10 text-indigo-700',
    };
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium transition-smooth ${colors[persona] || 'bg-gray-500/10 text-gray-600'}`}>
        {persona.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  const uniquePersonas = Array.from(new Set(recommendations.map(r => r.persona_type)));

  if (loading) {
    return <div className="text-center py-12 text-[var(--text-secondary)]">Loading recommendations...</div>;
  }

  if (error) {
    return (
      <div className="card-dark border border-red-500 p-4 transition-smooth">
        <p className="text-red-500">Error: {error}</p>
        <button
          onClick={loadRecommendations}
          className="mt-2 text-red-500 underline hover:text-red-400 transition-smooth"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Filters */}
      <div className="card-dark p-4 mb-6 transition-smooth">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
              Search
            </label>
            <input
              type="text"
              placeholder="Search by title, user..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg focus:ring-2 focus:ring-[var(--accent-primary)] focus:border-[var(--accent-primary)] text-[var(--text-primary)] transition-smooth placeholder:text-[var(--text-muted)]"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg focus:ring-2 focus:ring-[var(--accent-primary)] focus:border-[var(--accent-primary)] text-[var(--text-primary)] transition-smooth"
            >
              <option value="all">All Statuses</option>
              <option value="review">Flagged/Review</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
              Persona
            </label>
            <select
              value={personaFilter}
              onChange={(e) => setPersonaFilter(e.target.value)}
              className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg focus:ring-2 focus:ring-[var(--accent-primary)] focus:border-[var(--accent-primary)] text-[var(--text-primary)] transition-smooth"
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
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
              Results
            </label>
            <div className="px-3 py-2 bg-[var(--bg-secondary)] rounded-lg text-center font-semibold border border-[var(--border-color)]">
              {filteredRecs.length} of {recommendations.length}
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations List */}
      <div className="space-y-4">
        {filteredRecs.length === 0 ? (
          <div className="card-dark p-8 text-center text-[var(--text-secondary)] transition-smooth">
            No recommendations match your filters.
          </div>
        ) : (
          filteredRecs.map((rec) => (
            <div
              key={rec.recommendation_id}
              className="card-dark p-6 transition-smooth"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    {getStatusBadge(rec.approval_status)}
                    {getPersonaBadge(rec.persona_type)}
                    <span className="text-xs text-[var(--text-muted)]">
                      {rec.content_type}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold mb-2">
                    {rec.title}
                  </h3>
                  <p className="text-sm text-[var(--text-secondary)] mb-2">{rec.description}</p>

                  {rec.rationale && (
                    <div className="bg-[var(--bg-secondary)] border-l-4 border-blue-500 p-3 mt-3 rounded transition-smooth">
                      <p className="text-sm font-medium text-blue-400">Rationale:</p>
                      <p className="text-sm text-[var(--text-secondary)] mt-1">{rec.rationale}</p>
                    </div>
                  )}

                  {rec.operator_notes && (
                    <div className={`mt-3 p-3 rounded transition-smooth ${
                      rec.operator_notes.includes('AUTO-FLAGGED') || rec.operator_notes.includes('FLAGGED')
                        ? 'bg-[var(--bg-secondary)] border-l-4 border-red-500'
                        : 'bg-[var(--bg-secondary)] border-l-4 border-[var(--border-color)]'
                    }`}>
                      <p className="text-sm font-medium">Operator Notes:</p>
                      <p className="text-sm text-[var(--text-secondary)] mt-1">{rec.operator_notes}</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-[var(--border-color)]">
                <div className="text-sm text-[var(--text-muted)]">
                  User: <span className="font-mono text-[var(--text-secondary)]">{rec.user_id}</span> •
                  Created: {new Date(rec.created_at).toLocaleDateString()}
                </div>
                <div className="flex gap-2">
                  {rec.approval_status !== 'approved' && (
                    <button
                      onClick={() => handleApprove(rec.recommendation_id)}
                      className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-smooth"
                    >
                      Approve
                    </button>
                  )}
                  {rec.approval_status !== 'review' && (
                    <button
                      onClick={() => handleFlag(rec.recommendation_id)}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-smooth"
                    >
                      Flag
                    </button>
                  )}
                  <button
                    onClick={() => viewDetails(rec)}
                    className="btn-secondary transition-smooth"
                  >
                    Details
                  </button>
                  <button
                    onClick={() => {
                      setSelectedTraceId(rec.recommendation_id);
                      setShowDecisionTrace(true);
                    }}
                    className="btn-accent transition-smooth"
                  >
                    Decision Trace
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Details Modal */}
      {selectedRec && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4 backdrop-blur-sm modal-backdrop">
          <div className="bg-[var(--bg-card)] rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto border border-[var(--border-color)] shadow-2xl modal-content">
            <div className="p-6 border-b border-[var(--border-color)] flex items-center justify-between sticky top-0 bg-[var(--bg-card)] z-10">
              <h2 className="text-2xl font-bold">Recommendation Details</h2>
              <button
                onClick={() => setSelectedRec(null)}
                className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-2xl transition-smooth"
              >
                &times;
              </button>
            </div>

            <div className="p-6">
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-2">{selectedRec.title}</h3>
                <div className="flex gap-2 mb-4">
                  {getStatusBadge(selectedRec.approval_status)}
                  {getPersonaBadge(selectedRec.persona_type)}
                </div>
                <p className="text-[var(--text-secondary)] mb-4">{selectedRec.description}</p>

                {selectedRec.rationale && (
                  <div className="bg-[var(--bg-secondary)] p-4 rounded-lg mb-4 border-l-4 border-blue-500 transition-smooth">
                    <p className="font-semibold text-blue-400">Rationale:</p>
                    <p className="text-[var(--text-secondary)] mt-2">{selectedRec.rationale}</p>
                  </div>
                )}

                {selectedRec.disclaimer && (
                  <div className="bg-[var(--bg-secondary)] p-4 rounded-lg mb-4 border-l-4 border-yellow-500 transition-smooth">
                    <p className="font-semibold text-yellow-400">Disclaimer:</p>
                    <p className="text-[var(--text-secondary)] text-sm mt-2">{selectedRec.disclaimer}</p>
                  </div>
                )}
              </div>

              {/* Audit Log */}
              <div className="border-t border-[var(--border-color)] pt-6">
                <h4 className="font-semibold mb-4">Activity History</h4>
                {auditLogs.length === 0 ? (
                  <p className="text-[var(--text-muted)] text-sm">No audit logs found for this user.</p>
                ) : (
                  <div className="space-y-2 max-h-64 overflow-auto">
                    {auditLogs.slice(0, 10).map((log) => (
                      <div key={log.log_id} className="bg-[var(--bg-secondary)] p-3 rounded text-sm transition-smooth hover:bg-[var(--bg-tertiary)]">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium">{log.action}</span>
                          <span className="text-[var(--text-muted)] text-xs">
                            {new Date(log.timestamp).toLocaleString()}
                          </span>
                        </div>
                        {log.details && (
                          <p className="text-[var(--text-secondary)] text-xs">{log.details}</p>
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

      {/* Decision Trace Modal */}
      {showDecisionTrace && selectedTraceId && (
        <DecisionTraceModal
          recommendationId={selectedTraceId}
          onClose={() => {
            setShowDecisionTrace(false);
            setSelectedTraceId(null);
          }}
        />
      )}
    </div>
  );
}
