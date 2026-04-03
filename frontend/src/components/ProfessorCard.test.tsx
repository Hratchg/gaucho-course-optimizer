import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ProfessorRanking } from '@/types/api'
import { ProfessorCard } from './ProfessorCard'

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
}

function renderWithClient(ui: React.ReactElement) {
  const client = makeQueryClient()
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>
  )
}

const mockProfessor: ProfessorRanking = {
  id: 1, name: 'Dr. Test Professor', department: 'CMPSC',
  gaucho_score: 75, gpa_factor: 0.8, quality_factor: 0.7,
  difficulty_factor: 0.6, sentiment_factor: 0.5,
  rmp_quality: 4.2, rmp_difficulty: 3.1, rmp_would_take_again: 85,
  rmp_num_ratings: 50, mean_gpa: 3.45, std_gpa: 0.3,
  avg_sentiment: 0.4, match_confidence: 0.95,
  quarters_taught: 8, keywords: ['engaging', 'fair grader', 'helpful'],
}

describe('ProfessorCard', () => {
  it('displays the professor name', () => {
    renderWithClient(<ProfessorCard professor={mockProfessor} score={75} courseId={1} />)
    expect(screen.getByText('Dr. Test Professor')).toBeInTheDocument()
  })

  it('displays the computed score', () => {
    renderWithClient(<ProfessorCard professor={mockProfessor} score={75} courseId={1} />)
    expect(screen.getByText('75')).toBeInTheDocument()
  })

  it('displays RMP quality rating', () => {
    renderWithClient(<ProfessorCard professor={mockProfessor} score={75} courseId={1} />)
    expect(screen.getByText(/Quality:.*4\.2/)).toBeInTheDocument()
  })

  it('displays keyword tags', () => {
    renderWithClient(<ProfessorCard professor={mockProfessor} score={75} courseId={1} />)
    expect(screen.getByText('engaging')).toBeInTheDocument()
    expect(screen.getByText('fair grader')).toBeInTheDocument()
    expect(screen.getByText('helpful')).toBeInTheDocument()
  })

  it('displays avg GPA', () => {
    renderWithClient(<ProfessorCard professor={mockProfessor} score={75} courseId={1} />)
    expect(screen.getByText(/Avg GPA:.*3\.45/)).toBeInTheDocument()
  })

  it('displays score in a badge with green color for score >= 70', () => {
    renderWithClient(<ProfessorCard professor={mockProfessor} score={75} courseId={1} />)
    const badge = screen.getByText('75')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toContain('bg-green-500')
  })

  it('displays score in a badge with yellow color for score 50-69', () => {
    renderWithClient(<ProfessorCard professor={mockProfessor} score={55} courseId={1} />)
    const badge = screen.getByText('55')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toContain('bg-yellow-500')
  })

  it('displays score in a badge with red color for score < 50', () => {
    renderWithClient(<ProfessorCard professor={mockProfessor} score={35} courseId={1} />)
    const badge = screen.getByText('35')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toContain('bg-red-500')
  })

  it('toggles "Show details" / "Hide details" on click', async () => {
    const user = userEvent.setup()
    renderWithClient(<ProfessorCard professor={mockProfessor} score={75} courseId={1} />)

    const trigger = screen.getByText(/Show details/i)
    expect(trigger).toBeInTheDocument()

    await user.click(trigger)
    expect(screen.getByText(/Hide details/i)).toBeInTheDocument()

    await user.click(screen.getByText(/Hide details/i))
    expect(screen.getByText(/Show details/i)).toBeInTheDocument()
  })
})
