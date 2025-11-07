'use client'

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { UserProfile } from '@/types';

interface DashboardSummaryProps {
  userId: string;
  profile?: UserProfile | null;
}

export default function DashboardSummary({ userId, profile: profileProp }: DashboardSummaryProps) {
  const [profile, setProfile] = useState<UserProfile | null>(profileProp || null);
  const [loading, setLoading] = useState(!profileProp);
  const [error, setError] = useState<string | null>(null);

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
        setLoading(true);
        const data = await api.getUserProfile(userId);
        setProfile(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load profile');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [userId, profileProp]);

  if (loading) {
    return (
      <div className="card-dark p-8 transition-smooth">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-[var(--bg-tertiary)] rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="h-24 bg-[var(--bg-tertiary)] rounded"></div>
            <div className="h-24 bg-[var(--bg-tertiary)] rounded"></div>
            <div className="h-24 bg-[var(--bg-tertiary)] rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="card-dark p-8 transition-smooth border-l-4 border-red-500">
        <p className="text-red-400">
          {error || 'Unable to load your financial summary'}
        </p>
      </div>
    );
  }

  // Extract financial data from signals
  const creditUtilSignal = profile.signals?.find(s => s.signal_type === 'credit_utilization');
  const incomeSignal = profile.signals?.find(s => s.signal_type === 'income_stability');
  const spendingSignal = profile.signals?.find(s => s.signal_type === 'spending_surge');

  const creditBalance = creditUtilSignal?.details?.current_balance || 0;
  const avgIncome = incomeSignal?.details?.average_income || 0;
  const totalCash = avgIncome; // Using average income as approximation
  const totalBalance = totalCash - creditBalance;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <div className="card-dark p-8 transition-smooth">
      <h2 className="text-xl font-semibold mb-6">Financial Overview</h2>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        {/* Total Cash */}
        <div className="bg-[var(--bg-tertiary)] p-6 rounded-lg border border-[var(--border-color)] transition-smooth hover:border-[var(--accent-primary)]">
          <p className="text-sm text-[var(--text-secondary)] mb-2">Total Cash</p>
          <p className="text-2xl font-bold text-[var(--accent-primary)]">{formatCurrency(totalCash)}</p>
          <p className="text-xs text-[var(--text-secondary)] mt-2">
            Checking & Savings
          </p>
        </div>

        {/* Credit Balance */}
        <div className="bg-[var(--bg-tertiary)] p-6 rounded-lg border border-[var(--border-color)] transition-smooth hover:border-[var(--accent-primary)]">
          <p className="text-sm text-[var(--text-secondary)] mb-2">Credit Balance</p>
          <p className="text-2xl font-bold text-blue-700">{formatCurrency(creditBalance)}</p>
          <p className="text-xs text-[var(--text-secondary)] mt-2">
            Current Balance
          </p>
        </div>

        {/* Net Worth */}
        <div className="bg-[var(--bg-tertiary)] p-6 rounded-lg border border-[var(--border-color)] transition-smooth hover:border-[var(--accent-primary)]">
          <p className="text-sm text-[var(--text-secondary)] mb-2">Net Position</p>
          <p className={`text-2xl font-bold ${totalBalance >= 0 ? 'text-blue-700' : 'text-blue-900'}`}>
            {formatCurrency(totalBalance)}
          </p>
          <p className="text-xs text-[var(--text-secondary)] mt-2">
            Total Balance
          </p>
        </div>
      </div>

      {/* Financial Signals */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wide">
          Financial Insights
        </h3>

        {creditUtilSignal && (
          <div className="flex items-center justify-between p-4 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-color)] transition-smooth hover:border-[var(--accent-primary)]">
            <div>
              <p className="font-medium">Credit Utilization</p>
              <p className="text-xs text-[var(--text-secondary)]">
                {creditUtilSignal.details.status}
              </p>
            </div>
            <div className="text-right">
              <p className="font-semibold text-blue-700">
                {creditUtilSignal.details.utilization_percent.toFixed(1)}%
              </p>
              <p className="text-xs text-[var(--text-secondary)]">
                {formatCurrency(creditUtilSignal.details.current_balance)} / {formatCurrency(creditUtilSignal.details.credit_limit)}
              </p>
            </div>
          </div>
        )}

        {incomeSignal && (
          <div className="flex items-center justify-between p-4 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-color)] transition-smooth hover:border-[var(--accent-primary)]">
            <div>
              <p className="font-medium">Income Stability</p>
              <p className="text-xs text-[var(--text-secondary)]">
                {incomeSignal.details.status}
              </p>
            </div>
            <div className="text-right">
              <p className="font-semibold text-blue-700">
                {formatCurrency(incomeSignal.details.average_income)}
              </p>
              <p className="text-xs text-[var(--text-secondary)]">
                avg / {incomeSignal.details.median_pay_gap_days} days
              </p>
            </div>
          </div>
        )}

        {profile.signals && profile.signals.length === 0 && (
          <div className="text-center py-6 text-[var(--text-secondary)]">
            No financial data available yet
          </div>
        )}
      </div>

      {/* User Info */}
      <div className="mt-6 pt-6 border-t border-[var(--border-color)]">
        <div className="flex items-center justify-between text-sm">
          <div>
            <p className="text-[var(--text-secondary)]">Account Holder</p>
            <p className="font-medium">{profile.name}</p>
          </div>
          <div className="text-right">
            <p className="text-[var(--text-secondary)]">Income Level</p>
            <p className="font-medium capitalize">{profile.income_level || 'Not specified'}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
