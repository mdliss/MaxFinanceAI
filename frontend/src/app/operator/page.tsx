'use client'

import { useState } from 'react';
import Link from 'next/link';
import DashboardStats from '@/components/operator/DashboardStats';
import ImprovedRecommendationQueue from '@/components/operator/ImprovedRecommendationQueue';
import UserSearch from '@/components/operator/UserSearch';
import UserProfile from '@/components/operator/UserProfile';
import AuditLog from '@/components/operator/AuditLog';

type TabType = 'overview' | 'recommendations' | 'users' | 'audit';

export default function OperatorDashboard() {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);

  const tabs: { id: TabType; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'recommendations', label: 'Queue' },
    { id: 'users', label: 'Users' },
    { id: 'audit', label: 'Audit' },
  ];

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Header */}
      <header className="bg-[var(--bg-secondary)] border-b border-[var(--border-color)]">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="text-xl font-bold tracking-tight hover:text-[var(--accent-primary)] transition-smooth">
              SpendSense
            </Link>
            <button className="btn-secondary transition-smooth text-sm px-4 py-2">
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Tabs */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  px-6 py-3 text-sm font-medium rounded-lg transition-smooth
                  ${
                    activeTab === tab.id
                      ? 'bg-[var(--accent-primary)] text-[var(--bg-primary)]'
                      : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]'
                  }
                `}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div>
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div>
                <div className="mb-6">
                  <h2 className="text-2xl font-semibold mb-2">
                    System Overview
                  </h2>
                  <p className="text-sm text-[var(--text-secondary)]">
                    Monitor recommendation status, run auto-flagging, and track system health
                  </p>
                </div>
                <DashboardStats />
              </div>
            )}

            {/* Recommendations Tab */}
            {activeTab === 'recommendations' && (
              <div>
                <div className="mb-6">
                  <h2 className="text-2xl font-semibold mb-2">
                    Recommendation Queue
                  </h2>
                  <p className="text-sm text-[var(--text-secondary)]">
                    Review, approve, or flag recommendations before they're delivered to users
                  </p>
                </div>
                <ImprovedRecommendationQueue />
              </div>
            )}

            {/* Users Tab */}
            {activeTab === 'users' && (
              <div>
                <div className="mb-6">
                  <h2 className="text-2xl font-semibold mb-2">
                    User Management
                  </h2>
                  <p className="text-sm text-[var(--text-secondary)]">
                    Search users and view their behavioral profiles
                  </p>
                </div>

                <UserSearch
                  onUserSelect={setSelectedUserId}
                  selectedUserId={selectedUserId}
                />

                {selectedUserId ? (
                  <div className="mt-6">
                    <UserProfile userId={selectedUserId} />
                  </div>
                ) : (
                  <div className="mt-6 card-dark p-12 text-center transition-smooth">
                    <p className="text-[var(--text-secondary)]">
                      Search and select a user to view their profile
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Audit Log Tab */}
            {activeTab === 'audit' && (
              <div>
                <div className="mb-6">
                  <h2 className="text-2xl font-semibold mb-2">
                    System Audit Log
                  </h2>
                  <p className="text-sm text-[var(--text-secondary)]">
                    Track all operator actions, consent changes, and system events for compliance
                  </p>
                </div>
                <AuditLog userId={selectedUserId} />
              </div>
            )}
          </div>
        </div>

        {/* Help Section */}
        <div className="card-dark p-6 border-l-4 border-[var(--accent-primary)] transition-smooth">
          <h3 className="font-semibold mb-4 text-lg">Quick Guide</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
            <div>
              <p className="font-medium mb-2 text-[var(--accent-primary)]">Dashboard Overview:</p>
              <ul className="text-[var(--text-secondary)] space-y-2 list-disc list-inside">
                <li>View real-time stats and workflow priorities</li>
                <li>Run auto-flagging to identify recommendations needing review</li>
                <li>Follow numbered workflow steps for efficient review</li>
              </ul>
            </div>
            <div>
              <p className="font-medium mb-2 text-[var(--accent-primary)]">Recommendation Queue:</p>
              <ul className="text-[var(--text-secondary)] space-y-2 list-disc list-inside">
                <li>Filter by status, persona, or search terms</li>
                <li>Review flagged items first (red badges)</li>
                <li>Approve safe recommendations or flag concerns</li>
                <li>View details to see audit history</li>
              </ul>
            </div>
            <div>
              <p className="font-medium mb-2 text-[var(--accent-primary)]">User Management:</p>
              <ul className="text-[var(--text-secondary)] space-y-2 list-disc list-inside">
                <li>Search users by name or ID</li>
                <li>View behavioral signals and personas</li>
                <li>Check consent status</li>
              </ul>
            </div>
            <div>
              <p className="font-medium mb-2 text-[var(--accent-primary)]">Audit Log:</p>
              <ul className="text-[var(--text-secondary)] space-y-2 list-disc list-inside">
                <li>Track operator approvals and flags</li>
                <li>Monitor consent grant/revoke events</li>
                <li>Ensure compliance and accountability</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
