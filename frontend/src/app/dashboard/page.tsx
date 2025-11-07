'use client'

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import DashboardSummary from '@/components/user/DashboardSummary';
import TransactionsList from '@/components/user/TransactionsList';
import RecommendationsForUser from '@/components/user/RecommendationsForUser';
import ConsentManagement from '@/components/user/ConsentManagement';
import FinancialChatbot from '@/components/user/FinancialChatbot';
import CreditUtilizationGauge from '@/components/user/CreditUtilizationGauge';
import SpendingPieChart from '@/components/user/SpendingPieChart';
import SavingsLineChart from '@/components/user/SavingsLineChart';
import BehavioralSignals from '@/components/user/BehavioralSignals';
import AlertsCenter from '@/components/user/AlertsCenter';
import GoalsSummary from '@/components/user/GoalsSummary';
import BudgetsSummary from '@/components/user/BudgetsSummary';

export default function UserDashboard() {
  const router = useRouter();
  const [userId, setUserId] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>('');
  const [loading, setLoading] = useState(true);

  // Financial data state
  const [creditUtilization, setCreditUtilization] = useState<any>(null);
  const [savingsHistory, setSavingsHistory] = useState<any>(null);
  const [spendingCategories, setSpendingCategories] = useState<any>(null);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [dataLoading, setDataLoading] = useState(true);

  useEffect(() => {
    const storedUserId = localStorage.getItem('userId');
    const storedUserName = localStorage.getItem('userName');

    if (!storedUserId) {
      router.push('/login');
      return;
    }

    setUserId(storedUserId);
    setUserName(storedUserName || 'User');
    setLoading(false);
  }, [router]);

  // Fetch financial data when userId is available
  useEffect(() => {
    if (!userId) return;

    const fetchFinancialData = async () => {
      setDataLoading(true);
      try {
        // Fetch all data in parallel - INCLUDES USER PROFILE to avoid duplicate calls
        const [profileData, creditData, savingsData, spendingData] = await Promise.all([
          api.getUserProfile(userId).catch(() => null),
          api.getCreditUtilization(userId).catch(() => null),
          api.getSavingsHistory(userId, 6).catch(() => null),
          api.getSpendingCategories(userId, 30).catch(() => null),
        ]);

        setUserProfile(profileData);
        setCreditUtilization(creditData);
        setSavingsHistory(savingsData);
        setSpendingCategories(spendingData);
      } catch (error) {
        console.error('Error fetching financial data:', error);
      } finally {
        setDataLoading(false);
      }
    };

    fetchFinancialData();
  }, [userId]);

  const handleLogout = () => {
    localStorage.removeItem('userId');
    localStorage.removeItem('userName');
    router.push('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-[var(--text-secondary)]">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

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
              <Link href="/dashboard" className="text-sm font-semibold text-[var(--accent-primary)]">
                Dashboard
              </Link>
              <Link href="/goals" className="text-sm text-[var(--text-secondary)] hover:text-[var(--accent-primary)] transition-smooth">
                Goals
              </Link>
              <Link href="/budgets" className="text-sm text-[var(--text-secondary)] hover:text-[var(--accent-primary)] transition-smooth">
                Budgets
              </Link>
              <div className="flex items-center gap-4 ml-4 pl-4 border-l border-[var(--border-color)]">
                <AlertsCenter userId={userId} />
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
        {/* Page Title */}
        <div className="mb-8 drop-in-1">
          <h1 className="text-3xl font-bold mb-2">My Dashboard</h1>
          <p className="text-[var(--text-secondary)]">
            View your financial overview, expenses, and personalized recommendations
          </p>
        </div>

        {/* Dashboard Summary */}
        <div className="mb-8 drop-in-2">
          <DashboardSummary userId={userId} profile={userProfile} />
        </div>

        {/* Financial Visualizations */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="drop-in-3">
            {dataLoading ? (
              <div className="card-elevated h-64 flex items-center justify-center">
                <div className="w-8 h-8 border-4 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : (
              <CreditUtilizationGauge
                utilization={creditUtilization?.utilization_percentage || 0}
                limit={creditUtilization?.total_limit || 0}
                balance={creditUtilization?.total_balance || 0}
              />
            )}
          </div>
          <div className="drop-in-3">
            {dataLoading ? (
              <div className="card-elevated h-64 flex items-center justify-center">
                <div className="w-8 h-8 border-4 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : (
              <SavingsLineChart
                data={savingsHistory?.history || []}
                growthRate={savingsHistory?.growth_rate || 0}
              />
            )}
          </div>
          <div className="drop-in-3">
            {dataLoading ? (
              <div className="card-elevated h-64 flex items-center justify-center">
                <div className="w-8 h-8 border-4 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : (
              <SpendingPieChart
                data={spendingCategories?.categories || []}
              />
            )}
          </div>
        </div>

        {/* Behavioral Signals */}
        <div className="mb-8 drop-in-4">
          <BehavioralSignals userId={userId} profile={userProfile} />
        </div>

        {/* V2 Features: Goals & Budgets */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="drop-in-5">
            <GoalsSummary userId={userId} />
          </div>
          <div className="drop-in-5">
            <BudgetsSummary userId={userId} />
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column: Transactions */}
          <div className="drop-in-6">
            <TransactionsList userId={userId} />
          </div>

          {/* Right Column: Recommendations */}
          <div className="drop-in-6">
            <RecommendationsForUser userId={userId} />
          </div>
        </div>

        {/* Consent Management */}
        <div className="mt-8 drop-in-7">
          <ConsentManagement userId={userId} />
        </div>
      </div>

      {/* Floating Financial Chatbot */}
      <FinancialChatbot userId={userId} />
    </div>
  );
}
