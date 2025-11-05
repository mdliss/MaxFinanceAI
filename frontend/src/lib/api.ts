import type {
  User,
  UserProfile,
  Recommendation,
  AuditLog,
  GuardrailSummary,
  ToneCheckResult,
  FeedbackSubmission,
  EvaluationMetrics,
  DecisionTrace
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

console.log('🔧 API Configuration:', {
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  API_BASE_URL,
  allEnv: Object.keys(process.env).filter(k => k.startsWith('NEXT_PUBLIC'))
});

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const fullUrl = `${API_BASE_URL}${endpoint}`;
  console.log(`🌐 API Request: ${options?.method || 'GET'} ${fullUrl}`);

  const response = await fetch(fullUrl, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  console.log(`📡 API Response: ${response.status} ${response.statusText} for ${fullUrl}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    console.error(`❌ API Error:`, error);
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  const data = await response.json();
  console.log(`✅ API Success:`, data);
  return data;
}

export const api = {
  // User Management
  getUsers: () => fetchAPI<User[]>('/users/'),

  getUser: (userId: string) => fetchAPI<User>(`/users/${userId}`),

  getUserProfile: (userId: string) => fetchAPI<UserProfile>(`/profile/${userId}`),

  // Recommendations
  getRecommendations: (userId: string, status?: string) => {
    const params = status ? `?status=${status}` : '';
    return fetchAPI<Recommendation[]>(`/recommendations/${userId}${params}`);
  },

  getAllRecommendations: async (status?: string, limit: number = 500) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit.toString());
    const queryString = params.toString() ? `?${params.toString()}` : '';
    const response = await fetchAPI<{ recommendations: Recommendation[]; total: number }>(`/operator/recommendations${queryString}`);
    return response.recommendations;
  },

  submitFeedback: (feedback: FeedbackSubmission) =>
    fetchAPI<{ message: string }>('/recommendations/feedback', {
      method: 'POST',
      body: JSON.stringify(feedback),
    }),

  // Operator Actions
  approveRecommendation: (recommendationId: number, notes?: string) =>
    fetchAPI<Recommendation>(`/operator/approve/${recommendationId}`, {
      method: 'POST',
      body: JSON.stringify({ operator_notes: notes }),
    }),

  overrideRecommendation: (
    recommendationId: number,
    updates: { title?: string; description?: string; rationale?: string },
    notes?: string
  ) =>
    fetchAPI<Recommendation>(`/operator/override/${recommendationId}`, {
      method: 'POST',
      body: JSON.stringify({ ...updates, operator_notes: notes }),
    }),

  flagRecommendation: (
    recommendationId: number,
    reason: string,
    severity: 'low' | 'medium' | 'high'
  ) =>
    fetchAPI<Recommendation>(`/operator/flag/${recommendationId}`, {
      method: 'POST',
      body: JSON.stringify({ reason, severity }),
    }),

  // Guardrails
  getGuardrailSummary: () => fetchAPI<GuardrailSummary>('/guardrails/summary'),

  checkTone: (text: string) =>
    fetchAPI<ToneCheckResult>('/guardrails/tone-check', {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),

  // Audit Log
  getAuditLogs: async (userId?: string, limit = 100) => {
    const params = userId ? `?user_id=${userId}&limit=${limit}` : `?limit=${limit}`;
    const response = await fetchAPI<{ logs: AuditLog[]; total: number }>(`/operator/audit-logs${params}`);
    return response.logs;
  },

  // Auto-flagging
  autoFlagRecommendations: () =>
    fetchAPI<{ message: string; flagged_count: number; rules_applied: string[] }>(
      '/operator/auto-flag-recommendations',
      { method: 'POST' }
    ),

  // Priority Queue
  getPriorityQueue: () =>
    fetchAPI<{
      flagged_count: number;
      pending_count: number;
      high_risk_approved_count: number;
      workflow_steps: Array<{
        step: number;
        title: string;
        count: number;
        status: string;
      }>;
    }>('/operator/stats/priority-queue'),

  // Stats
  getRecommendationsByPersona: () =>
    fetchAPI<{ persona_stats: Array<{ persona_type: string; count: number }> }>(
      '/operator/stats/recommendations-by-persona'
    ),

  getDashboardStats: () =>
    fetchAPI<{
      total_users: number;
      users_with_consent: number;
      total_recommendations: number;
      pending_recommendations: number;
      approved_recommendations: number;
      total_signals: number;
      total_personas: number;
      total_transactions: number;
      recent_consent_changes: number;
    }>('/operator/dashboard/stats'),

  // Evaluation Metrics
  getEvaluationMetrics: () =>
    fetchAPI<EvaluationMetrics>('/operator/evaluation/metrics'),

  getDecisionTrace: (recommendationId: number) =>
    fetchAPI<DecisionTrace>(`/operator/decision-trace/${recommendationId}`),

  // Accounts
  getAccounts: (userId: string) =>
    fetchAPI<any[]>(`/accounts/${userId}`),

  getCreditUtilization: (userId: string) =>
    fetchAPI<{
      total_balance: number;
      total_limit: number;
      utilization_percentage: number;
      accounts: any[];
    }>(`/accounts/${userId}/credit-utilization`),

  // Transactions
  getTransactions: (userId: string, limit?: number, offset?: number) => {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return fetchAPI<any[]>(`/transactions/${userId}${queryString}`);
  },

  getSpendingCategories: (userId: string, days?: number) => {
    const params = days ? `?days=${days}` : '';
    return fetchAPI<{
      categories: Array<{
        category: string;
        amount: number;
        percentage: number;
        transaction_count: number;
      }>;
      total_spending: number;
      period_start: string;
      period_end: string;
    }>(`/transactions/${userId}/spending-categories${params}`);
  },

  getSavingsHistory: (userId: string, months?: number) => {
    const params = months ? `?months=${months}` : '';
    return fetchAPI<{
      history: Array<{
        date: string;
        balance: number;
        month: string;
      }>;
      growth_rate: number;
      current_balance: number;
      starting_balance: number;
    }>(`/transactions/${userId}/savings-history${params}`);
  },
};
