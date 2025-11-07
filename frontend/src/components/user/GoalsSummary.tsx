'use client'

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import Link from 'next/link';

interface GoalsSummaryProps {
  userId: string;
}

export default function GoalsSummary({ userId }: GoalsSummaryProps) {
  const [goals, setGoals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchGoals = async () => {
      try {
        const data = await api.goals.getGoals(userId);
        setGoals(data.slice(0, 3)); // Show top 3 goals
      } catch (error) {
        console.error('Error fetching goals:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchGoals();
  }, [userId]);

  if (loading) {
    return (
      <div className="card-dark p-6 h-64 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (goals.length === 0) {
    return (
      <div className="card-dark p-6 h-64 flex flex-col items-center justify-center text-center">
        <h3 className="font-semibold mb-2">No Goals Yet</h3>
        <p className="text-sm text-[var(--text-secondary)] mb-4">
          Set financial goals to track your progress
        </p>
        <Link href="/goals" className="text-sm text-[var(--accent-primary)] hover:underline font-medium">
          Create a goal →
        </Link>
      </div>
    );
  }

  const getProgressColor = (percentage: number) => {
    if (percentage >= 100) return '#1e40af';
    if (percentage >= 75) return '#2563eb';
    if (percentage >= 50) return '#3b82f6';
    if (percentage >= 25) return '#60a5fa';
    return '#93c5fd';
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
        <h3 className="text-lg font-semibold">Financial Goals</h3>
        <Link href="/goals" className="text-sm text-[var(--accent-primary)] hover:underline">
          View all
        </Link>
      </div>

      <div className="space-y-4">
        {goals.map((goal) => {
          const progress = goal.progress_percentage || ((goal.current_amount / goal.target_amount) * 100);

          return (
            <div key={goal.id} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0 mr-3">
                  <p className="font-medium text-sm truncate">{goal.name}</p>
                  <p className="text-xs text-[var(--text-secondary)]">
                    {formatCurrency(goal.current_amount)} of {formatCurrency(goal.target_amount)}
                  </p>
                </div>
                <span
                  className="text-sm font-bold flex-shrink-0"
                  style={{ color: getProgressColor(progress) }}
                >
                  {progress.toFixed(0)}%
                </span>
              </div>
              <div className="h-2 bg-[var(--bg-tertiary)] rounded-full overflow-hidden border border-[var(--border-color)]">
                <div
                  className="h-full"
                  style={{
                    width: `${Math.min(progress, 100)}%`,
                    backgroundColor: getProgressColor(progress),
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {goals.length === 3 && (
        <div className="mt-4 pt-4 border-t border-[var(--border-color)] text-center">
          <Link href="/goals" className="text-sm text-[var(--accent-primary)] hover:underline font-medium">
            View all goals →
          </Link>
        </div>
      )}
    </div>
  );
}
