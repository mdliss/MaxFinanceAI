'use client'

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Recommendation } from '@/types';

interface RecommendationsForUserProps {
  userId: string;
}

export default function RecommendationsForUser({ userId }: RecommendationsForUserProps) {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [submittingFeedback, setSubmittingFeedback] = useState<number | null>(null);

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        setLoading(true);
        // Get profile which includes recommendations
        const profile = await api.getUserProfile(userId);
        // Show only approved recommendations to users
        const approvedRecs = profile.recommendations.filter(rec => rec.approval_status === 'approved');
        setRecommendations(approvedRecs);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load recommendations');
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [userId]);

  const handleFeedback = async (recommendationId: number, rating: number, helpful: boolean) => {
    try {
      setSubmittingFeedback(recommendationId);
      await api.submitFeedback({
        user_id: userId,
        recommendation_id: recommendationId,
        rating,
        helpful,
        comments: '',
      });

      // Update local state
      setRecommendations(prev =>
        prev.map(rec =>
          rec.recommendation_id === recommendationId
            ? { ...rec, user_feedback: { rating, helpful } }
            : rec
        )
      );
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    } finally {
      setSubmittingFeedback(null);
    }
  };

  if (loading) {
    return (
      <div className="card-dark p-6 transition-smooth">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-[var(--bg-tertiary)] rounded w-1/2"></div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 bg-[var(--bg-tertiary)] rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card-dark p-6 transition-smooth border-l-4 border-red-500">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  const getPersonaBadgeColor = (persona: string) => {
    const colors: Record<string, string> = {
      'Budget Breaker': 'bg-red-500/20 text-red-400 border-red-500/30',
      'Savings Superstar': 'bg-green-500/20 text-green-400 border-green-500/30',
      'Impulse Buyer': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
      'Credit Climber': 'bg-purple-500/20 text-purple-400 border-purple-500/30',
      'Bill Juggler': 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    };
    return colors[persona] || 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  };

  return (
    <div className="card-dark p-6 transition-smooth">
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-2">Your Recommendations</h2>
        <p className="text-sm text-[var(--text-secondary)]">
          Personalized financial education based on your spending patterns
        </p>
      </div>

      {recommendations.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-[var(--bg-tertiary)] rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl">💡</span>
          </div>
          <p className="text-[var(--text-secondary)] mb-2">No recommendations yet</p>
          <p className="text-xs text-[var(--text-secondary)]">
            Keep using your accounts to receive personalized insights
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec) => (
            <div
              key={rec.recommendation_id}
              className="bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-color)] transition-smooth hover:border-[var(--accent-primary)]"
            >
              {/* Recommendation Header */}
              <div
                className="p-4 cursor-pointer"
                onClick={() => setExpandedId(expandedId === rec.recommendation_id ? null : rec.recommendation_id)}
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-lg flex-1">{rec.title}</h3>
                  <button className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-smooth">
                    {expandedId === rec.recommendation_id ? '▼' : '▶'}
                  </button>
                </div>

                {/* Persona Badge */}
                <div className="mb-3">
                  <span className={`text-xs px-2 py-1 rounded border ${getPersonaBadgeColor(rec.persona_type)}`}>
                    {rec.persona_type}
                  </span>
                </div>

                {/* Short Description */}
                <p className="text-sm text-[var(--text-secondary)]">
                  {rec.description}
                </p>
              </div>

              {/* Expanded Details */}
              {expandedId === rec.recommendation_id && (
                <div className="px-4 pb-4 border-t border-[var(--border-color)] pt-4 mt-4">
                  {/* Rationale */}
                  <div className="mb-4">
                    <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide mb-2">
                      Why this matters
                    </p>
                    <p className="text-sm text-[var(--text-secondary)]">
                      {rec.rationale}
                    </p>
                  </div>

                  {/* Feedback Section */}
                  <div className="bg-[var(--bg-tertiary)] p-4 rounded-lg">
                    <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide mb-3">
                      Was this helpful?
                    </p>

                    {rec.user_feedback ? (
                      <div className="text-sm text-green-400">
                        ✓ Thanks for your feedback!
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleFeedback(rec.recommendation_id, 5, true)}
                          disabled={submittingFeedback === rec.recommendation_id}
                          className="btn-accent text-sm px-4 py-2 transition-smooth"
                        >
                          👍 Yes
                        </button>
                        <button
                          onClick={() => handleFeedback(rec.recommendation_id, 2, false)}
                          disabled={submittingFeedback === rec.recommendation_id}
                          className="btn-secondary text-sm px-4 py-2 transition-smooth"
                        >
                          👎 No
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
