'use client'

import { useState } from 'react';
import type { Recommendation } from '@/types';

interface RecommendationCardProps {
  recommendation: Recommendation;
  onOverride: (
    id: number,
    updates: { title?: string; description?: string; rationale?: string },
    notes?: string
  ) => Promise<void>;
  onFlag: (id: number, reason: string, severity: 'low' | 'medium' | 'high') => Promise<void>;
}

export default function RecommendationCard({
  recommendation,
  onOverride,
  onFlag,
}: RecommendationCardProps) {
  const [showActions, setShowActions] = useState(false);
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [showFlagModal, setShowFlagModal] = useState(false);

  // Override state
  const [overrideTitle, setOverrideTitle] = useState(recommendation.title);
  const [overrideDescription, setOverrideDescription] = useState(recommendation.description || '');
  const [overrideRationale, setOverrideRationale] = useState(recommendation.rationale);
  const [overrideNotes, setOverrideNotes] = useState('');

  // Flag state
  const [flagReason, setFlagReason] = useState('');
  const [flagSeverity, setFlagSeverity] = useState<'low' | 'medium' | 'high'>('medium');

  const getStatusBadge = () => {
    const isFlagged = recommendation.approval_status === 'flagged';
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium transition-smooth ${
        isFlagged ? 'bg-orange-900/30 text-orange-400' : 'bg-green-900/30 text-green-400'
      }`}>
        {isFlagged ? 'Flagged' : 'Active'}
      </span>
    );
  };

  const handleOverride = async () => {
    const updates: { title?: string; description?: string; rationale?: string } = {};
    if (overrideTitle !== recommendation.title) updates.title = overrideTitle;
    if (overrideDescription !== recommendation.description) updates.description = overrideDescription;
    if (overrideRationale !== recommendation.rationale) updates.rationale = overrideRationale;

    await onOverride(recommendation.recommendation_id, updates, overrideNotes);
    setShowOverrideModal(false);
    setShowActions(false);
  };

  const handleFlag = async () => {
    if (!flagReason.trim()) {
      alert('Please provide a reason for flagging this recommendation');
      return;
    }
    await onFlag(recommendation.recommendation_id, flagReason, flagSeverity);
    setShowFlagModal(false);
    setShowActions(false);
  };

  return (
    <>
      <div className="card-dark p-6 transition-smooth">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h3 className="text-lg font-semibold">{recommendation.title}</h3>
              {getStatusBadge()}
            </div>
            <div className="flex gap-4 text-xs text-[var(--text-muted)]">
              <span>ID: {recommendation.recommendation_id}</span>
              <span>User: {recommendation.user_id}</span>
              <span>Persona: {recommendation.persona_type}</span>
              <span>Type: {recommendation.content_type}</span>
            </div>
          </div>
          <button
            onClick={() => setShowActions(!showActions)}
            className="text-[var(--text-muted)] hover:text-[var(--text-primary)] p-2 transition-smooth"
          >
            &vellip;
          </button>
        </div>

        {/* Description */}
        {recommendation.description && (
          <p className="text-[var(--text-secondary)] mb-3">{recommendation.description}</p>
        )}

        {/* Rationale */}
        <div className="bg-[var(--bg-secondary)] border border-blue-500 rounded-lg p-3 mb-3 transition-smooth">
          <div className="text-xs font-medium text-blue-400 mb-1">Rationale:</div>
          <p className="text-sm text-[var(--text-secondary)]">{recommendation.rationale}</p>
        </div>

        {/* Eligibility */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-medium text-[var(--text-secondary)]">Eligibility:</span>
          <span
            className={`px-2 py-1 rounded text-xs font-medium transition-smooth ${
              recommendation.eligibility_met
                ? 'bg-green-900/30 text-green-400'
                : 'bg-red-900/30 text-red-400'
            }`}
          >
            {recommendation.eligibility_met ? 'Met' : 'Not Met'}
          </span>
        </div>

        {/* Operator Notes */}
        {recommendation.operator_notes && (
          <div className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg p-3 mb-3 transition-smooth">
            <div className="text-xs font-medium text-[var(--text-secondary)] mb-1">Operator Notes:</div>
            <p className="text-sm text-[var(--text-secondary)]">{recommendation.operator_notes}</p>
          </div>
        )}

        {/* Action Buttons */}
        {showActions && (
          <div className="mt-4 pt-4 border-t border-[var(--border-color)]">
            <div className="flex gap-2">
              <button
                onClick={() => setShowOverrideModal(true)}
                className="flex-1 btn-accent transition-smooth"
              >
                Override
              </button>
              <button
                onClick={() => setShowFlagModal(true)}
                className="flex-1 bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-smooth"
              >
                Flag
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Override Modal */}
      {showOverrideModal && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4 backdrop-blur-sm modal-backdrop">
          <div className="bg-[var(--bg-card)] rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-[var(--border-color)] shadow-2xl modal-content">
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">Override Recommendation</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Title</label>
                  <input
                    type="text"
                    value={overrideTitle}
                    onChange={(e) => setOverrideTitle(e.target.value)}
                    className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg focus:ring-2 focus:ring-[var(--accent-primary)] transition-smooth text-[var(--text-primary)]"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
                    Description
                  </label>
                  <textarea
                    value={overrideDescription}
                    onChange={(e) => setOverrideDescription(e.target.value)}
                    className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg resize-none focus:ring-2 focus:ring-[var(--accent-primary)] transition-smooth text-[var(--text-primary)]"
                    rows={3}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Rationale</label>
                  <textarea
                    value={overrideRationale}
                    onChange={(e) => setOverrideRationale(e.target.value)}
                    className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg resize-none focus:ring-2 focus:ring-[var(--accent-primary)] transition-smooth text-[var(--text-primary)]"
                    rows={3}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
                    Override Notes
                  </label>
                  <textarea
                    value={overrideNotes}
                    onChange={(e) => setOverrideNotes(e.target.value)}
                    placeholder="Explain why you're overriding..."
                    className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg resize-none focus:ring-2 focus:ring-[var(--accent-primary)] transition-smooth text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
                    rows={2}
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={handleOverride}
                  className="flex-1 btn-accent transition-smooth"
                >
                  Save Override
                </button>
                <button
                  onClick={() => setShowOverrideModal(false)}
                  className="flex-1 btn-secondary transition-smooth"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Flag Modal */}
      {showFlagModal && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4 backdrop-blur-sm modal-backdrop">
          <div className="bg-[var(--bg-card)] rounded-lg max-w-lg w-full border border-[var(--border-color)] shadow-2xl modal-content">
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">Flag Recommendation</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Severity</label>
                  <select
                    value={flagSeverity}
                    onChange={(e) => setFlagSeverity(e.target.value as 'low' | 'medium' | 'high')}
                    className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg focus:ring-2 focus:ring-[var(--accent-primary)] transition-smooth text-[var(--text-primary)]"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Reason</label>
                  <textarea
                    value={flagReason}
                    onChange={(e) => setFlagReason(e.target.value)}
                    placeholder="Describe the issue..."
                    className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg resize-none focus:ring-2 focus:ring-[var(--accent-primary)] transition-smooth text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
                    rows={4}
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={handleFlag}
                  className="flex-1 bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-smooth"
                >
                  Flag for Review
                </button>
                <button
                  onClick={() => setShowFlagModal(false)}
                  className="flex-1 btn-secondary transition-smooth"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
