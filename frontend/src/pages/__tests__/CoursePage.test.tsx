import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/mswServer'
import CoursePage from '../CoursePage'

function renderCoursePage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/course/1']}>
        <Routes>
          <Route path="/course/:courseId" element={<CoursePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

function makeProfessorData(overrides: Record<string, unknown> = {}) {
  return {
    id: 101,
    name: 'Alice Smith',
    department: 'CMPSC',
    gaucho_score: 82,
    gpa_factor: 0.85,
    quality_factor: 0.80,
    difficulty_factor: 0.65,
    sentiment_factor: 0.75,
    has_rmp: true,
    rmp_quality: 4.1,
    rmp_difficulty: 3.2,
    rmp_would_take_again: 0.78,
    rmp_num_ratings: 120,
    mean_gpa: 3.4,
    std_gpa: 0.45,
    avg_sentiment: 0.6,
    match_confidence: 0.95,
    quarters_taught: 8,
    tags: [
      { name: 'Clear Explanations', count: 12 },
      { name: 'Helpful', count: 8 },
    ],
    is_active_teacher: true,
    recent_quarters: ['Fall 2024', 'Winter 2024', 'Spring 2024'],
    ...overrides,
  }
}

describe('CoursePage - Active Teacher Filter', () => {
  it('filter checkbox defaults to unchecked', async () => {
    renderCoursePage()
    await waitFor(() => expect(screen.getByText('Alice Smith')).toBeInTheDocument())
    const checkbox = screen.getByRole('checkbox', { name: /taught recently only/i })
    expect(checkbox).toHaveAttribute('data-state', 'unchecked')
  })

  it('checking filter hides inactive professor', async () => {
    server.use(
      http.get('http://localhost:8001/courses/:id/professors', () => {
        return HttpResponse.json([
          makeProfessorData({ id: 101, name: 'Alice Smith', is_active_teacher: true }),
          makeProfessorData({ id: 102, name: 'Bob Jones', is_active_teacher: false, gaucho_score: 71, gpa_factor: 0.72, quality_factor: 0.68, difficulty_factor: 0.55, sentiment_factor: 0.60 }),
        ])
      })
    )
    const user = userEvent.setup()
    renderCoursePage()
    await waitFor(() => {
      expect(screen.getByText('Alice Smith')).toBeInTheDocument()
      expect(screen.getByText('Bob Jones')).toBeInTheDocument()
    })
    await user.click(screen.getByRole('checkbox', { name: /taught recently only/i }))
    expect(screen.queryByText('Bob Jones')).toBeNull()
    expect(screen.getByText('Alice Smith')).toBeInTheDocument()
  })

  it('shows all professors with note when filter on but none active', async () => {
    server.use(
      http.get('http://localhost:8001/courses/:id/professors', () => {
        return HttpResponse.json([
          makeProfessorData({ id: 101, name: 'Alice Smith', is_active_teacher: false }),
          makeProfessorData({ id: 102, name: 'Bob Jones', is_active_teacher: false, gaucho_score: 71, gpa_factor: 0.72, quality_factor: 0.68, difficulty_factor: 0.55, sentiment_factor: 0.60 }),
        ])
      })
    )
    const user = userEvent.setup()
    renderCoursePage()
    await waitFor(() => {
      expect(screen.getByText('Alice Smith')).toBeInTheDocument()
      expect(screen.getByText('Bob Jones')).toBeInTheDocument()
    })
    await user.click(screen.getByRole('checkbox', { name: /taught recently only/i }))
    expect(screen.getByText('Alice Smith')).toBeInTheDocument()
    expect(screen.getByText('Bob Jones')).toBeInTheDocument()
    expect(screen.getByText(/no professors have taught this course recently/i)).toBeInTheDocument()
  })

  it('starts on next quarter and shows the meeting time', async () => {
    const user = userEvent.setup()
    renderCoursePage()
    expect(await screen.findByText('Alice Smith')).toBeInTheDocument()
    expect(screen.queryByText('Bob Jones')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Spring 2026', pressed: true })).toBeInTheDocument()
    expect(screen.getByText(/MWF 10:00 AM–10:50 AM, Phelps 1260, 42 of 120/)).toBeInTheDocument()
    expect(screen.getAllByText('Spring 2026').length).toBeGreaterThan(1)

    await user.click(screen.getByRole('button', { name: 'All' }))
    expect(screen.getByText('Bob Jones')).toBeInTheDocument()
  })

  it('shows a server-fault message and retry when the API fails', async () => {
    let calls = 0
    server.use(
      http.get('http://localhost:8001/courses/:id/professors', () => {
        calls += 1
        return new HttpResponse(null, { status: 500 })
      })
    )
    const user = userEvent.setup()
    renderCoursePage()
    expect(await screen.findByText(/we could not load professors/i)).toBeInTheDocument()
    expect(screen.queryByText(/check your connection/i)).not.toBeInTheDocument()
    const before = calls
    await user.click(screen.getByRole('button', { name: /try again/i }))
    await waitFor(() => expect(calls).toBeGreaterThan(before))
  })
})
