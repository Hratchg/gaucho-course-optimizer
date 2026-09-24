import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import LibraryLanding from './LibraryLanding'

vi.mock('./LibraryScene', () => ({
  default: () => <div data-testid="library-scene-mock" />,
}))

vi.mock('./ClassicBookHud', () => ({
  default: ({ courseId, code, onClose }: { courseId: number; code?: string; onClose: () => void }) => (
    <div data-testid="classic-book-hud">
      classic {courseId} {code}
      <button type="button" onClick={onClose}>Close book</button>
    </div>
  ),
}))

function LocationProbe() {
  const location = useLocation()
  return <div data-testid="location">{location.pathname}</div>
}

function renderLanding(initialPath = '/') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route
            element={
              <>
                <LibraryLanding />
                <LocationProbe />
              </>
            }
          >
            <Route path="/" element={<></>} />
            <Route path="/courses/:courseId" element={<></>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('LibraryLanding overlay', () => {
  it('renders the search pill without mounting the WebGL scene', async () => {
    renderLanding()

    expect(screen.getByLabelText('Search courses')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/search a course/i)).toBeInTheDocument()
    expect(screen.getByText(/find the right professor/i)).toBeInTheDocument()
    const dock = screen.getByTestId('search-dock')
    expect(dock.className).toContain('absolute')
    expect(dock.className).toContain('bottom-6')
    expect(screen.getByRole('heading', { level: 1, name: /search ucsb courses/i })).toBeInTheDocument()
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

  it('opens the classic HUD after a course is picked and records the course URL', async () => {
    const user = userEvent.setup()
    renderLanding()

    await user.type(screen.getByLabelText('Search courses'), 'CS')
    await user.click(await screen.findByRole('button', { name: /cmpsc 8/i }))

    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
    expect(await screen.findByTestId('classic-book-hud', {}, { timeout: 3000 })).toHaveTextContent('classic 1')
    expect(screen.getByPlaceholderText(/search another course/i)).toBeInTheDocument()
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/courses/1'))
    expect(screen.queryByText(/find the right professor/i)).not.toBeInTheDocument()
  })

  it('opens the highlighted course when Enter is pressed', async () => {
    const user = userEvent.setup()
    renderLanding()

    await user.type(screen.getByLabelText('Search courses'), 'CS')
    await screen.findByRole('button', { name: /cmpsc 8/i })
    await user.keyboard('{Enter}')

    expect(await screen.findByTestId('classic-book-hud', {}, { timeout: 3000 })).toHaveTextContent('CMPSC 8')
  })

  it('puts the open book back before pulling the next search', async () => {
    const user = userEvent.setup()
    renderLanding()

    await user.type(screen.getByLabelText('Search courses'), 'CS')
    await user.keyboard('{Enter}')
    await screen.findByTestId('classic-book-hud', {}, { timeout: 3000 })

    await user.type(screen.getByLabelText('Search courses'), 'CS')
    await user.click(await screen.findByRole('button', { name: /cmpsc 8/i }))

    expect(screen.queryByTestId('classic-book-hud')).not.toBeInTheDocument()
    expect(await screen.findByTestId('classic-book-hud', {}, { timeout: 4500 })).toHaveTextContent('CMPSC 8')
  })

  it('closes the book and returns to the shelf', async () => {
    const user = userEvent.setup()
    renderLanding()

    await user.type(screen.getByLabelText('Search courses'), 'CS')
    await user.keyboard('{Enter}')
    await screen.findByTestId('classic-book-hud', {}, { timeout: 3000 })

    await user.click(screen.getByRole('button', { name: /close book/i }))

    expect(await screen.findByPlaceholderText(/search a course/i)).toBeInTheDocument()
    expect(screen.queryByTestId('classic-book-hud')).not.toBeInTheDocument()
    expect(screen.getByTestId('location')).toHaveTextContent('/')
  })
})
