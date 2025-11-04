'use client'

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { GuardrailSummary, ToneCheckResult } from '@/types';

export default function GuardrailsSummary() {
  const [summary, setSummary] = useState<GuardrailSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Tone checker state
  const [toneText, setToneText] = useState('');
  const [toneResult, setToneResult] = useState<ToneCheckResult | null>(null);
  const [checkingTone, setCheckingTone] = useState(false);

  useEffect(() => {
    loadSummary();
  }, []);

  const loadSummary = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getGuardrailSummary();
      setSummary(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load guardrails summary');
    } finally {
      setLoading(false);
    }
  };

  const handleToneCheck = async () => {
    if (!toneText.trim()) {
      alert('Please enter some text to check');
      return;
    }

    try {
      setCheckingTone(true);
      const result = await api.checkTone(toneText);
      setToneResult(result);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to check tone');
    } finally {
      setCheckingTone(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12 text-[var(--text-secondary)]">Loading guardrails...</div>;
  }

  if (error) {
    return (
      <div className="card-dark border border-red-500 p-4 text-red-400 transition-smooth">{error}</div>
    );
  }

  if (!summary) {
    return <div className="text-center py-12 text-[var(--text-secondary)]">No guardrails data found</div>;
  }

  return (
    <div className="space-y-6">
      {/* Guardrails Stats */}
      <div className="card-dark p-6 border-l-4 border-green-500 transition-smooth">
        <h2 className="text-lg font-semibold mb-4">{summary.message}</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border-color)] transition-smooth hover:border-blue-500">
            <div className="text-2xl font-bold text-blue-400">{summary.guardrails.user_eligibility_rules.minimum_age}</div>
            <div className="text-xs text-[var(--text-muted)] mt-1">Minimum Age</div>
          </div>
          <div className="bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border-color)] transition-smooth hover:border-purple-500">
            <div className="text-2xl font-bold text-purple-400">{summary.guardrails.tone_guardrails.prohibited_tone_patterns_count}</div>
            <div className="text-xs text-[var(--text-muted)] mt-1">Tone Patterns</div>
          </div>
          <div className="bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border-color)] transition-smooth hover:border-orange-500">
            <div className="text-2xl font-bold text-orange-400">{summary.guardrails.content_safety_rules.prohibited_patterns.length}</div>
            <div className="text-xs text-[var(--text-muted)] mt-1">Prohibited Content</div>
          </div>
          <div className="bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border-color)] transition-smooth hover:border-green-500">
            <div className="text-2xl font-bold text-green-400">{summary.guardrails.rate_limits.max_per_day}</div>
            <div className="text-xs text-[var(--text-muted)] mt-1">Max Per Day</div>
          </div>
        </div>
      </div>

      {/* Tone Validation Tool */}
      <div className="card-dark p-6 transition-smooth">
        <h3 className="text-lg font-semibold mb-4">Tone Validation Tool</h3>
        <p className="text-sm text-[var(--text-secondary)] mb-4">
          Check if recommendation text meets tone guardrails (empowering, non-judgmental language)
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
              Text to Validate
            </label>
            <textarea
              value={toneText}
              onChange={(e) => setToneText(e.target.value)}
              placeholder="Enter recommendation text to check tone..."
              className="w-full px-4 py-3 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg resize-none focus:ring-2 focus:ring-[var(--accent-primary)] focus:border-[var(--accent-primary)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] transition-smooth"
              rows={6}
            />
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleToneCheck}
              disabled={checkingTone || !toneText.trim()}
              className="btn-accent disabled:opacity-50 disabled:cursor-not-allowed transition-smooth"
            >
              {checkingTone ? 'Checking...' : 'Check Tone'}
            </button>
            <button
              onClick={() => {
                setToneText('');
                setToneResult(null);
              }}
              className="btn-secondary transition-smooth"
            >
              Clear
            </button>
          </div>

          {/* Tone Check Result */}
          {toneResult && (
            <div className="mt-6 transition-smooth">
              <div
                className={`p-4 rounded-lg border-2 transition-smooth ${
                  toneResult.valid
                    ? 'bg-green-900/20 border-green-500'
                    : 'bg-red-900/20 border-red-500'
                }`}
              >
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">{toneResult.valid ? '✓' : '✗'}</span>
                  <span
                    className={`font-semibold ${
                      toneResult.valid ? 'text-green-400' : 'text-red-400'
                    }`}
                  >
                    {toneResult.valid ? 'Tone Check Passed' : 'Tone Violations Detected'}
                  </span>
                </div>

                {/* Violations */}
                {toneResult.violations.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="font-medium text-red-400">Violations:</h4>
                    {toneResult.violations.map((violation, idx) => (
                      <div key={idx} className="bg-[var(--bg-secondary)] rounded p-3 border border-red-500 transition-smooth hover:border-red-400">
                        <div className="flex items-start gap-2">
                          <span className="px-2 py-1 bg-red-900/30 text-red-400 rounded text-xs font-medium transition-smooth">
                            {violation.category}
                          </span>
                          <div className="flex-1">
                            <div className="text-sm font-medium mb-1">
                              Pattern: {violation.pattern}
                            </div>
                            {violation.matches.length > 0 && (
                              <div className="text-xs text-red-400">
                                Matches: {violation.matches.join(', ')}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Suggestions */}
                {toneResult.suggestions.length > 0 && (
                  <div className="mt-4">
                    <h4 className="font-medium text-[var(--accent-primary)] mb-2">Suggestions:</h4>
                    <ul className="space-y-1">
                      {toneResult.suggestions.map((suggestion, idx) => (
                        <li key={idx} className="text-sm text-[var(--text-secondary)] flex items-start gap-2">
                          <span className="text-[var(--accent-primary)]">•</span>
                          <span>{suggestion}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Content Safety Rules */}
      <div className="card-dark p-6 transition-smooth">
        <h3 className="text-lg font-semibold mb-4">
          Prohibited Content Patterns ({summary.guardrails.content_safety_rules.prohibited_patterns.length})
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-60 overflow-y-auto">
          {summary.guardrails.content_safety_rules.prohibited_patterns.map((pattern, idx) => (
            <div key={idx} className="bg-red-900/20 border border-red-500 rounded px-3 py-2 text-sm transition-smooth hover:bg-red-900/30 hover:border-red-400">
              <span className="text-red-400">{pattern}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Tone Guardrails */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card-dark p-6 transition-smooth">
          <h3 className="text-lg font-semibold mb-4">
            Prohibited Tone Examples
          </h3>
          <div className="space-y-2">
            {summary.guardrails.tone_guardrails.examples_prohibited.map((pattern, idx) => (
              <div key={idx} className="bg-red-900/20 border border-red-500 rounded px-3 py-2 text-sm transition-smooth hover:bg-red-900/30 hover:border-red-400">
                <span className="text-red-400">{pattern}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card-dark p-6 transition-smooth">
          <h3 className="text-lg font-semibold mb-4">
            Encouraged Tone Examples
          </h3>
          <div className="space-y-2">
            {summary.guardrails.tone_guardrails.examples_encouraged.map((pattern, idx) => (
              <div key={idx} className="bg-green-900/20 border border-green-500 rounded px-3 py-2 text-sm transition-smooth hover:bg-green-900/30 hover:border-green-400">
                <span className="text-green-400">{pattern}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
