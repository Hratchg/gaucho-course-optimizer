import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import LibraryLanding from './LibraryLanding'

vi.mock('./LibraryScene', () => ({
  default: () => <div data-testid="library-scene-mock" />,
}))

function renderLanding() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <LibraryLanding />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('LibraryLanding overlay', () => {
  it('renders the search input without mounting the WebGL scene', async () => {
    renderLanding()

    expect(screen.getByLabelText('Search courses')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/find a course/i)).toBeInTheDocument()
    // Search card is docked top-right (absolute, right-anchored on sm+).
    const dock = screen.getByTestId('search-dock')
    expect(dock.className).toContain('absolute')
    expect(dock.className).toContain('sm:right-6')
    expect(dock.className).toContain('sm:top-6')
    expect(screen.getByRole('heading', { level: 1, name: /every ucsb course/i })).toBeInTheDocument()
    // Lazy scene resolves to the mock — never a WebGL canvas.
    expect(await screen.findByTestId('library-scene-mock')).toBeInTheDocument()
    expect(document.querySelector('canvas')).toBeNull()
  })

  it('shows course results after typing 2+ characters', async () => {
    const user = userEvent.setup()
    renderLanding()

    await user.type(screen.getByLabelText('Search courses'), 'CS')

    expect(await screen.findByRole('listbox', { name: /course results/i })).toBeInTheDocument()
    expect(await screen.findByText('CMPSC 8')).toBeInTheDocument()
    expect(screen.getByText('Intro to CS')).toBeInTheDocument()
  })

  it('shows the Open the book card after a result is picked', async () => {
    const user = userEvent.setup()
    renderLanding()

    await user.type(screen.getByLabelText('Search courses'), 'CS')
    await user.click(await screen.findByRole('button', { name: /cmpsc 8/i }))

    expect(screen.getByRole('button', { name: /open the book/i })).toBeInTheDocument()
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })
})
