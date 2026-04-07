import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import HomePage from './HomePage'

describe('HomePage', () => {
  it('renders hero heading text', () => {
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )
    expect(
      screen.getByRole('heading', {
        name: /find the best professor for any ucsb course/i,
      })
    ).toBeInTheDocument()
  })

  it('renders "Start Searching" link pointing to /search', () => {
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )
    const link = screen.getByRole('link', { name: /start searching/i })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', '/search')
  })

  it('sets document.title to "Home | Gaucho Course Optimizer"', () => {
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )
    expect(document.title).toBe('Home | Gaucho Course Optimizer')
  })
})
