import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import MobileMenu from './MobileMenu'

function renderMobileMenu(initialPath = '/') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <MobileMenu />
    </MemoryRouter>
  )
}

describe('MobileMenu', () => {
  it('renders hamburger button with aria-label "Open navigation menu"', () => {
    renderMobileMenu()
    const button = screen.getByRole('button', { name: /open navigation menu/i })
    expect(button).toBeInTheDocument()
  })

  it('hamburger button has 44px minimum touch target', () => {
    renderMobileMenu()
    const button = screen.getByRole('button', { name: /open navigation menu/i })
    expect(button.className).toContain('min-h-[44px]')
    expect(button.className).toContain('min-w-[44px]')
  })

  it('clicking hamburger opens Sheet with title "CoursePick"', async () => {
    const user = userEvent.setup()
    renderMobileMenu()

    const button = screen.getByRole('button', { name: /open navigation menu/i })
    await user.click(button)

    await waitFor(() => {
      expect(screen.getByText('CoursePick')).toBeInTheDocument()
    })
  })

  it('Sheet contains Home and Methodology links, not Search', async () => {
    const user = userEvent.setup()
    renderMobileMenu()

    await user.click(screen.getByRole('button', { name: /open navigation menu/i }))

    await waitFor(() => {
      expect(screen.getByRole('link', { name: 'Home' })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: 'Methodology' })).toBeInTheDocument()
      expect(screen.queryByRole('link', { name: 'Search' })).not.toBeInTheDocument()
    })
  })

  it('clicking a link in the Sheet closes it', async () => {
    const user = userEvent.setup()
    renderMobileMenu()

    await user.click(screen.getByRole('button', { name: /open navigation menu/i }))

    await waitFor(() => {
      expect(screen.getByRole('link', { name: 'Home' })).toBeInTheDocument()
    })

    // Click the Home link inside the Sheet
    await user.click(screen.getByRole('link', { name: 'Home' }))

    // Sheet content should disappear after clicking a link
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })
})
