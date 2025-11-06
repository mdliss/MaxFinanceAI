/**
 * Chat-related TypeScript types for the frontend
 */

export interface ChatMessage {
  message_id: number;
  user_id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  tokens_used?: number;
  response_time_ms?: number;
  model_used?: string;
  created_at: string;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: number;
  response: string;
  tokens_used: number;
  response_time_ms: number;
  model: string;
  timestamp: string;
}

export interface ChatRequest {
  user_id: string;
  message: string;
  conversation_id?: string;
}

export interface Conversation {
  conversation_id: string;
  started_at: string;
  last_message_at: string;
  message_count: number;
  messages: ChatMessage[];
}

export interface ChatHistory {
  user_id: string;
  conversations: Conversation[];
  total_conversations: number;
}

export interface FeedbackRequest {
  message_id: number;
  user_id: string;
  rating: number; // 1-5
  feedback_text?: string;
}

export interface FeedbackResponse {
  feedback_id: number;
  message: string;
  rating: number;
}

// Local UI message type (simplified for component state)
export interface UIMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  messageId?: number; // Backend message ID for feedback
}
