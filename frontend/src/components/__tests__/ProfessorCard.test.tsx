import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ProfessorCard } from '../ProfessorCard'
import type { ProfessorRanking } from '@/types/api'
import type { GradeQuarter } from '@/types/api'

class ResizeObserverMock { observe() {} unobserve() {} disconnect() {} }
globalThis.ResizeObserver = ResizeObserverMock as any

vi.mock('@/hooks/useProfessorGrades', () => ({
  useProfessorGrades: vi.fn(),
}))

vi.mock('@/hooks/useProfessorComments', () => ({
  useProfessorComments: vi.fn(() => ({ data: [], isLoading: false })),
}))

import { useProfessorGrades } from '@/hooks/useProfessorGrades'

const multiQuarters: GradeQuarter[] = [
  {
    quarter: 'Fall 2023', avg_gpa: 3.0,
    a_plus: 2, a: 10, a_minus: 5, b_plus: 4, b: 8, b_minus: 3,
    c_plus: 2, c: 3, c_minus: 1, d_plus: 0, d: 1, d_minus: 0, f: 1,
  },
  {
    quarter: 'Winter 2024', avg_gpa: 3.4,
    a_plus: 5, a: 15, a_minus: 8, b_plus: 6, b: 10, b_minus: 4,
    c_plus: 1, c: 2, c_minus: 1, d_plus: 0, d: 0, d_minus: 0, f: 0,
  },
]

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
    tags: [],
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
  beforeEach(() => {
    (useProfessorGrades as ReturnType<typeof vi.fn>).mockReturnValue({ data: undefined, isLoading: false })
  })

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

describe('ProfessorCard - Quarter Selector', () => {
  beforeEach(() => {
    (useProfessorGrades as ReturnType<typeof vi.fn>).mockReturnValue({ data: multiQuarters, isLoading: false })
  })

  it('shows quarter Select dropdown when expanded with grade data', async () => {
    const user = userEvent.setup()
    renderCard(makeProfessor())
    await user.click(screen.getByText(/Show details/))
    expect(screen.getByText('Most Recent')).toBeInTheDocument()
  })

  it('defaults to Most Recent selection', async () => {
    const user = userEvent.setup()
    renderCard(makeProfessor())
    await user.click(screen.getByText(/Show details/))
    expect(screen.getByText('Most Recent')).toBeInTheDocument()
  })
})
