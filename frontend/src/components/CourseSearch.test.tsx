import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
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
})
