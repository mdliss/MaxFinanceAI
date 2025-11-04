'use client'

import { useState } from 'react';
import type { Recommendation } from '@/types';

interface RecommendationCardProps {
  recommendation: Recommendation;
  onApprove: (id: number, notes?: string) => Promise<void>;
  onOverride: (
    id: number,
    updates: { title?: string; description?: string; rationale?: string },
    notes?: string
  ) => Promise<void>;
  onFlag: (id: number, reason: string, severity: 'low' | 'medium' | 'high') => Promise<void>;
}

export default function RecommendationCard({
  recommendation,
  onApprove,
  onOverride,
  onFlag,
}: RecommendationCardProps) {
  const [showActions, setShowActions] = useState(false);
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [showFlagModal, setShowFlagModal] = useState(false);
  const [notes, setNotes] = useState('');

  // Override state
  const [overrideTitle, setOverrideTitle] = useState(recommendation.title);
  const [overrideDescription, setOverrideDescription] = useState(recommendation.description || '');
  const [overrideRationale, setOverrideRationale] = useState(recommendation.rationale);
  const [overrideNotes, setOverrideNotes] = useState('');

  // Flag state
  const [flagReason, setFlagReason] = useState('');
  const [flagSeverity, setFlagSeverity] = useState<'low' | 'medium' | 'high'>('medium');

  const getStatusBadge = () => {
    const statusConfig = {
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Pending' },
      approved: { bg: 'bg-green-100', text: 'text-green-800', label: 'Approved' },
      rejected: { bg: 'bg-red-100', text: 'text-red-800', label: 'Rejected' },
      review: { bg: 'bg-orange-100', text: 'text-orange-800', label: 'Review' },
    };

    const config = statusConfig[recommendation.approval_status] || statusConfig.pending;
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    );
  };

  const handleApprove = async () => {
    await onApprove(recommendation.recommendation_id, notes);
    setNotes('');
    setShowActions(false);
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
      <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h3 className="text-lg font-semibold text-gray-900">{recommendation.title}</h3>
              {getStatusBadge()}
            </div>
            <div className="flex gap-4 text-xs text-gray-500">
              <span>ID: {recommendation.recommendation_id}</span>
              <span>User: {recommendation.user_id}</span>
              <span>Persona: {recommendation.persona_type}</span>
              <span>Type: {recommendation.content_type}</span>
            </div>
          </div>
          <button
            onClick={() => setShowActions(!showActions)}
            className="text-gray-400 hover:text-gray-600 p-2"
          >
            ⋮
          </button>
        </div>

        {/* Description */}
        {recommendation.description && (
          <p className="text-gray-700 mb-3">{recommendation.description}</p>
        )}

        {/* Rationale */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
          <div className="text-xs font-medium text-blue-900 mb-1">Rationale:</div>
          <p className="text-sm text-blue-800">{recommendation.rationale}</p>
        </div>

        {/* Eligibility */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-medium text-gray-600">Eligibility:</span>
          <span
            className={`px-2 py-1 rounded text-xs font-medium ${
              recommendation.eligibility_met
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}
          >
            {recommendation.eligibility_met ? 'Met' : 'Not Met'}
          </span>
        </div>

        {/* Operator Notes */}
        {recommendation.operator_notes && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-3">
            <div className="text-xs font-medium text-gray-700 mb-1">Operator Notes:</div>
            <p className="text-sm text-gray-600">{recommendation.operator_notes}</p>
          </div>
        )}

        {/* Action Buttons */}
        {showActions && recommendation.approval_status === 'pending' && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex gap-2">
              <button
                onClick={handleApprove}
                className="flex-1 bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-colors"
              >
                ✓ Approve
              </button>
              <button
                onClick={() => setShowOverrideModal(true)}
                className="flex-1 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
              >
                ✎ Override
              </button>
              <button
                onClick={() => setShowFlagModal(true)}
                className="flex-1 bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition-colors"
              >
                ⚑ Flag
              </button>
            </div>

            {/* Notes Input */}
            <div className="mt-3">
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add operator notes (optional)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
                rows={2}
              />
            </div>
          </div>
        )}
      </div>

      {/* Override Modal */}
      {showOverrideModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">Override Recommendation</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                  <input
                    type="text"
                    value={overrideTitle}
                    onChange={(e) => setOverrideTitle(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={overrideDescription}
                    onChange={(e) => setOverrideDescription(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none"
                    rows={3}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Rationale</label>
                  <textarea
                    value={overrideRationale}
                    onChange={(e) => setOverrideRationale(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none"
                    rows={3}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Override Notes
                  </label>
                  <textarea
                    value={overrideNotes}
                    onChange={(e) => setOverrideNotes(e.target.value)}
                    placeholder="Explain why you're overriding..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none"
                    rows={2}
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={handleOverride}
                  className="flex-1 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
                >
                  Save Override
                </button>
                <button
                  onClick={() => setShowOverrideModal(false)}
                  className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-lg w-full">
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">Flag Recommendation</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
                  <select
                    value={flagSeverity}
                    onChange={(e) => setFlagSeverity(e.target.value as 'low' | 'medium' | 'high')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Reason</label>
                  <textarea
                    value={flagReason}
                    onChange={(e) => setFlagReason(e.target.value)}
                    placeholder="Describe the issue..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none"
                    rows={4}
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={handleFlag}
                  className="flex-1 bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600"
                >
                  Flag for Review
                </button>
                <button
                  onClick={() => setShowFlagModal(false)}
                  className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
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
