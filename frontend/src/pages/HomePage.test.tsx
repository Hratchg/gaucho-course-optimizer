import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import HomePage from './HomePage'

function renderHomePage() {
  return render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>
  )
}

describe('HomePage', () => {
  describe('page metadata', () => {
    it('sets document.title to "Home | CoursePick"', () => {
      renderHomePage()
      expect(document.title).toBe('Home | CoursePick')
    })
  })

  describe('Hero', () => {
    it('renders the 2D library hero as the page h1 when 3D is unavailable', () => {
      renderHomePage()
      expect(
        screen.getByRole('heading', {
          level: 1,
          name: /every ucsb course/i,
        }),
      ).toBeInTheDocument()
      expect(screen.getByText(/welcome to the stacks/i)).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /search courses/i })).toHaveAttribute(
        'href',
        '/search',
      )
    })

    it('demotes the classic hero copy to h2', () => {
      renderHomePage()
      const heading = screen.getByRole('heading', {
        level: 2,
        name: /find the best professor for any ucsb course/i,
      })
      expect(heading).toBeInTheDocument()
    })

    it('renders hero subtext with exact UI-SPEC copy', () => {
      renderHomePage()
      expect(
        screen.getByText(
          /search any ucsb course and instantly see which professor will give you the best outcome/i
        )
      ).toBeInTheDocument()
    })
  })

  describe('Score Breakdown', () => {
    it('renders "How Gaucho Score Works" as h2', () => {
      renderHomePage()
      const heading = screen.getByRole('heading', {
        level: 2,
        name: /how gaucho score works/i,
      })
      expect(heading).toBeInTheDocument()
    })

    it('renders score bar container with role="img" and appropriate aria-label', () => {
      renderHomePage()
      const bar = screen.getByRole('img', {
        name: /gaucho score breakdown.*four equally weighted factors/i,
      })
      expect(bar).toBeInTheDocument()
    })

    it('renders 4 score bar segments with correct aria-labels', () => {
      renderHomePage()
      expect(screen.getByLabelText('GPA: 25%')).toBeInTheDocument()
      expect(screen.getByLabelText('Quality: 25%')).toBeInTheDocument()
      expect(screen.getByLabelText('Difficulty: 25%')).toBeInTheDocument()
      expect(screen.getByLabelText('Sentiment: 25%')).toBeInTheDocument()
    })
  })

  describe('Factor Cards', () => {
    it('renders "What Each Factor Means" as h2', () => {
      renderHomePage()
      const heading = screen.getByRole('heading', {
        level: 2,
        name: /what each factor means/i,
      })
      expect(heading).toBeInTheDocument()
    })

    it('renders all 4 factor card titles', () => {
      renderHomePage()
      expect(
        screen.getByRole('heading', { level: 3, name: 'GPA' })
      ).toBeInTheDocument()
      expect(
        screen.getByRole('heading', { level: 3, name: 'Quality' })
      ).toBeInTheDocument()
      expect(
        screen.getByRole('heading', { level: 3, name: 'Difficulty' })
      ).toBeInTheDocument()
      expect(
        screen.getByRole('heading', { level: 3, name: 'Sentiment' })
      ).toBeInTheDocument()
    })

    it('renders example values for each factor card', () => {
      renderHomePage()
      expect(screen.getByText(/3\.45 \/ 4\.00/)).toBeInTheDocument()
      expect(screen.getByText(/4\.2 \/ 5\.0/)).toBeInTheDocument()
      expect(screen.getByText(/2\.8 \/ 5\.0/)).toBeInTheDocument()
      expect(screen.getByText(/0\.65 compound/)).toBeInTheDocument()
    })
  })

  describe('Usage Guide', () => {
    it('renders "How to Use CoursePick" as h2', () => {
      renderHomePage()
      const heading = screen.getByRole('heading', {
        level: 2,
        name: /how to use coursepick/i,
      })
      expect(heading).toBeInTheDocument()
    })

    it('renders all 3 step titles', () => {
      renderHomePage()
      expect(screen.getByText('Search a Course')).toBeInTheDocument()
      expect(screen.getByText('Compare Professors')).toBeInTheDocument()
      expect(screen.getByText('Adjust Your Priorities')).toBeInTheDocument()
    })
  })

  describe('Final CTA', () => {
    it('renders "Ready to Find Your Professor?" as h2', () => {
      renderHomePage()
      const heading = screen.getByRole('heading', {
        level: 2,
        name: /ready to find your professor/i,
      })
      expect(heading).toBeInTheDocument()
    })

    it('renders "Start Searching" link pointing to /search', () => {
      renderHomePage()
      const link = screen.getByRole('link', { name: /start searching/i })
      expect(link).toBeInTheDocument()
      expect(link).toHaveAttribute('href', '/search')
    })
  })
})
