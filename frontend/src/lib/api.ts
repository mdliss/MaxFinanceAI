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
import type {
  ChatRequest,
  ChatResponse,
  ChatHistory,
  FeedbackRequest,
  FeedbackResponse
} from '@/types/chat';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

console.log('API Configuration:', {
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  API_BASE_URL,
  allEnv: Object.keys(process.env).filter(k => k.startsWith('NEXT_PUBLIC'))
});

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const fullUrl = `${API_BASE_URL}${endpoint}`;
  console.log(`API Request: ${options?.method || 'GET'} ${fullUrl}`);

  const response = await fetch(fullUrl, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  console.log(`API Response: ${response.status} ${response.statusText} for ${fullUrl}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    console.error(`API Error:`, error);
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  const data = await response.json();
  console.log(`API Success:`, data);
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

  // Financial Goals (V2)
  goals: {
    getGoals: (userId: string) =>
      fetchAPI<any[]>(`/goals/${userId}`),

    getGoal: (goalId: number) =>
      fetchAPI<any>(`/goals/goal/${goalId}`),

    createGoal: (userId: string, goal: {
      name: string;
      target_amount: number;
      current_amount: number;
      deadline: string;
      category: string;
    }) =>
      fetchAPI<any>('/goals/', {
        method: 'POST',
        body: JSON.stringify({ user_id: userId, ...goal }),
      }),

    updateGoal: (goalId: number, updates: any) =>
      fetchAPI<any>(`/goals/${goalId}`, {
        method: 'PUT',
        body: JSON.stringify(updates),
      }),

    deleteGoal: (goalId: number) =>
      fetchAPI<{ message: string }>(`/goals/${goalId}`, {
        method: 'DELETE',
      }),

    updateProgress: (goalId: number, currentAmount: number) =>
      fetchAPI<any>(`/goals/${goalId}/progress`, {
        method: 'POST',
        body: JSON.stringify({ current_amount: currentAmount }),
      }),
  },

  // Budgets (V2)
  budgets: {
    getBudgets: (userId: string) =>
      fetchAPI<any[]>(`/budgets/${userId}`),

    getBudget: (budgetId: number) =>
      fetchAPI<any>(`/budgets/budget/${budgetId}`),

    createBudget: (userId: string, budget: {
      category: string;
      limit: number;
      period: string;
      start_date: string;
    }) =>
      fetchAPI<any>('/budgets/', {
        method: 'POST',
        body: JSON.stringify({ user_id: userId, ...budget }),
      }),

    updateBudget: (budgetId: number, updates: any) =>
      fetchAPI<any>(`/budgets/${budgetId}`, {
        method: 'PUT',
        body: JSON.stringify(updates),
      }),

    deleteBudget: (budgetId: number) =>
      fetchAPI<{ message: string }>(`/budgets/${budgetId}`, {
        method: 'DELETE',
      }),

    getSpending: (budgetId: number) =>
      fetchAPI<{ budget: any; spending: number; remaining: number; percentage: number }>(
        `/budgets/${budgetId}/spending`
      ),
  },

  // Alerts (V2)
  alerts: {
    getAlerts: (userId: string, status?: string) => {
      const params = status ? `?status=${status}` : '';
      return fetchAPI<any[]>(`/alerts/${userId}${params}`);
    },

    getAlert: (alertId: number) =>
      fetchAPI<any>(`/alerts/alert/${alertId}`),

    createAlert: (userId: string, alert: {
      alert_type: string;
      severity: string;
      title: string;
      message: string;
      metadata?: any;
    }) =>
      fetchAPI<any>('/alerts/', {
        method: 'POST',
        body: JSON.stringify({ user_id: userId, ...alert }),
      }),

    markAsRead: (alertId: number) =>
      fetchAPI<any>(`/alerts/${alertId}/read`, {
        method: 'POST',
      }),

    dismissAlert: (alertId: number) =>
      fetchAPI<any>(`/alerts/${alertId}/dismiss`, {
        method: 'POST',
      }),

    deleteAlert: (alertId: number) =>
      fetchAPI<{ message: string }>(`/alerts/${alertId}`, {
        method: 'DELETE',
      }),

    getUnreadCount: (userId: string) =>
      fetchAPI<{ unread_count: number }>(`/alerts/${userId}/unread-count`),
  },

  // Chat/Chatbot
  chat: {
    /**
     * Send a message to the financial chatbot
     */
    sendMessage: (userId: string, message: string, conversationId?: string) =>
      fetchAPI<ChatResponse>('/chat/message', {
        method: 'POST',
        body: JSON.stringify({
          user_id: userId,
          message,
          conversation_id: conversationId,
        } as ChatRequest),
      }),

    /**
     * Stream a message response from the chatbot (SSE)
     * Returns an async generator that yields text chunks
     */
    streamMessage: async function* (userId: string, message: string, conversationId?: string) {
      const fullUrl = `${API_BASE_URL}/chat/message/stream`;
      console.log(`Streaming Request: POST ${fullUrl}`);

      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          message,
          conversation_id: conversationId,
        } as ChatRequest),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Stream error' }));
        throw new Error(error.detail || `Stream Error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body reader available');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          // Decode the chunk and add to buffer
          buffer += decoder.decode(value, { stream: true });

          // Process complete SSE messages (separated by \n\n)
          const messages = buffer.split('\n\n');
          buffer = messages.pop() || ''; // Keep the last incomplete message in buffer

          for (const message of messages) {
            if (!message.trim()) continue;

            // Parse SSE format: "data: {...}"
            const dataMatch = message.match(/^data: (.+)$/m);
            if (dataMatch) {
              try {
                const data = JSON.parse(dataMatch[1]);

                // Yield based on event type
                if (data.type === 'chunk') {
                  yield {
                    type: 'chunk' as const,
                    content: data.content,
                  };
                } else if (data.type === 'done') {
                  yield {
                    type: 'done' as const,
                    messageId: data.message_id,
                    conversationId: data.conversation_id,
                  };
                } else if (data.type === 'start') {
                  yield {
                    type: 'start' as const,
                    conversationId: data.conversation_id,
                  };
                } else if (data.type === 'error') {
                  throw new Error(data.error);
                }
              } catch (parseError) {
                console.error('Failed to parse SSE message:', dataMatch[1]);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    },

    /**
     * Get conversation history for a user
     */
    getHistory: (userId: string, limit = 50, conversationId?: string) => {
      const params = new URLSearchParams({ limit: limit.toString() });
      if (conversationId) params.append('conversation_id', conversationId);
      return fetchAPI<ChatHistory>(`/chat/history/${userId}?${params.toString()}`);
    },

    /**
     * Delete conversation history (requires confirm=true)
     */
    deleteHistory: (userId: string, conversationId?: string, confirm = true) => {
      const params = new URLSearchParams({ confirm: confirm.toString() });
      if (conversationId) params.append('conversation_id', conversationId);
      return fetchAPI<{ deleted_count: number; message: string }>(
        `/chat/history/${userId}?${params.toString()}`,
        { method: 'DELETE' }
      );
    },

    /**
     * Submit feedback (rating) for a chat message
     */
    submitFeedback: (messageId: number, userId: string, rating: number, feedbackText?: string) =>
      fetchAPI<FeedbackResponse>('/chat/feedback', {
        method: 'POST',
        body: JSON.stringify({
          message_id: messageId,
          user_id: userId,
          rating,
          feedback_text: feedbackText,
        } as FeedbackRequest),
      }),
  },
};
