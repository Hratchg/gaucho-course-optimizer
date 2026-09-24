import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import BookCoursePage from './BookCoursePage'

function renderBook(courseId = '123') {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[{ pathname: `/courses/${courseId}`, state: { courseCode: 'MATH 4A' } }]}>
        <Routes>
          <Route path="/courses/:courseId" element={<BookCoursePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('BookCoursePage', () => {
  afterEach(() => {
    document.title = ''
  })

  it('sets the document title from navigation state', () => {
    renderBook()
    expect(document.title).toBe('MATH 4A | CoursePick')
  })

  it('offers a path back to the shelf and the classic list', () => {
    renderBook()
    expect(screen.getByRole('link', { name: /shelf/i })).toHaveAttribute('href', '/')
    expect(screen.getAllByRole('link', { name: /classic view/i })[0]).toHaveAttribute(
      'href',
      '/courses/123?classic=1',
    )
  })
})
