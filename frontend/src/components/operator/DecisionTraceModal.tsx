'use client'

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { DecisionTrace } from '@/types';

interface DecisionTraceModalProps {
  recommendationId: number;
  onClose: () => void;
}

export default function DecisionTraceModal({ recommendationId, onClose }: DecisionTraceModalProps) {
  const [trace, setTrace] = useState<DecisionTrace | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTrace();
  }, [recommendationId]);

  const loadTrace = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDecisionTrace(recommendationId);
      setTrace(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load decision trace');
    } finally {
      setLoading(false);
    }
  };

  const getSignalIcon = (signalType: string) => {
    const icons: Record<string, string> = {
      credit_utilization: '💳',
      subscription_detection: '📱',
      savings_growth: '💰',
      income_stability: '💵',
      spending_surge: '📈',
      emergency_fund: '🏦',
    };
    return icons[signalType] || '📊';
  };

  const getPersonaIcon = (personaType: string) => {
    const icons: Record<string, string> = {
      savings_builder: '💰',
      credit_optimizer: '💳',
      subscription_heavy: '📱',
      variable_income: '📊',
      financial_newcomer: '🎯',
    };
    return icons[personaType] || '👤';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4 backdrop-blur-sm modal-backdrop">
      <div className="bg-[var(--bg-card)] rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto border border-[var(--border-color)] shadow-2xl modal-content">
        {/* Header */}
        <div className="p-6 border-b border-[var(--border-color)] flex items-center justify-between sticky top-0 bg-[var(--bg-card)] z-10">
          <div>
            <h2 className="text-2xl font-bold">Decision Trace</h2>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              Recommendation #{recommendationId} • Full Logic Chain
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-2xl transition-smooth"
          >
            &times;
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading && (
            <div className="text-center py-12">
              <div className="w-12 h-12 border-4 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-[var(--text-secondary)]">Loading decision trace...</p>
            </div>
          )}

          {error && (
            <div className="card-dark border border-red-500 p-4 text-red-700 transition-smooth">
              {error}
              <button onClick={loadTrace} className="mt-4 btn-accent transition-smooth">
                Retry
              </button>
            </div>
          )}

          {!loading && !error && trace && (
            <div className="space-y-6">
              {/* Step 1: Signals Detected */}
              <div className="card-dark p-6 transition-smooth">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-[var(--accent-primary)] text-white flex items-center justify-center font-bold">
                    1
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold">Behavioral Signals Detected</h3>
                    <p className="text-sm text-[var(--text-secondary)]">
                      {trace.signals_detected.length} signals identified for user {trace.user_id}
                    </p>
                  </div>
                </div>

                <div className="space-y-3 ml-13">
                  {trace.signals_detected.map((signal, idx) => (
                    <div
                      key={idx}
                      className="bg-[var(--bg-secondary)] p-4 rounded-lg border border-[var(--border-color)] transition-smooth"
                    >
                      <div className="flex items-start gap-3">
                        <div className="text-2xl">{getSignalIcon(signal.signal_type)}</div>
                        <div className="flex-1">
                          <h4 className="font-semibold capitalize">
                            {signal.signal_type.replace(/_/g, ' ')}
                          </h4>
                          <p className="text-sm text-[var(--text-secondary)] mt-1">
                            Value: {signal.value.toFixed(2)}
                          </p>
                          {signal.details && (
                            <div className="mt-2 text-xs">
                              <pre className="bg-[var(--bg-tertiary)] p-2 rounded overflow-x-auto">
                                {JSON.stringify(signal.details, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Arrow */}
              <div className="flex justify-center">
                <div className="text-4xl text-[var(--text-muted)]">↓</div>
              </div>

              {/* Step 2: Persona Assignment */}
              <div className="card-dark p-6 transition-smooth">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-[var(--accent-primary)] text-white flex items-center justify-center font-bold">
                    2
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold">Persona Assigned</h3>
                    <p className="text-sm text-[var(--text-secondary)]">
                      Based on detected behaviors and criteria
                    </p>
                  </div>
                </div>

                <div className="ml-13 bg-[var(--bg-secondary)] p-6 rounded-lg border border-[var(--accent-primary)] transition-smooth">
                  <div className="flex items-center gap-4">
                    <div className="text-5xl">{getPersonaIcon(trace.persona_assigned.persona_type)}</div>
                    <div className="flex-1">
                      <h4 className="text-xl font-bold capitalize mb-1">
                        {trace.persona_assigned.persona_type.replace(/_/g, ' ')}
                      </h4>
                      <p className="text-sm text-[var(--text-secondary)] mb-2">
                        Priority Rank: {trace.persona_assigned.priority_rank}
                      </p>
                      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 text-sm">
                        <p className="font-medium text-blue-700 mb-1">Criteria Met:</p>
                        <p className="text-blue-700">{trace.persona_assigned.criteria_met}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Arrow */}
              <div className="flex justify-center">
                <div className="text-4xl text-[var(--text-muted)]">↓</div>
              </div>

              {/* Step 3: Recommendation Generated */}
              <div className="card-dark p-6 transition-smooth">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-[var(--accent-primary)] text-white flex items-center justify-center font-bold">
                    3
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold">Recommendation Generated</h3>
                    <p className="text-sm text-[var(--text-secondary)]">
                      Final output with rationale and validation
                    </p>
                  </div>
                </div>

                <div className="ml-13 space-y-4">
                  {/* Title */}
                  <div className="bg-[var(--bg-secondary)] p-4 rounded-lg border border-[var(--border-color)]">
                    <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide mb-1">Title</p>
                    <p className="font-semibold">{trace.recommendation_logic.title}</p>
                  </div>

                  {/* Rationale */}
                  <div className="bg-[var(--bg-secondary)] p-4 rounded-lg border border-blue-500 transition-smooth">
                    <p className="text-xs text-blue-700 uppercase tracking-wide mb-1 font-semibold">
                      "Because..." Rationale
                    </p>
                    <p className="text-sm text-[var(--text-secondary)]">
                      {trace.recommendation_logic.rationale}
                    </p>
                  </div>

                  {/* Eligibility Checks */}
                  <div className="bg-[var(--bg-secondary)] p-4 rounded-lg border border-[var(--border-color)]">
                    <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide mb-2">
                      Eligibility Checks Passed
                    </p>
                    <div className="space-y-1">
                      {trace.recommendation_logic.eligibility_checks.map((check, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-sm">
                          <span className="text-slate-700">✓</span>
                          <span>{check}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Tone Validation */}
                  <div className="bg-[var(--bg-secondary)] p-4 rounded-lg border border-[var(--border-color)]">
                    <div className="flex items-center justify-between">
                      <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide">
                        Tone Validation
                      </p>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        trace.recommendation_logic.tone_validated
                          ? 'bg-slate-500/10 text-slate-700'
                          : 'bg-red-500/10 text-red-700'
                      }`}>
                        {trace.recommendation_logic.tone_validated ? '✓ PASSED' : '✗ FAILED'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Timestamp */}
              <div className="text-center text-sm text-[var(--text-muted)] pt-4 border-t border-[var(--border-color)]">
                Decision trace generated at {new Date(trace.timestamp).toLocaleString()}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-[var(--border-color)] bg-[var(--bg-secondary)]">
          <button onClick={onClose} className="btn-secondary w-full transition-smooth">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
