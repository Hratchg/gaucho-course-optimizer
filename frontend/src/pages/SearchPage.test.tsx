import { render } from '@testing-library/react'
import { describe, it, expect, afterEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import SearchPage from './SearchPage'

function renderWithProviders(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('SearchPage', () => {
  afterEach(() => {
    document.title = ''
  })

  it('sets document.title to "Search | Gaucho Course Optimizer"', () => {
    renderWithProviders(<SearchPage />)
    expect(document.title).toBe('Search | Gaucho Course Optimizer')
  })
})
