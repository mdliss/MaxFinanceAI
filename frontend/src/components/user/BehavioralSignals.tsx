'use client'

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { UserProfile } from '@/types';

interface BehavioralSignalsProps {
  userId: string;
}

export default function BehavioralSignals({ userId }: BehavioralSignalsProps) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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
  }, [userId]);

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
            <div className="text-5xl">
              {persona.persona_type === 'savings_builder' ? '💰' :
               persona.persona_type === 'credit_optimizer' ? '💳' :
               persona.persona_type === 'subscription_heavy' ? '📱' :
               persona.persona_type === 'variable_income' ? '📊' :
               '🎯'}
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
                <div className="text-2xl">{getSignalIcon(signal.signal_type)}</div>
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
            <p className="text-4xl mb-2">📊</p>
            <p>No behavioral signals detected yet</p>
            <p className="text-xs mt-1">Connect your accounts to start tracking</p>
          </div>
        )}
      </div>
    </div>
  );
}
