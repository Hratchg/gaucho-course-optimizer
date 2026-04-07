import { render } from '@testing-library/react'
import { describe, it, expect, afterEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import CoursePage from './CoursePage'

function renderWithProviders(courseId: string = '123') {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/courses/${courseId}`]}>
        <Routes>
          <Route path="/courses/:courseId" element={<CoursePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('CoursePage', () => {
  afterEach(() => {
    document.title = ''
  })

  it('sets document.title to "Course Results | Gaucho Course Optimizer"', () => {
    renderWithProviders('123')
    expect(document.title).toBe('Course Results | Gaucho Course Optimizer')
  })
})
