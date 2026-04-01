import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { SentimentBadge } from './SentimentBadge'

describe('SentimentBadge', () => {
  it('renders Positive badge for score >= 0.2', () => {
    render(<SentimentBadge score={0.5} />)
    expect(screen.getByText('Positive')).toBeInTheDocument()
  })

  it('renders Negative badge for score <= -0.2', () => {
    render(<SentimentBadge score={-0.5} />)
    expect(screen.getByText('Negative')).toBeInTheDocument()
  })

  it('renders Neutral badge for score between -0.2 and 0.2', () => {
    render(<SentimentBadge score={0.1} />)
    expect(screen.getByText('Neutral')).toBeInTheDocument()
  })

  it('renders Positive badge at exact threshold 0.2', () => {
    render(<SentimentBadge score={0.2} />)
    expect(screen.getByText('Positive')).toBeInTheDocument()
  })

  it('renders Negative badge at exact threshold -0.2', () => {
    render(<SentimentBadge score={-0.2} />)
    expect(screen.getByText('Negative')).toBeInTheDocument()
  })

  it('renders nothing when score is null', () => {
    const { container } = render(<SentimentBadge score={null} />)
    expect(container).toBeEmptyDOMElement()
  })
})
