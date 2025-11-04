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
    return <div className="text-center py-12 text-gray-500">Loading guardrails...</div>;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>
    );
  }

  if (!summary) {
    return <div className="text-center py-12 text-gray-500">No guardrails data found</div>;
  }

  return (
    <div className="space-y-6">
      {/* Guardrails Stats */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">{summary.message}</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl font-bold text-blue-600">{summary.guardrails.user_eligibility_rules.minimum_age}</div>
            <div className="text-xs text-gray-600 mt-1">Minimum Age</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl font-bold text-purple-600">{summary.guardrails.tone_guardrails.prohibited_tone_patterns_count}</div>
            <div className="text-xs text-gray-600 mt-1">Tone Patterns</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl font-bold text-orange-600">{summary.guardrails.content_safety_rules.prohibited_patterns.length}</div>
            <div className="text-xs text-gray-600 mt-1">Prohibited Content</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl font-bold text-green-600">{summary.guardrails.rate_limits.max_per_day}</div>
            <div className="text-xs text-gray-600 mt-1">Max Per Day</div>
          </div>
        </div>
      </div>

      {/* Tone Validation Tool */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Tone Validation Tool</h3>
        <p className="text-sm text-gray-600 mb-4">
          Check if recommendation text meets tone guardrails (empowering, non-judgmental language)
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Text to Validate
            </label>
            <textarea
              value={toneText}
              onChange={(e) => setToneText(e.target.value)}
              placeholder="Enter recommendation text to check tone..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={6}
            />
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleToneCheck}
              disabled={checkingTone || !toneText.trim()}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {checkingTone ? 'Checking...' : 'Check Tone'}
            </button>
            <button
              onClick={() => {
                setToneText('');
                setToneResult(null);
              }}
              className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Clear
            </button>
          </div>

          {/* Tone Check Result */}
          {toneResult && (
            <div className="mt-6">
              <div
                className={`p-4 rounded-lg border-2 ${
                  toneResult.valid
                    ? 'bg-green-50 border-green-300'
                    : 'bg-red-50 border-red-300'
                }`}
              >
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">{toneResult.valid ? '✓' : '✗'}</span>
                  <span
                    className={`font-semibold ${
                      toneResult.valid ? 'text-green-800' : 'text-red-800'
                    }`}
                  >
                    {toneResult.valid ? 'Tone Check Passed' : 'Tone Violations Detected'}
                  </span>
                </div>

                {/* Violations */}
                {toneResult.violations.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="font-medium text-red-900">Violations:</h4>
                    {toneResult.violations.map((violation, idx) => (
                      <div key={idx} className="bg-white rounded p-3 border border-red-200">
                        <div className="flex items-start gap-2">
                          <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-medium">
                            {violation.category}
                          </span>
                          <div className="flex-1">
                            <div className="text-sm font-medium text-gray-900 mb-1">
                              Pattern: {violation.pattern}
                            </div>
                            {violation.matches.length > 0 && (
                              <div className="text-xs text-red-700">
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
                    <h4 className="font-medium text-blue-900 mb-2">Suggestions:</h4>
                    <ul className="space-y-1">
                      {toneResult.suggestions.map((suggestion, idx) => (
                        <li key={idx} className="text-sm text-blue-800 flex items-start gap-2">
                          <span className="text-blue-500">•</span>
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
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Prohibited Content Patterns ({summary.guardrails.content_safety_rules.prohibited_patterns.length})
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-60 overflow-y-auto">
          {summary.guardrails.content_safety_rules.prohibited_patterns.map((pattern, idx) => (
            <div key={idx} className="bg-red-50 border border-red-200 rounded px-3 py-2 text-sm">
              <span className="text-red-800">{pattern}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Tone Guardrails */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Prohibited Tone Examples
          </h3>
          <div className="space-y-2">
            {summary.guardrails.tone_guardrails.examples_prohibited.map((pattern, idx) => (
              <div key={idx} className="bg-red-50 border border-red-200 rounded px-3 py-2 text-sm">
                <span className="text-red-800">{pattern}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Encouraged Tone Examples
          </h3>
          <div className="space-y-2">
            {summary.guardrails.tone_guardrails.examples_encouraged.map((pattern, idx) => (
              <div key={idx} className="bg-green-50 border border-green-200 rounded px-3 py-2 text-sm">
                <span className="text-green-800">{pattern}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
