import type {
  User,
  UserProfile,
  Recommendation,
  AuditLog,
  GuardrailSummary,
  ToneCheckResult,
  FeedbackSubmission
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

  getAllRecommendations: async (status?: string) => {
    const params = status ? `?status=${status}` : '';
    const response = await fetchAPI<{ recommendations: Recommendation[]; total: number }>(`/operator/recommendations${params}`);
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
};
