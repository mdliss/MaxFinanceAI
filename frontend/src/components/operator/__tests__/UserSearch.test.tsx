import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import UserSearch from '../UserSearch'

describe('UserSearch', () => {
  const mockOnSearch = vi.fn()

  it('renders search input', () => {
    render(<UserSearch onSearch={mockOnSearch} />)

    const searchInput = screen.getByPlaceholderText(/search by name or user id/i)
    expect(searchInput).toBeInTheDocument()
  })

  it('calls onSearch when typing in search box', () => {
    render(<UserSearch onSearch={mockOnSearch} />)

    const searchInput = screen.getByPlaceholderText(/search by name or user id/i)
    fireEvent.change(searchInput, { target: { value: 'Charlotte' } })

    expect(mockOnSearch).toHaveBeenCalled()
  })

  it('displays search label', () => {
    render(<UserSearch onSearch={mockOnSearch} />)

    expect(screen.getByText(/search users/i)).toBeInTheDocument()
  })
})
