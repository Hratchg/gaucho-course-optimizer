import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { WeightSliders } from './WeightSliders'
import type { Weights } from '@/lib/scoring'

const defaultWeights: Weights = { gpa: 4, quality: 3, difficulty: 2, sentiment: 1 }

describe('WeightSliders', () => {
  it('renders all four slider labels', () => {
    render(<WeightSliders weights={defaultWeights} onWeightsChange={vi.fn()} />)
    expect(screen.getByText('GPA Weight')).toBeInTheDocument()
    expect(screen.getByText('Quality Weight')).toBeInTheDocument()
    expect(screen.getByText('Difficulty Weight')).toBeInTheDocument()
    expect(screen.getByText('Sentiment Weight')).toBeInTheDocument()
  })

  it('displays normalized weight values', () => {
    render(<WeightSliders weights={defaultWeights} onWeightsChange={vi.fn()} />)
    // 4/(4+3+2+1) = 0.40
    expect(screen.getByText('0.40')).toBeInTheDocument()
    // 3/10 = 0.30
    expect(screen.getByText('0.30')).toBeInTheDocument()
  })

  it('displays equal weights when all zeros', () => {
    const zeroWeights: Weights = { gpa: 0, quality: 0, difficulty: 0, sentiment: 0 }
    render(<WeightSliders weights={zeroWeights} onWeightsChange={vi.fn()} />)
    // All should show 0.25
    const elements = screen.getAllByText('0.25')
    expect(elements.length).toBe(4)
  })

  it('renders heading "Score Weights"', () => {
    render(<WeightSliders weights={defaultWeights} onWeightsChange={vi.fn()} />)
    expect(screen.getByText('Score Weights')).toBeInTheDocument()
  })
})
