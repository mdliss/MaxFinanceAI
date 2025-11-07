'use client'

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface Transaction {
  transaction_id: string;
  date: string;
  amount: number;
  merchant_name: string;
  category_primary: string;
  category_detailed: string;
  payment_channel: string;
}

interface TransactionsListProps {
  userId: string;
}

export default function TransactionsList({ userId }: TransactionsListProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        setLoading(true);
        const data = await api.getTransactions(userId, 10);
        setTransactions(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load transactions');
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
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

  if (error) {
    return (
      <div className="card-dark p-6 border-l-4 border-red-500">
        <p className="text-red-400">
          {error || 'Unable to load transactions'}
        </p>
      </div>
    );
  }

  // Filter transactions by category
  const filteredTransactions = filter === 'all'
    ? transactions
    : transactions.filter(t => t.category_detailed?.toLowerCase() === filter.toLowerCase());

  // Get unique categories from transactions
  const categories = Array.from(new Set(transactions.map(t => t.category_detailed).filter(Boolean)));

  // Sort transactions by date (most recent first)
  const sortedTransactions = [...filteredTransactions].sort((a, b) => {
    return new Date(b.date).getTime() - new Date(a.date).getTime();
  });

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
      groceries: 'bg-green-500/10 text-green-400 border-green-500/20',
      restaurants: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
      'general merchandise': 'bg-purple-500/10 text-purple-400 border-purple-500/20',
      entertainment: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
      'gas stations': 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      utilities: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
      paycheck: 'bg-green-600/10 text-green-500 border-green-600/20',
      income: 'bg-green-600/10 text-green-500 border-green-600/20',
    };
    return colors[category.toLowerCase()] || 'bg-gray-500/10 text-gray-400 border-gray-500/20';
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

      {sortedTransactions.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-[var(--text-secondary)]">No transactions found</p>
        </div>
      ) : (
        <div className="space-y-2">
          {sortedTransactions.map((transaction) => (
            <div
              key={transaction.transaction_id}
              className="flex items-center justify-between p-4 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-color)] hover:border-[var(--accent-primary)]"
            >
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <div>
                    <p className="font-medium">{transaction.merchant_name}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-xs px-2 py-0.5 rounded border ${getCategoryColor(transaction.category_detailed)}`}>
                        {transaction.category_detailed}
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
