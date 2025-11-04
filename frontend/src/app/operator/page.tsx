'use client'

import { useState } from 'react';
import DashboardStats from '@/components/operator/DashboardStats';
import ImprovedRecommendationQueue from '@/components/operator/ImprovedRecommendationQueue';
import UserSearch from '@/components/operator/UserSearch';
import UserProfile from '@/components/operator/UserProfile';
import AuditLog from '@/components/operator/AuditLog';

type TabType = 'overview' | 'recommendations' | 'users' | 'audit';

export default function OperatorDashboard() {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);

  const tabs: { id: TabType; label: string; icon: string }[] = [
    { id: 'overview', label: 'Dashboard Overview', icon: '📊' },
    { id: 'recommendations', label: 'Recommendation Queue', icon: '📋' },
    { id: 'users', label: 'User Management', icon: '👥' },
    { id: 'audit', label: 'Audit Log', icon: '📝' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                SpendSense Operator Dashboard
              </h1>
              <p className="text-sm text-gray-600 mt-2">
                Review and manage personalized financial education recommendations
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500">Operator View</p>
              <p className="text-sm font-medium text-gray-900">Human Oversight Required</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    px-6 py-4 text-sm font-medium border-b-2 transition-colors flex items-center gap-2
                    ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600 bg-blue-50'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <span className="text-lg">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div>
                <div className="mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">
                    System Overview
                  </h2>
                  <p className="text-sm text-gray-600">
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
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">
                    Recommendation Queue
                  </h2>
                  <p className="text-sm text-gray-600">
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
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">
                    User Management
                  </h2>
                  <p className="text-sm text-gray-600">
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
                  <div className="mt-6 bg-gray-50 rounded-lg p-12 text-center">
                    <p className="text-gray-500">
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
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">
                    System Audit Log
                  </h2>
                  <p className="text-sm text-gray-600">
                    Track all operator actions, consent changes, and system events for compliance
                  </p>
                </div>
                <AuditLog userId={selectedUserId} />
              </div>
            )}
          </div>
        </div>

        {/* Help Section */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
          <h3 className="font-semibold text-gray-900 mb-2">💡 Quick Guide</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="font-medium text-gray-900 mb-1">Dashboard Overview:</p>
              <ul className="text-gray-700 space-y-1 list-disc list-inside">
                <li>View real-time stats and workflow priorities</li>
                <li>Run auto-flagging to identify recommendations needing review</li>
                <li>Follow numbered workflow steps for efficient review</li>
              </ul>
            </div>
            <div>
              <p className="font-medium text-gray-900 mb-1">Recommendation Queue:</p>
              <ul className="text-gray-700 space-y-1 list-disc list-inside">
                <li>Filter by status, persona, or search terms</li>
                <li>Review flagged items first (red badges)</li>
                <li>Approve safe recommendations or flag concerns</li>
                <li>View details to see audit history</li>
              </ul>
            </div>
            <div>
              <p className="font-medium text-gray-900 mb-1">User Management:</p>
              <ul className="text-gray-700 space-y-1 list-disc list-inside">
                <li>Search users by name or ID</li>
                <li>View behavioral signals and personas</li>
                <li>Check consent status</li>
              </ul>
            </div>
            <div>
              <p className="font-medium text-gray-900 mb-1">Audit Log:</p>
              <ul className="text-gray-700 space-y-1 list-disc list-inside">
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
