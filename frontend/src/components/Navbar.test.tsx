import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Navbar from './Navbar'

describe('Navbar', () => {
  it('renders brand text "CoursePick"', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Navbar />
      </MemoryRouter>
    )
    // Wordmark renders as Course + Pick spans; match on the link's accessible name
    expect(screen.getByRole('link', { name: /coursepick/i })).toBeInTheDocument()
  })

  it('renders both "Home" and "Search" link text', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Navbar />
      </MemoryRouter>
    )
    expect(screen.getByRole('link', { name: /home/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /search/i })).toBeInTheDocument()
  })

  it('at "/", Home link has aria-current="page"', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Navbar />
      </MemoryRouter>
    )
    const homeLink = screen.getByRole('link', { name: /home/i })
    expect(homeLink).toHaveAttribute('aria-current', 'page')
  })

  it('at "/search", Search link has aria-current="page"', () => {
    render(
      <MemoryRouter initialEntries={['/search']}>
        <Navbar />
      </MemoryRouter>
    )
    const searchLink = screen.getByRole('link', { name: /search/i })
    expect(searchLink).toHaveAttribute('aria-current', 'page')
  })

  it('brand text links to home page', () => {
    render(
      <MemoryRouter initialEntries={['/search']}>
        <Navbar />
      </MemoryRouter>
    )
    const brandLink = screen.getByRole('link', { name: /coursepick/i })
    expect(brandLink).toHaveAttribute('href', '/')
  })
})
