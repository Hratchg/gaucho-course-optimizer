import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ProfessorCard } from '../ProfessorCard'
import type { ProfessorRanking } from '@/types/api'

function makeProfessor(overrides: Partial<ProfessorRanking> = {}): ProfessorRanking {
  return {
    id: 1,
    name: 'Test Professor',
    department: 'CMPSC',
    gaucho_score: 75,
    gpa_factor: 0.8,
    quality_factor: 0.7,
    difficulty_factor: 0.6,
    sentiment_factor: 0.65,
    rmp_quality: 4.0,
    rmp_difficulty: 2.5,
    rmp_would_take_again: 80,
    rmp_num_ratings: 50,
    mean_gpa: 3.5,
    std_gpa: 0.4,
    avg_sentiment: 0.5,
    match_confidence: 0.9,
    quarters_taught: 5,
    keywords: [],
    is_active_teacher: false,
    recent_quarters: [],
    ...overrides,
  }
}

function renderCard(professor: ProfessorRanking, score = 75) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <ProfessorCard professor={professor} score={score} courseId={1} />
    </QueryClientProvider>
  )
}

describe('ProfessorCard - Active Teaching', () => {
  it('renders Actively Teaching badge when is_active_teacher is true', () => {
    renderCard(makeProfessor({ is_active_teacher: true }))
    expect(screen.getByText('Actively Teaching')).toBeInTheDocument()
  })

  it('does not render Actively Teaching badge when is_active_teacher is false', () => {
    renderCard(makeProfessor({ is_active_teacher: false }))
    expect(screen.queryByText('Actively Teaching')).toBeNull()
  })

  it('renders Quarters Taught trigger with count when recent_quarters has items', () => {
    renderCard(makeProfessor({ recent_quarters: ['Fall 2024', 'Winter 2024', 'Spring 2024'] }))
    expect(screen.getByText(/Quarters Taught \(3\)/)).toBeInTheDocument()
  })

  it('does not render Quarters Taught when recent_quarters is empty', () => {
    renderCard(makeProfessor({ recent_quarters: [] }))
    expect(screen.queryByText(/Quarters Taught/)).toBeNull()
  })

  it('expands to show quarter badges when trigger is clicked', async () => {
    const user = userEvent.setup()
    renderCard(makeProfessor({ recent_quarters: ['Fall 2024', 'Winter 2024'] }))
    await user.click(screen.getByText(/Quarters Taught/))
    expect(screen.getByText('Fall 2024')).toBeInTheDocument()
    expect(screen.getByText('Winter 2024')).toBeInTheDocument()
  })
})
