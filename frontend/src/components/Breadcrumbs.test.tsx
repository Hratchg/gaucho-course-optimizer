import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import Breadcrumbs from './Breadcrumbs'

function renderAtPath(path: string, state?: Record<string, unknown>) {
  return render(
    <MemoryRouter initialEntries={[{ pathname: path, state }]}>
      <Breadcrumbs />
    </MemoryRouter>
  )
}

describe('Breadcrumbs', () => {
  it('renders nothing at "/" (Home page)', () => {
    renderAtPath('/')
    expect(screen.queryByRole('navigation', { name: /breadcrumb/i })).toBeNull()
  })

  it('renders "Home > Search" at "/search"', () => {
    renderAtPath('/search')
    const nav = screen.getByRole('navigation', { name: /breadcrumb/i })
    expect(nav).toBeInTheDocument()

    // "Home" should be a link
    const homeLink = screen.getByRole('link', { name: 'Home' })
    expect(homeLink).toHaveAttribute('href', '/')

    // "Search" should be present but NOT a link (active breadcrumb)
    expect(screen.getByText('Search')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Search' })).toBeNull()
  })

  it('renders "Home > Search > CMPSC 130A" at "/courses/42" with courseCode in state', () => {
    renderAtPath('/courses/42', { courseCode: 'CMPSC 130A' })
    const nav = screen.getByRole('navigation', { name: /breadcrumb/i })
    expect(nav).toBeInTheDocument()

    // "Home" is a link to /
    const homeLink = screen.getByRole('link', { name: 'Home' })
    expect(homeLink).toHaveAttribute('href', '/')

    // "Search" is a link to /search
    const searchLink = screen.getByRole('link', { name: 'Search' })
    expect(searchLink).toHaveAttribute('href', '/search')

    // "CMPSC 130A" is the active (last) breadcrumb, NOT a link
    expect(screen.getByText('CMPSC 130A')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'CMPSC 130A' })).toBeNull()
  })

  it('renders fallback "Course Results" at "/courses/42" without state', () => {
    renderAtPath('/courses/42')
    expect(screen.getByText('Course Results')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Course Results' })).toBeNull()
  })

  it('has aria-label="Breadcrumb" on nav element', () => {
    renderAtPath('/search')
    const nav = screen.getByRole('navigation', { name: /breadcrumb/i })
    expect(nav).toHaveAttribute('aria-label', 'Breadcrumb')
  })

  it('renders chevron separators with aria-hidden="true"', () => {
    renderAtPath('/courses/42', { courseCode: 'CMPSC 130A' })
    // There should be two separators for Home > Search > CMPSC 130A
    const separators = screen.getAllByRole('listitem', { hidden: true }).filter(
      (li) => li.getAttribute('aria-hidden') === 'true'
    )
    expect(separators.length).toBe(2)
  })

  it('applies text-primary font-semibold classes to active breadcrumb', () => {
    renderAtPath('/search')
    const activeCrumb = screen.getByText('Search')
    expect(activeCrumb.className).toContain('text-primary')
    expect(activeCrumb.className).toContain('font-semibold')
  })

  it('applies text-muted-foreground class to inactive breadcrumb links', () => {
    renderAtPath('/search')
    const homeLink = screen.getByRole('link', { name: 'Home' })
    expect(homeLink.className).toContain('text-muted-foreground')
  })
})
