import { render } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { SkeletonCard } from './SkeletonCard'

describe('SkeletonCard', () => {
  it('renders skeleton elements', () => {
    const { container } = render(<SkeletonCard />)
    const skeletons = container.querySelectorAll('[data-slot="skeleton"]')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('renders inside a Card with border-l-4', () => {
    const { container } = render(<SkeletonCard />)
    const card = container.querySelector('[data-slot="card"]')
    expect(card).toBeInTheDocument()
    expect(card?.className).toContain('border-l-4')
  })
})
