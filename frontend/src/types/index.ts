export interface User {
  user_id: string;
  name: string;
  age?: number;
  income_level?: string;
  consent_status: boolean;
  consent_timestamp?: string;
  created_at: string;
}

export interface Signal {
  signal_id: string;
  signal_type: string;
  value: number;
  details?: any;
  computed_at: string;
}

export interface Persona {
  persona_id: number;
  user_id: string;
  window_days: number;
  persona_type: string;
  priority_rank: number;
  criteria_met: string;
  assigned_at: string;
}

export interface Recommendation {
  recommendation_id: number;
  user_id: string;
  persona_type: string;
  content_type: string;
  title: string;
  description?: string;
  rationale: string;
  eligibility_met: boolean;
  approval_status: 'pending' | 'approved' | 'rejected' | 'review';
  operator_notes?: string;
  created_at: string;
}

export interface AuditLog {
  log_id: number;
  user_id?: string;
  action: string;
  actor: string;
  details?: string;
  timestamp: string;
}

export interface UserProfile {
  user_id: string;
  name: string;
  age?: number;
  income_level?: string;
  consent_status: boolean;
  consent_timestamp?: string;
  created_at: string;
  signals: Signal[];
  personas: Persona[];
  recommendations: Recommendation[];
}

export interface GuardrailSummary {
  message: string;
  guardrails: {
    user_eligibility_rules: {
      minimum_age: number;
      requires_consent: boolean;
      minimum_transactions: number;
      minimum_signals: number;
    };
    content_safety_rules: {
      allowed_risk_levels: string[];
      prohibited_patterns: string[];
      required_disclaimers: boolean;
    };
    tone_guardrails: {
      prohibited_tone_patterns_count: number;
      requires_empowering_language: boolean;
      examples_prohibited: string[];
      examples_encouraged: string[];
    };
    rate_limits: {
      max_per_week: number;
      max_per_day: number;
    };
    vulnerable_population_protections: {
      [key: string]: string;
    };
  };
}

export interface ToneCheckResult {
  valid: boolean;
  violations: Array<{
    pattern: string;
    category: string;
    matches: string[];
  }>;
  suggestions: string[];
}

export interface FeedbackSubmission {
  recommendation_id: number;
  user_id: string;
  rating: number;
  feedback_type: 'helpful' | 'not_helpful' | 'irrelevant';
  comment?: string;
}
