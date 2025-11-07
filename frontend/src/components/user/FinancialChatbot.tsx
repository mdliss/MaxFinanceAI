'use client'

import { useEffect, useState, useRef } from 'react';
import { api } from '@/lib/api';
import type { UserProfile } from '@/types';

interface FinancialChatbotProps {
  userId: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  messageId?: number; // Backend message ID for feedback
  rating?: number; // User's rating (1-5)
}

export default function FinancialChatbot({ userId }: FinancialChatbotProps) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await api.getUserProfile(userId);
        setProfile(data);

        // Add personalized welcome message
        const approvedRecs = data.recommendations?.filter(r => r.approval_status === 'approved') || [];
        const welcomeMessage: Message = {
          id: 'welcome',
          role: 'assistant',
          content: `Hi ${data.name}! I'm your personal financial advisor. I've reviewed your account and ${approvedRecs.length > 0 ? `I have ${approvedRecs.length} personalized recommendation${approvedRecs.length > 1 ? 's' : ''} for you. Ask me about them, or anything else related to your finances!` : `I'm analyzing your spending patterns. Ask me anything about budgeting, saving, or managing your money!`}`,
          timestamp: new Date(),
        };
        setMessages([welcomeMessage]);
        setUnreadCount(1);
      } catch (err) {
        console.error('Failed to load profile:', err);
      }
    };

    fetchProfile();
  }, [userId]);

  useEffect(() => {
    if (isOpen) {
      setUnreadCount(0);
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setLoading(true);
    setError(null);

    // Add placeholder assistant message for streaming
    const assistantMessageId = (Date.now() + 1).toString();
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, assistantMessage]);

    try {
      let accumulatedContent = '';
      let finalMessageId: number | undefined;
      let finalConversationId: string | undefined;

      // Stream the response
      for await (const event of api.chat.streamMessage(userId, currentInput, conversationId)) {
        if (event.type === 'start') {
          // Store conversation ID
          if (!conversationId) {
            setConversationId(event.conversationId);
          }
          finalConversationId = event.conversationId;
        } else if (event.type === 'chunk') {
          // Accumulate content and update message in real-time
          accumulatedContent += event.content;
          setMessages(prev =>
            prev.map(msg =>
              msg.id === assistantMessageId
                ? { ...msg, content: accumulatedContent }
                : msg
            )
          );
        } else if (event.type === 'done') {
          // Finalize message with backend message_id
          finalMessageId = event.messageId;
          setMessages(prev =>
            prev.map(msg =>
              msg.id === assistantMessageId
                ? { ...msg, messageId: finalMessageId }
                : msg
            )
          );

          if (process.env.NODE_ENV === 'development') {
            console.log(`Streaming complete: ${accumulatedContent.length} chars, message_id: ${finalMessageId}`);
          }
        }
      }

      setLoading(false);
      if (!isOpen) {
        setUnreadCount(c => c + 1);
      }
    } catch (err: any) {
      console.error('Failed to send message:', err);
      setError(err.message || 'Failed to get response. Please try again.');

      // Replace streaming message with error
      setMessages(prev =>
        prev.map(msg =>
          msg.id === assistantMessageId
            ? { ...msg, content: "I'm having trouble processing your request. Please try again in a moment." }
            : msg
        )
      );
      setLoading(false);
    }
  };

  const handleFeedback = async (messageId: number, rating: number) => {
    try {
      await api.chat.submitFeedback(messageId, userId, rating);

      // Update message with rating
      setMessages(prev =>
        prev.map(msg =>
          msg.messageId === messageId ? { ...msg, rating } : msg
        )
      );
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickQuestions = profile?.recommendations?.filter(r => r.approval_status === 'approved').length ? [
    "Show my recommendations",
    "Help with my credit",
    "Create a budget for me",
    "What's my financial status?",
  ] : [
    "How can I save more?",
    "Help with budgeting",
    "Credit card tips",
    "Build emergency fund",
  ];

  return (
    <>
      {/* Floating Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 w-16 h-16 bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] rounded-full shadow-2xl hover:scale-110 transition-all duration-300 flex items-center justify-center z-50 group"
        >
          <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          {unreadCount > 0 && (
            <div className="absolute -top-1 -right-1 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-xs font-bold text-white animate-pulse">
              {unreadCount}
            </div>
          )}
          <div className="absolute -top-12 right-0 bg-[var(--bg-secondary)] border border-[var(--border-color)] px-3 py-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap text-sm">
            Chat with your advisor
          </div>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-[420px] h-[600px] bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden transition-all duration-300">
          {/* Header */}
          <div className="p-4 bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-white">Financial Advisor</h3>
                <p className="text-xs text-white/80">Personalized for {profile?.name}</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="w-8 h-8 rounded-full hover:bg-white/20 transition-smooth flex items-center justify-center text-white text-xl"
            >
              &times;
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[var(--bg-primary)]">
            {messages.map((message, index) => (
              <div key={message.id}>
                <div
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] text-white'
                        : 'bg-[var(--bg-secondary)] border border-[var(--border-color)]'
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-line">{message.content}</p>
                    <div className="flex items-center justify-between mt-2">
                      <p className={`text-xs ${
                        message.role === 'user' ? 'text-white/70' : 'text-[var(--text-secondary)]'
                      }`}>
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                      {/* Feedback buttons for assistant messages */}
                      {message.role === 'assistant' && message.messageId && !message.rating && (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleFeedback(message.messageId!, 5)}
                            className="text-xs px-2 py-1 hover:bg-green-500/20 rounded transition-colors"
                            title="Helpful"
                          >
                            Helpful
                          </button>
                          <button
                            onClick={() => handleFeedback(message.messageId!, 1)}
                            className="text-xs px-2 py-1 hover:bg-red-500/20 rounded transition-colors"
                            title="Not helpful"
                          >
                            Not helpful
                          </button>
                        </div>
                      )}
                      {/* Show feedback status */}
                      {message.rating && message.rating >= 4 && (
                        <span className="text-xs text-green-600">Rated helpful</span>
                      )}
                      {message.rating && message.rating <= 2 && (
                        <span className="text-xs text-gray-500">Feedback sent</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Quick Action Buttons - show after assistant messages */}
                {message.role === 'assistant' && message.content && index === messages.length - 1 && !loading && (
                  <div className="flex gap-2 mt-2 ml-2 flex-wrap">
                    <button
                      onClick={() => setInput("Show my credit card details")}
                      className="text-xs px-3 py-1.5 bg-[var(--bg-tertiary)] hover:bg-[var(--accent-primary)] hover:text-white border border-[var(--border-color)] rounded-full transition-all duration-200"
                    >
                      Credit Info
                    </button>
                    <button
                      onClick={() => setInput("Help me create a budget")}
                      className="text-xs px-3 py-1.5 bg-[var(--bg-tertiary)] hover:bg-[var(--accent-primary)] hover:text-white border border-[var(--border-color)] rounded-full transition-all duration-200"
                    >
                      Budget Help
                    </button>
                    <button
                      onClick={() => setInput("What are my subscriptions?")}
                      className="text-xs px-3 py-1.5 bg-[var(--bg-tertiary)] hover:bg-[var(--accent-primary)] hover:text-white border border-[var(--border-color)] rounded-full transition-all duration-200"
                    >
                      Subscriptions
                    </button>
                    <button
                      onClick={() => setInput("Show my savings goals")}
                      className="text-xs px-3 py-1.5 bg-[var(--bg-tertiary)] hover:bg-[var(--accent-primary)] hover:text-white border border-[var(--border-color)] rounded-full transition-all duration-200"
                    >
                      Savings
                    </button>
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-2xl px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-[var(--text-secondary)]">Thinking</span>
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-[var(--accent-primary)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-[var(--accent-primary)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-[var(--accent-primary)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Questions */}
          {messages.length === 1 && (
            <div className="px-4 py-3 border-t border-[var(--border-color)] bg-[var(--bg-secondary)]">
              <p className="text-xs text-[var(--text-secondary)] mb-2">Quick questions:</p>
              <div className="grid grid-cols-2 gap-2">
                {quickQuestions.map((question, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInput(question)}
                    className="text-xs text-left px-3 py-2 bg-[var(--bg-tertiary)] hover:bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg transition-smooth"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="p-4 border-t border-[var(--border-color)] bg-[var(--bg-secondary)]">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about your finances..."
                className="flex-1 px-4 py-2 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-lg focus:outline-none focus:border-[var(--accent-primary)] transition-smooth text-sm"
                disabled={loading}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || loading}
                className="px-4 py-2 bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition-smooth"
              >
                →
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
