import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import HomePage from './HomePage'

function renderHomePage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('HomePage', () => {
  it('sets document.title to "Home | CoursePick"', () => {
    renderHomePage()
    expect(document.title).toBe('Home | CoursePick')
  })

  it('renders a single h1 and a home search field when 3D is unavailable', () => {
    renderHomePage()
    expect(screen.getByRole('heading', { level: 1, name: /search ucsb courses/i })).toBeInTheDocument()
    expect(screen.getByLabelText('Search courses')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /search courses/i })).not.toBeInTheDocument()
  })
})
