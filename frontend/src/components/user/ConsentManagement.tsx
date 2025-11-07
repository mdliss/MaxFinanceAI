'use client'

import { useEffect, useState } from 'react';

interface ConsentManagementProps {
  userId: string;
}

interface ConsentStatus {
  user_id: string;
  consent_status: boolean;
  consent_timestamp: string | null;
}

export default function ConsentManagement({ userId }: ConsentManagementProps) {
  const [consent, setConsent] = useState<ConsentStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    fetchConsentStatus();
  }, [userId]);

  const fetchConsentStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/v1/consent/${userId}`);
      const data = await response.json();
      setConsent(data);
    } catch (err) {
      console.error('Failed to fetch consent status:', err);
    } finally {
      setLoading(false);
    }
  };

  const updateConsent = async (status: boolean) => {
    try {
      setUpdating(true);
      const response = await fetch('http://localhost:8000/api/v1/consent/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          consent_status: status,
        }),
      });

      if (response.ok) {
        await fetchConsentStatus();
      }
    } catch (err) {
      console.error('Failed to update consent:', err);
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="card-dark p-6 transition-smooth">
        <div className="animate-pulse h-24 bg-[var(--bg-tertiary)] rounded"></div>
      </div>
    );
  }

  return (
    <div className={`card-dark p-6 transition-smooth border-l-4 ${
      consent?.consent_status ? 'border-green-500' : 'border-yellow-500'
    }`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-semibold">Data Sharing Consent</h3>
            <span className={`text-xs px-2 py-1 rounded ${
              consent?.consent_status
                ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
            }`}>
              {consent?.consent_status ? 'Active' : 'Inactive'}
            </span>
          </div>

          <p className="text-sm text-[var(--text-secondary)] mb-4">
            {consent?.consent_status
              ? 'You have granted permission for FinanceMaxAI to analyze your financial data and provide personalized recommendations.'
              : 'Grant consent to receive personalized financial insights and recommendations based on your spending patterns.'}
          </p>

          {consent?.consent_timestamp && (
            <p className="text-xs text-[var(--text-secondary)]">
              Last updated: {new Date(consent.consent_timestamp).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          )}
        </div>

        <div className="ml-4">
          <button
            onClick={() => updateConsent(!consent?.consent_status)}
            disabled={updating}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-smooth ${
              consent?.consent_status
                ? 'bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30'
                : 'bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30'
            } ${updating ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {updating ? 'Updating...' : consent?.consent_status ? 'Revoke' : 'Grant Consent'}
          </button>
        </div>
      </div>
    </div>
  );
}
