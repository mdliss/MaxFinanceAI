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
    return <div className="text-center py-12 text-[var(--text-secondary)]">Loading profile...</div>;
  }

  if (error) {
    return (
      <div className="card-dark border border-red-500 p-4 text-red-400 transition-smooth">{error}</div>
    );
  }

  if (!profile) {
    return <div className="text-center py-12 text-[var(--text-secondary)]">No profile data found</div>;
  }

  return (
    <div className="space-y-6">
      {/* User Info */}
      <div className="card-dark p-6 border-l-4 border-[var(--accent-primary)] transition-smooth">
        <h2 className="text-2xl font-bold mb-4">{profile.name}</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-xs text-[var(--text-muted)] mb-1">User ID</div>
            <div className="font-medium">{profile.user_id}</div>
          </div>
          <div>
            <div className="text-xs text-[var(--text-muted)] mb-1">Age</div>
            <div className="font-medium">{profile.age || 'N/A'}</div>
          </div>
          <div>
            <div className="text-xs text-[var(--text-muted)] mb-1">Income Level</div>
            <div className="font-medium">{profile.income_level || 'N/A'}</div>
          </div>
          <div>
            <div className="text-xs text-[var(--text-muted)] mb-1">Consent Status</div>
            <div
              className={`inline-block px-3 py-1 rounded-full text-xs font-medium transition-smooth ${
                profile.consent_status
                  ? 'bg-green-900/30 text-green-400'
                  : 'bg-red-900/30 text-red-400'
              }`}
            >
              {profile.consent_status ? 'Active' : 'Inactive'}
            </div>
          </div>
        </div>
      </div>

      {/* Section Tabs */}
      <div className="border-b border-[var(--border-color)]">
        <nav className="flex -mb-px gap-2">
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
                px-6 py-3 text-sm font-medium rounded-t-lg transition-smooth
                ${
                  activeSection === section.id
                    ? 'bg-[var(--accent-primary)] text-[var(--bg-primary)]'
                    : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]'
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
            <div className="text-center py-8 text-[var(--text-secondary)]">No signals detected</div>
          ) : (
            <div className="card-dark p-4 transition-smooth">
              <h3 className="text-lg font-semibold mb-3">
                Detected Signals
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {profile.signals.map((signal) => (
                  <div
                    key={signal.signal_id}
                    className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded p-3 transition-smooth hover:border-[var(--accent-primary)]"
                  >
                    <div className="text-xs font-medium text-[var(--text-muted)] mb-1 uppercase">
                      {signal.signal_type.replace(/_/g, ' ')}
                    </div>
                    <div className="text-sm text-[var(--accent-primary)] font-bold mt-1">
                      {signal.value !== null
                        ? typeof signal.value === 'number'
                          ? signal.value.toFixed(2)
                          : signal.value
                        : 'N/A'}
                    </div>
                    {signal.details && (
                      <div className="text-xs text-[var(--text-secondary)] mt-2">
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
            <div className="text-center py-8 text-[var(--text-secondary)]">No personas assigned</div>
          ) : (
            profile.personas.map((persona) => (
              <div
                key={persona.persona_id}
                className="card-dark p-6 transition-smooth"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold">{persona.persona_type}</h3>
                    <div className="text-sm text-[var(--text-secondary)] mt-1">
                      {persona.window_days}-day window
                    </div>
                  </div>
                  <div className="px-3 py-1 bg-purple-900/30 text-purple-400 rounded-full text-xs font-medium transition-smooth">
                    Priority: {persona.priority_rank}
                  </div>
                </div>

                <div className="bg-[var(--bg-secondary)] border border-purple-500 rounded p-3 transition-smooth">
                  <div className="text-xs font-medium text-purple-400 mb-1">Criteria Met:</div>
                  <div className="text-sm text-[var(--text-secondary)]">{persona.criteria_met}</div>
                </div>

                <div className="text-xs text-[var(--text-muted)] mt-3">
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
            <div className="text-center py-8 text-[var(--text-secondary)]">No recommendations</div>
          ) : (
            profile.recommendations.map((rec) => (
              <div
                key={rec.recommendation_id}
                className="card-dark p-6 transition-smooth"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-lg font-semibold">{rec.title}</h3>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-smooth ${
                      rec.approval_status === 'approved'
                        ? 'bg-green-900/30 text-green-400'
                        : rec.approval_status === 'rejected'
                        ? 'bg-red-900/30 text-red-400'
                        : rec.approval_status === 'review'
                        ? 'bg-orange-900/30 text-orange-400'
                        : 'bg-yellow-900/30 text-yellow-400'
                    }`}
                  >
                    {rec.approval_status}
                  </span>
                </div>

                {rec.description && <p className="text-[var(--text-secondary)] mb-3">{rec.description}</p>}

                <div className="bg-[var(--bg-secondary)] border border-blue-500 rounded p-3 mb-3 transition-smooth">
                  <div className="text-xs font-medium text-blue-400 mb-1">Rationale:</div>
                  <p className="text-sm text-[var(--text-secondary)]">{rec.rationale}</p>
                </div>

                <div className="flex items-center gap-4 text-xs text-[var(--text-muted)]">
                  <span>Type: {rec.content_type}</span>
                  <span>Persona: {rec.persona_type}</span>
                  <span>
                    Eligible:{' '}
                    <span
                      className={rec.eligibility_met ? 'text-green-400' : 'text-red-400'}
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
