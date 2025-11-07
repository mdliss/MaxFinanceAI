'use client'

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import AlertsCenter from '@/components/user/AlertsCenter';

interface Goal {
  id: number;
  user_id: string;
  name: string;
  target_amount: number;
  current_amount: number;
  deadline: string;
  category: string;
  status: string;
  created_at: string;
  progress_percentage?: number;
}

export default function GoalsPage() {
  const router = useRouter();
  const [userId, setUserId] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>('');
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Create goal form state
  const [newGoal, setNewGoal] = useState({
    name: '',
    target_amount: '',
    current_amount: '',
    deadline: '',
    category: 'savings',
  });

  useEffect(() => {
    const storedUserId = localStorage.getItem('userId');
    const storedUserName = localStorage.getItem('userName');

    if (!storedUserId) {
      router.push('/login');
      return;
    }

    setUserId(storedUserId);
    setUserName(storedUserName || 'User');
  }, [router]);

  useEffect(() => {
    if (!userId) return;

    const fetchGoals = async () => {
      setLoading(true);
      try {
        const data = await api.goals.getGoals(userId);
        setGoals(data);
      } catch (error) {
        console.error('Error fetching goals:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchGoals();
  }, [userId]);

  const handleLogout = () => {
    localStorage.removeItem('userId');
    localStorage.removeItem('userName');
    router.push('/');
  };

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userId) return;

    try {
      await api.goals.createGoal(userId, {
        name: newGoal.name,
        target_amount: parseFloat(newGoal.target_amount),
        current_amount: parseFloat(newGoal.current_amount) || 0,
        deadline: newGoal.deadline,
        category: newGoal.category,
      });

      // Reset form and refresh goals
      setNewGoal({
        name: '',
        target_amount: '',
        current_amount: '',
        deadline: '',
        category: 'savings',
      });
      setShowCreateModal(false);

      // Refresh goals list
      const data = await api.goals.getGoals(userId);
      setGoals(data);
    } catch (error) {
      console.error('Error creating goal:', error);
      alert('Failed to create goal. Please try again.');
    }
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 100) return '#1e40af'; // deep blue
    if (percentage >= 75) return '#2563eb'; // blue-600
    if (percentage >= 50) return '#3b82f6'; // blue-500
    if (percentage >= 25) return '#60a5fa'; // blue-400
    return '#93c5fd'; // blue-300
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getDaysRemaining = (deadline: string) => {
    const today = new Date();
    const end = new Date(deadline);
    const diffTime = end.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  if (!userId) {
    return null;
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Header */}
      <header className="bg-[var(--bg-secondary)] border-b border-[var(--border-color)]">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="text-xl font-bold tracking-tight hover:text-[var(--accent-primary)] transition-smooth">
              FinanceMaxAI
            </Link>
            <div className="flex items-center gap-6">
              <Link href="/dashboard" className="text-sm text-[var(--text-secondary)] hover:text-[var(--accent-primary)] transition-smooth">
                Dashboard
              </Link>
              <Link href="/goals" className="text-sm font-semibold text-[var(--accent-primary)]">
                Goals
              </Link>
              <Link href="/budgets" className="text-sm text-[var(--text-secondary)] hover:text-[var(--accent-primary)] transition-smooth">
                Budgets
              </Link>
              <div className="flex items-center gap-4 ml-4 pl-4 border-l border-[var(--border-color)]">
                {userId && <AlertsCenter userId={userId} />}
                <span className="text-sm text-[var(--text-secondary)]">
                  {userName}
                </span>
                <button
                  onClick={handleLogout}
                  className="btn-secondary transition-smooth text-sm px-4 py-2"
                >
                  Sign Out
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Page Header */}
        <div className="mb-8 drop-in-1">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">Financial Goals</h1>
              <p className="text-[var(--text-secondary)]">
                Track your progress towards your financial objectives
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-accent transition-smooth"
            >
              + Create Goal
            </button>
          </div>
        </div>

        {/* Goals List */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-12 h-12 border-4 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : goals.length === 0 ? (
          <div className="card-dark p-12 text-center drop-in-2">
            <div className="max-w-md mx-auto">
              <h3 className="text-xl font-semibold mb-2">No goals yet</h3>
              <p className="text-[var(--text-secondary)] mb-6">
                Create your first financial goal to start tracking your progress
              </p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="btn-accent transition-smooth"
              >
                Create Your First Goal
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {goals.map((goal, index) => {
              const progress = goal.progress_percentage ||
                ((goal.current_amount / goal.target_amount) * 100);
              const daysRemaining = getDaysRemaining(goal.deadline);
              const isOverdue = daysRemaining < 0;
              const isComplete = progress >= 100;

              return (
                <div
                  key={goal.id}
                  className={`card-dark p-6 drop-in-${Math.min(index + 2, 6)}`}
                >
                  {/* Goal Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-xl font-semibold">{goal.name}</h3>
                        {isComplete && (
                          <span className="px-2 py-0.5 bg-blue-700/10 text-blue-700 text-xs font-semibold rounded">
                            COMPLETE
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-[var(--text-secondary)] capitalize">
                        {goal.category}
                      </p>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-semibold">
                        {formatCurrency(goal.current_amount)}
                      </span>
                      <span className="text-sm text-[var(--text-secondary)]">
                        {formatCurrency(goal.target_amount)}
                      </span>
                    </div>
                    <div className="h-3 bg-[var(--bg-tertiary)] rounded-full overflow-hidden border border-[var(--border-color)]">
                      <div
                        className="h-full transition-smooth"
                        style={{
                          width: `${Math.min(progress, 100)}%`,
                          backgroundColor: getProgressColor(progress),
                        }}
                      />
                    </div>
                    <div className="flex items-center justify-between mt-2">
                      <span
                        className="text-lg font-bold"
                        style={{ color: getProgressColor(progress) }}
                      >
                        {progress.toFixed(1)}%
                      </span>
                      <span className="text-sm text-[var(--text-secondary)]">
                        {formatCurrency(goal.target_amount - goal.current_amount)} remaining
                      </span>
                    </div>
                  </div>

                  {/* Goal Details */}
                  <div className="pt-4 border-t border-[var(--border-color)] space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-[var(--text-secondary)]">Deadline:</span>
                      <span className="font-medium">{formatDate(goal.deadline)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-[var(--text-secondary)]">Time remaining:</span>
                      <span className={`font-medium ${isOverdue ? 'text-blue-900' : ''}`}>
                        {isOverdue
                          ? `${Math.abs(daysRemaining)} days overdue`
                          : `${daysRemaining} days`}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-[var(--text-secondary)]">Status:</span>
                      <span className="font-medium capitalize">{goal.status}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Create Goal Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 modal-backdrop">
          <div className="bg-[var(--bg-secondary)] rounded-lg max-w-lg w-full mx-4 modal-content">
            <div className="p-6 border-b border-[var(--border-color)]">
              <h2 className="text-2xl font-bold">Create New Goal</h2>
            </div>
            <form onSubmit={handleCreateGoal} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Goal Name</label>
                <input
                  type="text"
                  required
                  value={newGoal.name}
                  onChange={(e) => setNewGoal({ ...newGoal, name: e.target.value })}
                  className="w-full px-4 py-2 border border-[var(--border-color)] rounded-lg focus:outline-none focus:border-[var(--accent-primary)] transition-smooth bg-[var(--bg-primary)]"
                  placeholder="Emergency Fund"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Category</label>
                <select
                  value={newGoal.category}
                  onChange={(e) => setNewGoal({ ...newGoal, category: e.target.value })}
                  className="w-full px-4 py-2 border border-[var(--border-color)] rounded-lg focus:outline-none focus:border-[var(--accent-primary)] transition-smooth bg-[var(--bg-primary)]"
                >
                  <option value="savings">Savings</option>
                  <option value="debt_payoff">Debt Payoff</option>
                  <option value="investment">Investment</option>
                  <option value="purchase">Purchase</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Target Amount ($)</label>
                <input
                  type="number"
                  required
                  step="0.01"
                  min="0"
                  value={newGoal.target_amount}
                  onChange={(e) => setNewGoal({ ...newGoal, target_amount: e.target.value })}
                  className="w-full px-4 py-2 border border-[var(--border-color)] rounded-lg focus:outline-none focus:border-[var(--accent-primary)] transition-smooth bg-[var(--bg-primary)]"
                  placeholder="10000.00"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Current Amount ($)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={newGoal.current_amount}
                  onChange={(e) => setNewGoal({ ...newGoal, current_amount: e.target.value })}
                  className="w-full px-4 py-2 border border-[var(--border-color)] rounded-lg focus:outline-none focus:border-[var(--accent-primary)] transition-smooth bg-[var(--bg-primary)]"
                  placeholder="0.00"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Deadline</label>
                <input
                  type="date"
                  required
                  value={newGoal.deadline}
                  onChange={(e) => setNewGoal({ ...newGoal, deadline: e.target.value })}
                  className="w-full px-4 py-2 border border-[var(--border-color)] rounded-lg focus:outline-none focus:border-[var(--accent-primary)] transition-smooth bg-[var(--bg-primary)]"
                />
              </div>
              <div className="flex gap-4 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 btn-secondary transition-smooth"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 btn-accent transition-smooth"
                >
                  Create Goal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
