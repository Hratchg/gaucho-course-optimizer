import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/mswServer'
import CourseSearch from './CourseSearch'

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('CourseSearch', () => {
  it('renders the search input with placeholder', () => {
    renderWithProviders(<CourseSearch />)
    expect(screen.getByPlaceholderText(/search courses/i)).toBeInTheDocument()
  })

  it('shows course results after typing 2+ characters', async () => {
    const user = userEvent.setup()
    renderWithProviders(<CourseSearch />)
    const input = screen.getByPlaceholderText(/search courses/i)
    await user.type(input, 'CS')
    // MSW default handler returns CMPSC 8
    expect(await screen.findByText('CMPSC 8')).toBeInTheDocument()
  })

  it('shows empty state when no results', async () => {
    // CRITICAL: Override MSW handler to return empty array for this test.
    server.use(
      http.get('http://localhost:8001/courses/search', () => {
        return HttpResponse.json([])
      })
    )
    const user = userEvent.setup()
    renderWithProviders(<CourseSearch />)
    const input = screen.getByPlaceholderText(/search courses/i)
    await user.type(input, 'ZZZZZZ')
    expect(await screen.findByText(/no courses found/i)).toBeInTheDocument()
  })

  it('hides the Courses heading when there are no results', async () => {
    server.use(
      http.get('http://localhost:8001/courses/search', () => {
        return HttpResponse.json([])
      })
    )
    const user = userEvent.setup()
    renderWithProviders(<CourseSearch />)
    await user.type(screen.getByPlaceholderText(/search courses/i), 'ZZZZZZ')
    await screen.findByText(/no courses found/i)
    expect(screen.queryByText('Courses')).not.toBeInTheDocument()
  })

  // UX-1: during an API outage the old code fell through to CommandEmpty and
  // told students the course didn't exist.
  it('shows a server-error state, not "no courses found", when the API fails', async () => {
    server.use(
      http.get('http://localhost:8001/courses/search', () => {
        return new HttpResponse(null, { status: 500 })
      })
    )
    const user = userEvent.setup()
    renderWithProviders(<CourseSearch />)
    await user.type(screen.getByPlaceholderText(/search courses/i), 'CS 16')

    expect(await screen.findByText(/search is unavailable/i)).toBeInTheDocument()
    expect(screen.queryByText(/no courses found/i)).not.toBeInTheDocument()
  })

  it('offers a retry action when the API fails', async () => {
    let calls = 0
    server.use(
      http.get('http://localhost:8001/courses/search', () => {
        calls += 1
        return new HttpResponse(null, { status: 500 })
      })
    )
    const user = userEvent.setup()
    renderWithProviders(<CourseSearch />)
    await user.type(screen.getByPlaceholderText(/search courses/i), 'CS 16')

    const retry = await screen.findByRole('button', { name: /try again/i })
    const before = calls
    await user.click(retry)
    await vi.waitFor(() => expect(calls).toBeGreaterThan(before))
  })
})
