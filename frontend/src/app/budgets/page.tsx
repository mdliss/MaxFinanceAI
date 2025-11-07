'use client'

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import AlertsCenter from '@/components/user/AlertsCenter';

interface Budget {
  id: number;
  user_id: string;
  category: string;
  limit: number;
  period: string;
  start_date: string;
  spent: number;
  remaining: number;
  status: string;
  created_at: string;
  spending_percentage?: number;
}

export default function BudgetsPage() {
  const router = useRouter();
  const [userId, setUserId] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>('');
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Create budget form state
  const [newBudget, setNewBudget] = useState({
    category: '',
    limit: '',
    period: 'monthly',
    start_date: new Date().toISOString().split('T')[0],
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

    const fetchBudgets = async () => {
      setLoading(true);
      try {
        const data = await api.budgets.getBudgets(userId);
        // Map API response to match frontend interface
        const mappedBudgets = data.map((budget: any) => ({
          id: budget.budget_id,
          user_id: budget.user_id,
          category: budget.category,
          limit: budget.amount,
          period: budget.period,
          start_date: budget.period_start_date,
          spent: budget.spent_amount,
          remaining: budget.remaining_amount,
          status: budget.status,
          created_at: budget.created_at,
          spending_percentage: (budget.spent_amount / budget.amount) * 100
        }));
        setBudgets(mappedBudgets);
      } catch (error) {
        console.error('Error fetching budgets:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchBudgets();
  }, [userId]);

  const handleLogout = () => {
    localStorage.removeItem('userId');
    localStorage.removeItem('userName');
    router.push('/');
  };

  const handleCreateBudget = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userId) return;

    try {
      await api.budgets.createBudget(userId, {
        category: newBudget.category,
        limit: parseFloat(newBudget.limit),
        period: newBudget.period,
        start_date: newBudget.start_date,
      });

      // Reset form and refresh budgets
      setNewBudget({
        category: '',
        limit: '',
        period: 'monthly',
        start_date: new Date().toISOString().split('T')[0],
      });
      setShowCreateModal(false);

      // Refresh budgets list
      const data = await api.budgets.getBudgets(userId);
      const mappedBudgets = data.map((budget: any) => ({
        id: budget.budget_id,
        user_id: budget.user_id,
        category: budget.category,
        limit: budget.amount,
        period: budget.period,
        start_date: budget.period_start_date,
        spent: budget.spent_amount,
        remaining: budget.remaining_amount,
        status: budget.status,
        created_at: budget.created_at,
        spending_percentage: (budget.spent_amount / budget.amount) * 100
      }));
      setBudgets(mappedBudgets);
    } catch (error) {
      console.error('Error creating budget:', error);
      alert('Failed to create budget. Please try again.');
    }
  };

  const getGaugeColor = (percentage: number) => {
    if (percentage >= 100) return '#1e40af'; // deep blue
    if (percentage >= 90) return '#2563eb'; // blue-600
    if (percentage >= 75) return '#3b82f6'; // blue-500
    return '#60a5fa'; // blue-400
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
              <Link href="/goals" className="text-sm text-[var(--text-secondary)] hover:text-[var(--accent-primary)] transition-smooth">
                Goals
              </Link>
              <Link href="/budgets" className="text-sm font-semibold text-[var(--accent-primary)]">
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
              <h1 className="text-3xl font-bold mb-2">Budget Tracker</h1>
              <p className="text-[var(--text-secondary)]">
                Monitor your spending across different categories
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-accent transition-smooth"
            >
              + Create Budget
            </button>
          </div>
        </div>

        {/* Budgets List */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-12 h-12 border-4 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : budgets.length === 0 ? (
          <div className="card-dark p-12 text-center drop-in-2">
            <div className="max-w-md mx-auto">
              <h3 className="text-xl font-semibold mb-2">No budgets yet</h3>
              <p className="text-[var(--text-secondary)] mb-6">
                Create your first budget to track your spending
              </p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="btn-accent transition-smooth"
              >
                Create Your First Budget
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {budgets.map((budget, index) => {
              const percentage = budget.spending_percentage ||
                ((budget.spent / budget.limit) * 100);
              const isOverBudget = percentage >= 100;
              const isWarning = percentage >= 90;

              const gaugeData = [
                { name: 'Spent', value: Math.min(percentage, 100) },
                { name: 'Remaining', value: Math.max(100 - percentage, 0) },
              ];

              const COLORS = [getGaugeColor(percentage), '#e0e0de'];

              return (
                <div
                  key={budget.id}
                  className={`card-dark p-6 drop-in-${Math.min(index + 2, 6)}`}
                >
                  {/* Budget Header */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-lg font-semibold capitalize">{budget.category}</h3>
                      {isOverBudget && (
                        <span className="px-2 py-0.5 bg-blue-500/10 text-blue-700 text-xs font-semibold rounded">
                          OVER
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-[var(--text-secondary)] capitalize">
                      {budget.period} budget
                    </p>
                  </div>

                  {/* Gauge Chart */}
                  <div className="relative mb-4">
                    <ResponsiveContainer width="100%" height={160}>
                      <PieChart>
                        <Pie
                          data={gaugeData}
                          cx="50%"
                          cy="50%"
                          startAngle={180}
                          endAngle={0}
                          innerRadius={50}
                          outerRadius={70}
                          paddingAngle={0}
                          dataKey="value"
                        >
                          {gaugeData.map((entry, idx) => (
                            <Cell key={`cell-${idx}`} fill={COLORS[idx]} />
                          ))}
                        </Pie>
                      </PieChart>
                    </ResponsiveContainer>

                    {/* Center Text */}
                    <div className="absolute inset-0 flex items-center justify-center" style={{ marginTop: '-15px' }}>
                      <div className="text-center">
                        <div className="text-3xl font-bold" style={{ color: getGaugeColor(percentage) }}>
                          {percentage.toFixed(0)}%
                        </div>
                        <div className="text-xs text-[var(--text-muted)]">Spent</div>
                      </div>
                    </div>
                  </div>

                  {/* Budget Details */}
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-[var(--text-secondary)]">Spent:</span>
                      <span className="font-semibold">{formatCurrency(budget.spent)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-secondary)]">Limit:</span>
                      <span className="font-semibold">{formatCurrency(budget.limit)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-secondary)]">Remaining:</span>
                      <span className={`font-semibold ${isOverBudget ? 'text-blue-900' : 'text-blue-700'}`}>
                        {formatCurrency(budget.remaining)}
                      </span>
                    </div>
                  </div>

                  {/* Warning Message */}
                  {isWarning && (
                    <div className={`mt-4 p-3 rounded-lg text-xs transition-smooth ${
                      isOverBudget
                        ? 'bg-blue-500/10 text-blue-900 border border-blue-500/20'
                        : 'bg-blue-400/10 text-blue-800 border border-blue-400/20'
                    }`}>
                      {isOverBudget
                        ? `Over budget by ${formatCurrency(Math.abs(budget.remaining))}`
                        : 'Approaching budget limit'}
                    </div>
                  )}

                  {/* Budget Footer */}
                  <div className="mt-4 pt-4 border-t border-[var(--border-color)] text-xs text-[var(--text-secondary)]">
                    Started: {formatDate(budget.start_date)}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Create Budget Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 modal-backdrop">
          <div className="bg-[var(--bg-secondary)] rounded-lg max-w-lg w-full mx-4 modal-content">
            <div className="p-6 border-b border-[var(--border-color)]">
              <h2 className="text-2xl font-bold">Create New Budget</h2>
            </div>
            <form onSubmit={handleCreateBudget} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Category</label>
                <input
                  type="text"
                  required
                  value={newBudget.category}
                  onChange={(e) => setNewBudget({ ...newBudget, category: e.target.value })}
                  className="w-full px-4 py-2 border border-[var(--border-color)] rounded-lg focus:outline-none focus:border-[var(--accent-primary)] transition-smooth bg-[var(--bg-primary)]"
                  placeholder="groceries, entertainment, etc."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Budget Limit ($)</label>
                <input
                  type="number"
                  required
                  step="0.01"
                  min="0"
                  value={newBudget.limit}
                  onChange={(e) => setNewBudget({ ...newBudget, limit: e.target.value })}
                  className="w-full px-4 py-2 border border-[var(--border-color)] rounded-lg focus:outline-none focus:border-[var(--accent-primary)] transition-smooth bg-[var(--bg-primary)]"
                  placeholder="500.00"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Period</label>
                <select
                  value={newBudget.period}
                  onChange={(e) => setNewBudget({ ...newBudget, period: e.target.value })}
                  className="w-full px-4 py-2 border border-[var(--border-color)] rounded-lg focus:outline-none focus:border-[var(--accent-primary)] transition-smooth bg-[var(--bg-primary)]"
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Start Date</label>
                <input
                  type="date"
                  required
                  value={newBudget.start_date}
                  onChange={(e) => setNewBudget({ ...newBudget, start_date: e.target.value })}
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
                  Create Budget
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
