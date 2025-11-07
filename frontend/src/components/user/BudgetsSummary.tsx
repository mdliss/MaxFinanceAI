'use client'

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import Link from 'next/link';

interface BudgetsSummaryProps {
  userId: string;
}

export default function BudgetsSummary({ userId }: BudgetsSummaryProps) {
  const [budgets, setBudgets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchBudgets = async () => {
      try {
        const data = await api.budgets.getBudgets(userId);
        // Map API response to match frontend interface
        const mappedBudgets = data.map((budget: any) => ({
          id: budget.budget_id,
          user_id: budget.user_id,
          category: budget.category,
          limit: budget.amount,
          spent: budget.spent_amount,
          remaining: budget.remaining_amount,
          spending_percentage: (budget.spent_amount / budget.amount) * 100
        }));
        // Show top 3 budgets sorted by percentage (highest first)
        const sorted = [...mappedBudgets].sort((a, b) => {
          const aPercent = a.spending_percentage || 0;
          const bPercent = b.spending_percentage || 0;
          return bPercent - aPercent;
        });
        setBudgets(sorted.slice(0, 3));
      } catch (error) {
        console.error('Error fetching budgets:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchBudgets();
  }, [userId]);

  if (loading) {
    return (
      <div className="card-dark p-6 h-64 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (budgets.length === 0) {
    return (
      <div className="card-dark p-6 h-64 flex flex-col items-center justify-center text-center">
        <h3 className="font-semibold mb-2">No Budgets Yet</h3>
        <p className="text-sm text-[var(--text-secondary)] mb-4">
          Create budgets to monitor your spending
        </p>
        <Link href="/budgets" className="text-sm text-[var(--accent-primary)] hover:underline font-medium">
          Create a budget →
        </Link>
      </div>
    );
  }

  const getStatusColor = (percentage: number) => {
    if (percentage >= 100) return '#1e40af';
    if (percentage >= 90) return '#2563eb';
    if (percentage >= 75) return '#3b82f6';
    return '#60a5fa';
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="card-dark p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Budget Tracker</h3>
        <Link href="/budgets" className="text-sm text-[var(--accent-primary)] hover:underline">
          View all
        </Link>
      </div>

      <div className="space-y-4">
        {budgets.map((budget) => {
          const percentage = budget.spending_percentage || ((budget.spent / budget.limit) * 100);
          const isOverBudget = percentage >= 100;

          return (
            <div key={budget.id} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0 mr-3">
                  <p className="font-medium text-sm capitalize truncate">{budget.category}</p>
                  <p className="text-xs text-[var(--text-secondary)]">
                    {formatCurrency(budget.spent)} of {formatCurrency(budget.limit)}
                  </p>
                </div>
                <span
                  className="text-sm font-bold flex-shrink-0"
                  style={{ color: getStatusColor(percentage) }}
                >
                  {percentage.toFixed(0)}%
                </span>
              </div>
              <div className="h-2 bg-[var(--bg-tertiary)] rounded-full overflow-hidden border border-[var(--border-color)]">
                <div
                  className="h-full"
                  style={{
                    width: `${Math.min(percentage, 100)}%`,
                    backgroundColor: getStatusColor(percentage),
                  }}
                />
              </div>
              {isOverBudget && (
                <p className="text-xs text-blue-900 font-medium">
                  Over by {formatCurrency(Math.abs(budget.remaining))}
                </p>
              )}
            </div>
          );
        })}
      </div>

      {budgets.length === 3 && (
        <div className="mt-4 pt-4 border-t border-[var(--border-color)] text-center">
          <Link href="/budgets" className="text-sm text-[var(--accent-primary)] hover:underline font-medium">
            View all budgets →
          </Link>
        </div>
      )}
    </div>
  );
}
