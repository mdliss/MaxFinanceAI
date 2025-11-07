'use client'

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { UserProfile } from '@/types';

interface BehavioralSignalsProps {
  userId: string;
  profile?: UserProfile | null;
}

export default function BehavioralSignals({ userId, profile: profileProp }: BehavioralSignalsProps) {
  const [profile, setProfile] = useState<UserProfile | null>(profileProp || null);
  const [loading, setLoading] = useState(!profileProp);

  useEffect(() => {
    // If profile is passed as prop, use it directly (avoid duplicate fetch)
    if (profileProp) {
      setProfile(profileProp);
      setLoading(false);
      return;
    }

    // Otherwise fetch it
    const fetchProfile = async () => {
      try {
        const data = await api.getUserProfile(userId);
        setProfile(data);
      } catch (err) {
        console.error('Failed to load profile:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [userId, profileProp]);

  if (loading) {
    return (
      <div className="card-dark p-6 transition-smooth">
        <div className="animate-pulse space-y-3">
          <div className="h-6 bg-[var(--bg-tertiary)] rounded w-1/3"></div>
          <div className="h-12 bg-[var(--bg-tertiary)] rounded"></div>
          <div className="h-12 bg-[var(--bg-tertiary)] rounded"></div>
        </div>
      </div>
    );
  }

  const getSignalLabel = (signalType: string) => {
    const labels: Record<string, string> = {
      credit_utilization: 'Credit',
      subscription_detection: 'Subscription',
      savings_growth: 'Savings',
      income_stability: 'Income',
      spending_surge: 'Spending',
      emergency_fund: 'Emergency Fund',
    };
    return labels[signalType] || 'Signal';
  };

  const getSignalColor = (signalType: string, value: number) => {
    if (signalType === 'credit_utilization') {
      if (value >= 80) return 'bg-red-500/10 border-red-500/20 text-red-700';
      if (value >= 50) return 'bg-amber-500/10 border-amber-500/20 text-amber-700';
      if (value >= 30) return 'bg-yellow-500/10 border-yellow-500/20 text-yellow-700';
      return 'bg-slate-500/10 border-slate-500/20 text-slate-700';
    }
    if (signalType === 'savings_growth' && value >= 2) {
      return 'bg-slate-500/10 border-slate-500/20 text-slate-700';
    }
    return 'bg-blue-500/10 border-blue-500/20 text-blue-700';
  };

  const formatSignalValue = (signal: any) => {
    if (signal.signal_type === 'credit_utilization') {
      return `${signal.details?.utilization_percent?.toFixed(1)}% utilization`;
    }
    if (signal.signal_type === 'subscription_detection') {
      return `${signal.details?.recurring_merchants?.length || 0} recurring subscriptions`;
    }
    if (signal.signal_type === 'savings_growth') {
      return `${signal.details?.growth_rate?.toFixed(1)}% growth rate`;
    }
    if (signal.signal_type === 'income_stability') {
      return `${signal.details?.median_pay_gap_days || 0} day pay gap`;
    }
    return signal.value?.toFixed(2) || 'N/A';
  };

  const getCurrentPersona = () => {
    if (!profile?.personas || profile.personas.length === 0) return null;
    // Get the most recent persona with highest priority
    return profile.personas.sort((a, b) => b.priority_rank - a.priority_rank)[0];
  };

  const persona = getCurrentPersona();

  return (
    <div className="card-dark p-6 transition-smooth">
      <h3 className="text-lg font-semibold mb-4">Your Financial Profile</h3>

      {/* Persona Badge */}
      {persona && (
        <div className="mb-6 p-4 bg-[var(--bg-secondary)] rounded-lg border border-[var(--accent-primary)] transition-smooth">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide mb-1">
                Your Persona
              </p>
              <h4 className="text-xl font-bold capitalize">
                {persona.persona_type.replace(/_/g, ' ')}
              </h4>
              <p className="text-xs text-[var(--text-secondary)] mt-1">
                Based on {persona.window_days}-day analysis
              </p>
            </div>
            <div className="text-sm font-bold text-[var(--accent-primary)] uppercase tracking-wide">
              {persona.persona_type === 'savings_builder' ? 'Savings' :
               persona.persona_type === 'credit_optimizer' ? 'Credit' :
               persona.persona_type === 'subscription_heavy' ? 'Subscriptions' :
               persona.persona_type === 'variable_income' ? 'Income' :
               'Financial'}
            </div>
          </div>
        </div>
      )}

      {/* Behavioral Signals */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wide">
          Detected Behaviors ({profile?.signals?.length || 0})
        </h4>

        {profile?.signals && profile.signals.length > 0 ? (
          profile.signals.map((signal) => (
            <div
              key={signal.signal_id}
              className={`p-4 rounded-lg border transition-smooth ${getSignalColor(
                signal.signal_type,
                signal.value
              )}`}
            >
              <div className="flex items-start gap-3">
                <div className="text-xs font-semibold px-2 py-1 bg-[var(--accent-primary)]/10 rounded">
                  {getSignalLabel(signal.signal_type)}
                </div>
                <div className="flex-1">
                  <div className="flex items-start justify-between">
                    <div>
                      <h5 className="font-semibold capitalize">
                        {signal.signal_type.replace(/_/g, ' ')}
                      </h5>
                      <p className="text-sm mt-1">{formatSignalValue(signal)}</p>
                    </div>
                    <span className="text-xs text-[var(--text-muted)]">
                      {new Date(signal.computed_at).toLocaleDateString()}
                    </span>
                  </div>

                  {/* Additional Details */}
                  {signal.details?.status && (
                    <p className="text-xs mt-2 opacity-75">{signal.details.status}</p>
                  )}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-[var(--text-secondary)]">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <p>No behavioral signals detected yet</p>
            <p className="text-xs mt-1">Connect your accounts to start tracking</p>
          </div>
        )}
      </div>
    </div>
  );
}
