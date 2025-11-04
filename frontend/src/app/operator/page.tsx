'use client'

import { useState } from 'react';
import UserSearch from '@/components/operator/UserSearch';
import UserProfile from '@/components/operator/UserProfile';
import RecommendationQueue from '@/components/operator/RecommendationQueue';
import GuardrailsSummary from '@/components/operator/GuardrailsSummary';
import AuditLog from '@/components/operator/AuditLog';

type TabType = 'profile' | 'queue' | 'guardrails' | 'audit';

export default function OperatorDashboard() {
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('queue');

  const tabs: { id: TabType; label: string }[] = [
    { id: 'queue', label: 'Recommendation Queue' },
    { id: 'profile', label: 'User Profile' },
    { id: 'guardrails', label: 'Guardrails' },
    { id: 'audit', label: 'Audit Log' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Operator Dashboard</h1>
          <p className="text-sm text-gray-600 mt-1">
            Review and manage user recommendations
          </p>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* User Search */}
        <div className="mb-6">
          <UserSearch
            onUserSelect={setSelectedUserId}
            selectedUserId={selectedUserId}
          />
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    px-6 py-3 text-sm font-medium border-b-2 transition-colors
                    ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'queue' && <RecommendationQueue userId={selectedUserId} />}
            {activeTab === 'profile' && (
              <>
                {selectedUserId ? (
                  <UserProfile userId={selectedUserId} />
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    Select a user to view their profile
                  </div>
                )}
              </>
            )}
            {activeTab === 'guardrails' && <GuardrailsSummary />}
            {activeTab === 'audit' && <AuditLog userId={selectedUserId} />}
          </div>
        </div>
      </div>
    </div>
  );
}
