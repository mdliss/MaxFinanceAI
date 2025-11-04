'use client'

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { UserProfile as UserProfileType } from '@/types';

interface UserProfileProps {
  userId: string;
}

export default function UserProfile({ userId }: UserProfileProps) {
  const [profile, setProfile] = useState<UserProfileType | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<'signals' | 'personas' | 'recommendations'>(
    'signals'
  );

  useEffect(() => {
    loadProfile();
  }, [userId]);

  const loadProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getUserProfile(userId);
      setProfile(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12 text-gray-500">Loading profile...</div>;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>
    );
  }

  if (!profile) {
    return <div className="text-center py-12 text-gray-500">No profile data found</div>;
  }

  return (
    <div className="space-y-6">
      {/* User Info */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">{profile.name}</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-xs text-gray-600 mb-1">User ID</div>
            <div className="font-medium text-gray-900">{profile.user_id}</div>
          </div>
          <div>
            <div className="text-xs text-gray-600 mb-1">Age</div>
            <div className="font-medium text-gray-900">{profile.age || 'N/A'}</div>
          </div>
          <div>
            <div className="text-xs text-gray-600 mb-1">Income Level</div>
            <div className="font-medium text-gray-900">{profile.income_level || 'N/A'}</div>
          </div>
          <div>
            <div className="text-xs text-gray-600 mb-1">Consent Status</div>
            <div
              className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                profile.consent_status
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {profile.consent_status ? 'Active' : 'Inactive'}
            </div>
          </div>
        </div>
      </div>

      {/* Section Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex -mb-px">
          {[
            { id: 'signals' as const, label: 'Signals', count: profile.signals.length },
            { id: 'personas' as const, label: 'Personas', count: profile.personas.length },
            {
              id: 'recommendations' as const,
              label: 'Recommendations',
              count: profile.recommendations.length,
            },
          ].map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`
                px-6 py-3 text-sm font-medium border-b-2 transition-colors
                ${
                  activeSection === section.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              {section.label} ({section.count})
            </button>
          ))}
        </nav>
      </div>

      {/* Signals Section */}
      {activeSection === 'signals' && (
        <div className="space-y-4">
          {profile.signals.length === 0 ? (
            <div className="text-center py-8 text-gray-500">No signals detected</div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                Detected Signals
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {profile.signals.map((signal) => (
                  <div
                    key={signal.signal_id}
                    className="bg-gray-50 border border-gray-200 rounded p-3"
                  >
                    <div className="text-xs font-medium text-gray-600 mb-1 uppercase">
                      {signal.signal_type.replace(/_/g, ' ')}
                    </div>
                    <div className="text-sm text-blue-600 font-bold mt-1">
                      {signal.value !== null
                        ? typeof signal.value === 'number'
                          ? signal.value.toFixed(2)
                          : signal.value
                        : 'N/A'}
                    </div>
                    {signal.details && (
                      <div className="text-xs text-gray-500 mt-2">
                        {Object.entries(signal.details).slice(0, 2).map(([key, val]) => (
                          <div key={key}>
                            {key}: {typeof val === 'number' ? val.toFixed(2) : String(val)}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Personas Section */}
      {activeSection === 'personas' && (
        <div className="space-y-4">
          {profile.personas.length === 0 ? (
            <div className="text-center py-8 text-gray-500">No personas assigned</div>
          ) : (
            profile.personas.map((persona) => (
              <div
                key={persona.persona_id}
                className="bg-white border border-gray-200 rounded-lg p-6"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{persona.persona_type}</h3>
                    <div className="text-sm text-gray-600 mt-1">
                      {persona.window_days}-day window
                    </div>
                  </div>
                  <div className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium">
                    Priority: {persona.priority_rank}
                  </div>
                </div>

                <div className="bg-purple-50 border border-purple-200 rounded p-3">
                  <div className="text-xs font-medium text-purple-900 mb-1">Criteria Met:</div>
                  <div className="text-sm text-purple-800">{persona.criteria_met}</div>
                </div>

                <div className="text-xs text-gray-500 mt-3">
                  Assigned: {new Date(persona.assigned_at).toLocaleString()}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Recommendations Section */}
      {activeSection === 'recommendations' && (
        <div className="space-y-4">
          {profile.recommendations.length === 0 ? (
            <div className="text-center py-8 text-gray-500">No recommendations</div>
          ) : (
            profile.recommendations.map((rec) => (
              <div
                key={rec.recommendation_id}
                className="bg-white border border-gray-200 rounded-lg p-6"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-lg font-semibold text-gray-900">{rec.title}</h3>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      rec.approval_status === 'approved'
                        ? 'bg-green-100 text-green-800'
                        : rec.approval_status === 'rejected'
                        ? 'bg-red-100 text-red-800'
                        : rec.approval_status === 'review'
                        ? 'bg-orange-100 text-orange-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}
                  >
                    {rec.approval_status}
                  </span>
                </div>

                {rec.description && <p className="text-gray-700 mb-3">{rec.description}</p>}

                <div className="bg-blue-50 border border-blue-200 rounded p-3 mb-3">
                  <div className="text-xs font-medium text-blue-900 mb-1">Rationale:</div>
                  <p className="text-sm text-blue-800">{rec.rationale}</p>
                </div>

                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span>Type: {rec.content_type}</span>
                  <span>Persona: {rec.persona_type}</span>
                  <span>
                    Eligible:{' '}
                    <span
                      className={rec.eligibility_met ? 'text-green-600' : 'text-red-600'}
                    >
                      {rec.eligibility_met ? 'Yes' : 'No'}
                    </span>
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
