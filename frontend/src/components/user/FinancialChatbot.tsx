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
}

export default function FinancialChatbot({ userId }: FinancialChatbotProps) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
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
          content: `Hi ${data.name}! 👋 I'm your personal financial advisor. I've reviewed your account and ${approvedRecs.length > 0 ? `I have ${approvedRecs.length} personalized recommendation${approvedRecs.length > 1 ? 's' : ''} for you. Ask me about them, or anything else related to your finances!` : `I'm analyzing your spending patterns. Ask me anything about budgeting, saving, or managing your money!`}`,
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

  const generatePersonalizedAdvice = (userMessage: string): string => {
    const lowerMessage = userMessage.toLowerCase();

    if (!profile) {
      return "I'm still loading your financial data. Please try again in a moment.";
    }

    // Extract financial data
    const approvedRecs = profile.recommendations?.filter(r => r.approval_status === 'approved') || [];
    const creditUtilSignal = profile.signals?.find(s => s.signal_type === 'credit_utilization');
    const incomeSignal = profile.signals?.find(s => s.signal_type === 'income_stability');
    const spendingSignal = profile.signals?.find(s => s.signal_type === 'spending_surge');
    const subscriptionSignal = profile.signals?.find(s => s.signal_type === 'subscription_detected');

    const creditBalance = creditUtilSignal?.details?.current_balance || 0;
    const creditLimit = creditUtilSignal?.details?.credit_limit || 0;
    const utilization = creditUtilSignal?.details?.utilization_percent || 0;
    const avgIncome = incomeSignal?.details?.average_income || 0;

    // Ask about recommendations
    if (lowerMessage.includes('recommend') || lowerMessage.includes('advice') || lowerMessage.includes('tips') || lowerMessage.includes('suggestions')) {
      if (approvedRecs.length === 0) {
        return "I'm still analyzing your spending patterns to generate personalized recommendations. In the meantime, I can help with general budgeting, saving strategies, or answer questions about your current finances!";
      }

      let response = `I have ${approvedRecs.length} personalized recommendation${approvedRecs.length > 1 ? 's' : ''} for you:\n\n`;
      approvedRecs.forEach((rec, idx) => {
        response += `${idx + 1}. **${rec.title}** (${rec.persona_type})\n   ${rec.description}\n\n`;
      });
      response += `You can view full details in the "Your Recommendations" section above, or ask me about any specific recommendation!`;
      return response;
    }

    // Ask about specific recommendation
    approvedRecs.forEach(rec => {
      if (lowerMessage.includes(rec.title.toLowerCase()) ||
          lowerMessage.includes(rec.persona_type.toLowerCase())) {
        return `**${rec.title}**\n\n${rec.description}\n\n**Why this matters:** ${rec.rationale}\n\nWould you like specific steps on how to implement this?`;
      }
    });

    // Credit questions - use their actual data
    if (lowerMessage.includes('credit') || lowerMessage.includes('debt') || lowerMessage.includes('balance')) {
      if (creditUtilSignal) {
        if (utilization > 30) {
          const targetBalance = creditLimit * 0.3;
          const amountToPayDown = creditBalance - targetBalance;
          return `Looking at your account, your credit utilization is **${utilization.toFixed(1)}%** (${creditBalance.toLocaleString('en-US', {style: 'currency', currency: 'USD'})} / ${creditLimit.toLocaleString('en-US', {style: 'currency', currency: 'USD'})}).\n\nThis is above the recommended 30% threshold. I suggest paying down **${amountToPayDown.toLocaleString('en-US', {style: 'currency', currency: 'USD'})}** to get below 30%. This will improve your credit score.\n\n💡 Tip: Pay before the statement closing date to report a lower balance.`;
        } else {
          return `Great news! Your credit utilization is **${utilization.toFixed(1)}%**, which is healthy (under 30%). Your current balance is ${creditBalance.toLocaleString('en-US', {style: 'currency', currency: 'USD'})} with a ${creditLimit.toLocaleString('en-US', {style: 'currency', currency: 'USD'})} limit.\n\nKeep up the good work! Try to pay your balance in full each month to avoid interest charges.`;
        }
      }
      return "I don't see credit card data in your profile yet. Once you link your accounts, I can give you personalized credit management advice!";
    }

    // Income questions - use their actual data
    if (lowerMessage.includes('income') || lowerMessage.includes('salary') || lowerMessage.includes('earn')) {
      if (incomeSignal) {
        const monthlyIncome = avgIncome;
        const needsBudget = monthlyIncome * 0.5;
        const wantsBudget = monthlyIncome * 0.3;
        const savingsBudget = monthlyIncome * 0.2;

        return `Based on your income data, your average monthly income is **${monthlyIncome.toLocaleString('en-US', {style: 'currency', currency: 'USD'})}**. Your status is "${incomeSignal.details.status}".\n\nI recommend the 50/30/20 budget:\n• **Needs (50%)**: ${needsBudget.toLocaleString('en-US', {style: 'currency', currency: 'USD'})} - rent, utilities, groceries\n• **Wants (30%)**: ${wantsBudget.toLocaleString('en-US', {style: 'currency', currency: 'USD'})} - entertainment, dining out\n• **Savings (20%)**: ${savingsBudget.toLocaleString('en-US', {style: 'currency', currency: 'USD'})} - emergency fund, investments`;
      }
      return "I need your income data to provide personalized budgeting advice. Once you link your accounts, I can create a custom budget for you!";
    }

    // Spending questions - use their actual spending signals
    if (lowerMessage.includes('spending') || lowerMessage.includes('spend') || lowerMessage.includes('expense')) {
      if (spendingSignal) {
        const category = spendingSignal.details?.category || 'general';
        const amount = spendingSignal.details?.total_spent || 0;
        const avgSpend = spendingSignal.details?.average_spending || 0;
        const percentIncrease = ((amount - avgSpend) / avgSpend * 100).toFixed(0);

        return `I detected a **spending surge** in your **${category}** category:\n\n• Recent spending: ${amount.toLocaleString('en-US', {style: 'currency', currency: 'USD'})}\n• Your average: ${avgSpend.toLocaleString('en-US', {style: 'currency', currency: 'USD'})}\n• Increase: **${percentIncrease}%**\n\n💡 Suggestion: Review your ${category} purchases and see if there are any one-time expenses or areas to cut back. The 24-hour rule can help: wait a day before purchases over $50.`;
      }
      return "I'm analyzing your spending patterns. Ask me about specific categories like dining, shopping, or subscriptions!";
    }

    // Subscription questions - use their actual subscriptions
    if (lowerMessage.includes('subscription') || lowerMessage.includes('recurring')) {
      if (subscriptionSignal) {
        const merchant = subscriptionSignal.details?.merchant_name || 'subscription service';
        const amount = subscriptionSignal.details?.monthly_amount || 0;
        const annualCost = amount * 12;

        return `I found a recurring subscription to **${merchant}** for ${amount.toLocaleString('en-US', {style: 'currency', currency: 'USD'})}/month (${annualCost.toLocaleString('en-US', {style: 'currency', currency: 'USD'})}/year).\n\n❓ Ask yourself:\n• Do I use this enough to justify the cost?\n• Are there cheaper alternatives?\n• Can I downgrade to a lower tier?\n\nCanceling unused subscriptions is one of the easiest ways to save money!`;
      }
      return "I haven't detected any subscription charges yet. Once you have recurring payments, I'll help you manage them!";
    }

    // Budget/saving questions
    if (lowerMessage.includes('budget') || lowerMessage.includes('save') || lowerMessage.includes('saving')) {
      if (avgIncome > 0) {
        const monthlySavingsGoal = avgIncome * 0.2;
        const annualSavings = monthlySavingsGoal * 12;
        return `Based on your ${avgIncome.toLocaleString('en-US', {style: 'currency', currency: 'USD'})} monthly income, aim to save **${monthlySavingsGoal.toLocaleString('en-US', {style: 'currency', currency: 'USD'})} per month** (20% of income).\n\nThat's **${annualSavings.toLocaleString('en-US', {style: 'currency', currency: 'USD'})} per year**!\n\n✅ Action steps:\n1. Set up automatic transfer to savings on payday\n2. Start with emergency fund (3-6 months expenses)\n3. Use high-yield savings account (5%+ APY)`;
      }
      return "I can help you create a personalized budget once I have your income information. In general, follow the 50/30/20 rule: 50% needs, 30% wants, 20% savings.";
    }

    // Emergency fund
    if (lowerMessage.includes('emergency')) {
      if (avgIncome > 0) {
        const threeMonths = avgIncome * 3;
        const sixMonths = avgIncome * 6;
        return `Based on your income, your emergency fund should be:\n\n• **Minimum**: ${threeMonths.toLocaleString('en-US', {style: 'currency', currency: 'USD'})} (3 months)\n• **Ideal**: ${sixMonths.toLocaleString('en-US', {style: 'currency', currency: 'USD'})} (6 months)\n\nStart with a mini goal of $1,000, then build from there. Keep it in a high-yield savings account for easy access!`;
      }
      return "An emergency fund should cover 3-6 months of expenses. Start with $500-$1,000 for minor emergencies, then build up gradually!";
    }

    // Summary/overview
    if (lowerMessage.includes('summary') || lowerMessage.includes('overview') || lowerMessage.includes('status')) {
      let summary = `**Your Financial Snapshot**\n\n`;

      if (creditUtilSignal) {
        summary += `💳 **Credit**: ${utilization.toFixed(1)}% utilization (${utilization > 30 ? '⚠️ Above 30%' : '✅ Healthy'})\n`;
      }

      if (incomeSignal) {
        summary += `💰 **Income**: ${avgIncome.toLocaleString('en-US', {style: 'currency', currency: 'USD'})}/mo (${incomeSignal.details.status})\n`;
      }

      if (approvedRecs.length > 0) {
        summary += `📊 **Recommendations**: ${approvedRecs.length} personalized tip${approvedRecs.length > 1 ? 's' : ''}\n`;
      }

      summary += `\nWhat would you like to work on?`;
      return summary;
    }

    // How to implement recommendations
    if (lowerMessage.includes('how') || lowerMessage.includes('implement') || lowerMessage.includes('steps')) {
      return "I can help you implement any of your recommendations! Which one would you like to tackle first? Just tell me the topic (e.g., 'credit card debt', 'budgeting', 'subscriptions').";
    }

    // Default response with context
    return `I'm here to help with your personal finances! I can answer questions about:\n\n• Your ${approvedRecs.length} personalized recommendation${approvedRecs.length !== 1 ? 's' : ''}\n• Credit management (current: ${utilization.toFixed(1)}% utilization)\n• Budgeting with your ${avgIncome.toLocaleString('en-US', {style: 'currency', currency: 'USD'})} income\n• Spending patterns and subscriptions\n• Saving and emergency funds\n\nWhat would you like to know?`;
  };

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    setTimeout(() => {
      const advice = generatePersonalizedAdvice(input);
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: advice,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      setLoading(false);
      if (!isOpen) {
        setUnreadCount(c => c + 1);
      }
    }, 800);
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
          <span className="text-2xl">💬</span>
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
                <span className="text-xl">💬</span>
              </div>
              <div>
                <h3 className="font-semibold text-white">Financial Advisor</h3>
                <p className="text-xs text-white/80">Personalized for {profile?.name}</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="w-8 h-8 rounded-full hover:bg-white/20 transition-smooth flex items-center justify-center text-white"
            >
              ✕
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[var(--bg-primary)]">
            {messages.map((message) => (
              <div
                key={message.id}
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
                  <p className={`text-xs mt-2 ${
                    message.role === 'user' ? 'text-white/70' : 'text-[var(--text-secondary)]'
                  }`}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-2xl px-4 py-3">
                  <div className="flex gap-2">
                    <div className="w-2 h-2 bg-[var(--accent-primary)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-[var(--accent-primary)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-[var(--accent-primary)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
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
