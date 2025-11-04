'use client'

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { UserProfile } from '@/types';

interface TransactionsListProps {
  userId: string;
}

export default function TransactionsList({ userId }: TransactionsListProps) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        setLoading(true);
        const data = await api.getUserProfile(userId);
        setProfile(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load transactions');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [userId]);

  if (loading) {
    return (
      <div className="card-dark p-6 transition-smooth">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-[var(--bg-tertiary)] rounded w-1/2"></div>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-16 bg-[var(--bg-tertiary)] rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="card-dark p-6 transition-smooth border-l-4 border-red-500">
        <p className="text-red-400">
          {error || 'Unable to load transactions'}
        </p>
      </div>
    );
  }

  // Extract subscription signals which contain merchant/spending data
  const subscriptionSignals = profile.signals?.filter(s => s.signal_type === 'subscription_detected') || [];
  const spendingSurges = profile.signals?.filter(s => s.signal_type === 'spending_surge') || [];

  // Create transaction-like items from signals
  const transactions = [
    ...subscriptionSignals.map(s => ({
      transaction_id: s.signal_id,
      merchant: s.details.merchant,
      amount: -(s.details.average_amount || 0),
      category: 'subscription',
      date: s.computed_at,
    })),
    ...spendingSurges.map(s => ({
      transaction_id: s.signal_id,
      merchant: s.details.category || 'Various',
      amount: -(s.details.total_spent || s.value),
      category: s.details.category?.toLowerCase() || 'other',
      date: s.computed_at,
    }))
  ];

  // Filter transactions by category
  const filteredTransactions = filter === 'all'
    ? transactions
    : transactions.filter(t => t.category === filter);

  // Get unique categories
  const categories = Array.from(new Set(transactions.map(t => t.category)));

  // Sort transactions by date (most recent first)
  const sortedTransactions = [...filteredTransactions].sort((a, b) => {
    return new Date(b.date).getTime() - new Date(a.date).getTime();
  });

  // Show only last 10 transactions
  const recentTransactions = sortedTransactions.slice(0, 10);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(Math.abs(amount));
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      groceries: 'text-green-400',
      dining: 'text-orange-400',
      shopping: 'text-purple-400',
      entertainment: 'text-pink-400',
      transportation: 'text-blue-400',
      utilities: 'text-yellow-400',
      healthcare: 'text-red-400',
      other: 'text-gray-400',
    };
    return colors[category.toLowerCase()] || 'text-gray-400';
  };

  return (
    <div className="card-dark p-6 transition-smooth">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Recent Transactions</h2>
        <div className="flex items-center gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded px-3 py-1 text-sm transition-smooth hover:border-[var(--accent-primary)] focus:border-[var(--accent-primary)] focus:outline-none"
          >
            <option value="all">All Categories</option>
            {categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </div>
      </div>

      {recentTransactions.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-[var(--text-secondary)]">No transactions found</p>
        </div>
      ) : (
        <div className="space-y-2">
          {recentTransactions.map((transaction) => (
            <div
              key={transaction.transaction_id}
              className="flex items-center justify-between p-4 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-color)] transition-smooth hover:border-[var(--accent-primary)]"
            >
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${getCategoryColor(transaction.category)}`}></div>
                  <div>
                    <p className="font-medium">{transaction.merchant}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-xs px-2 py-0.5 rounded ${getCategoryColor(transaction.category)} bg-opacity-10`}>
                        {transaction.category}
                      </span>
                      <span className="text-xs text-[var(--text-secondary)]">
                        {formatDate(transaction.date)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <p className={`font-semibold ${
                  transaction.amount < 0 ? 'text-red-400' : 'text-green-400'
                }`}>
                  {transaction.amount < 0 ? '-' : '+'}{formatCurrency(transaction.amount)}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {sortedTransactions.length > 10 && (
        <div className="mt-4 text-center">
          <p className="text-xs text-[var(--text-secondary)]">
            Showing {recentTransactions.length} of {sortedTransactions.length} transactions
          </p>
        </div>
      )}
    </div>
  );
}
