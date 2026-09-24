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

  it('renders Home and Methodology links, not Search', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Navbar />
      </MemoryRouter>
    )
    expect(screen.getByRole('link', { name: /home/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /methodology/i })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /^search$/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /day mode|night mode/i })).not.toBeInTheDocument()
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

  it('at "/methodology", Methodology link has aria-current="page"', () => {
    render(
      <MemoryRouter initialEntries={['/methodology']}>
        <Navbar />
      </MemoryRouter>
    )
    const methodologyLink = screen.getByRole('link', { name: /methodology/i })
    expect(methodologyLink).toHaveAttribute('aria-current', 'page')
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
