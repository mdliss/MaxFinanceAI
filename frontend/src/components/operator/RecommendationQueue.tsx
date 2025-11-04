'use client'

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { Recommendation } from '@/types';
import RecommendationCard from './RecommendationCard';

interface RecommendationQueueProps {
  userId: string | null;
}

export default function RecommendationQueue({ userId }: RecommendationQueueProps) {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('pending');

  useEffect(() => {
    loadRecommendations();
  }, [userId, statusFilter]);

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = userId
        ? await api.getRecommendations(userId, statusFilter === 'all' ? undefined : statusFilter)
        : await api.getAllRecommendations(statusFilter === 'all' ? undefined : statusFilter);

      setRecommendations(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (recommendationId: number, notes?: string) => {
    try {
      await api.approveRecommendation(recommendationId, notes);
      await loadRecommendations();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to approve recommendation');
    }
  };

  const handleOverride = async (
    recommendationId: number,
    updates: { title?: string; description?: string; rationale?: string },
    notes?: string
  ) => {
    try {
      await api.overrideRecommendation(recommendationId, updates, notes);
      await loadRecommendations();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to override recommendation');
    }
  };

  const handleFlag = async (
    recommendationId: number,
    reason: string,
    severity: 'low' | 'medium' | 'high'
  ) => {
    try {
      await api.flagRecommendation(recommendationId, reason, severity);
      await loadRecommendations();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to flag recommendation');
    }
  };

  const statusOptions = [
    { value: 'pending', label: 'Pending', color: 'yellow' },
    { value: 'approved', label: 'Approved', color: 'green' },
    { value: 'rejected', label: 'Rejected', color: 'red' },
    { value: 'review', label: 'Review', color: 'orange' },
    { value: 'all', label: 'All', color: 'gray' },
  ];

  return (
    <div>
      {/* Filter Controls */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            {userId ? 'User Recommendations' : 'All Recommendations'}
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            {recommendations.length} recommendation(s) found
          </p>
        </div>

        <div className="flex gap-2">
          {statusOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => setStatusFilter(option.value)}
              className={`
                px-4 py-2 rounded-lg text-sm font-medium transition-colors
                ${
                  statusFilter === option.value
                    ? 'bg-blue-100 text-blue-700 border-2 border-blue-300'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }
              `}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div className="text-center py-12 text-gray-500">
          Loading recommendations...
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {/* Recommendations List */}
      {!loading && !error && recommendations.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No recommendations found
        </div>
      )}

      {!loading && !error && recommendations.length > 0 && (
        <div className="space-y-4">
          {recommendations.map((rec) => (
            <RecommendationCard
              key={rec.recommendation_id}
              recommendation={rec}
              onApprove={handleApprove}
              onOverride={handleOverride}
              onFlag={handleFlag}
            />
          ))}
        </div>
      )}
    </div>
  );
}
