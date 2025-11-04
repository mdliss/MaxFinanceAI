import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import RecommendationCard from '../RecommendationCard'
import type { Recommendation } from '@/types'

describe('RecommendationCard', () => {
  const mockRecommendation: Recommendation = {
    recommendation_id: 1,
    user_id: 'user_123',
    persona_type: 'income_stable',
    content_type: 'article',
    title: 'Test Recommendation',
    description: 'Test description',
    rationale: 'Test rationale',
    disclaimer: 'Test disclaimer',
    eligibility_met: true,
    approval_status: 'pending',
    operator_notes: null,
    created_at: '2025-11-04T00:00:00',
  }

  const mockOnApprove = vi.fn()
  const mockOnOverride = vi.fn()
  const mockOnFlag = vi.fn()

  it('renders recommendation details correctly', () => {
    render(
      <RecommendationCard
        recommendation={mockRecommendation}
        onApprove={mockOnApprove}
        onOverride={mockOnOverride}
        onFlag={mockOnFlag}
      />
    )

    expect(screen.getByText('Test Recommendation')).toBeInTheDocument()
    expect(screen.getByText('Test description')).toBeInTheDocument()
  })

  it('displays approval status badge', () => {
    render(
      <RecommendationCard
        recommendation={mockRecommendation}
        onApprove={mockOnApprove}
        onOverride={mockOnOverride}
        onFlag={mockOnFlag}
      />
    )

    expect(screen.getByText(/pending/i)).toBeInTheDocument()
  })

  it('shows persona type', () => {
    render(
      <RecommendationCard
        recommendation={mockRecommendation}
        onApprove={mockOnApprove}
        onOverride={mockOnOverride}
        onFlag={mockOnFlag}
      />
    )

    expect(screen.getByText(/income_stable/i)).toBeInTheDocument()
  })
})
