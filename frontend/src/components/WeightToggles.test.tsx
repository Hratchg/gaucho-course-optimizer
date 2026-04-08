import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { WeightToggles } from './WeightToggles'
import type { ToggleWeights } from '@/lib/scoring'

const allOn: ToggleWeights = { gpa: true, quality: true, difficulty: true, sentiment: true }

describe('WeightToggles', () => {
  it('renders heading "Customize Ranking"', () => {
    render(<WeightToggles weights={allOn} onWeightsChange={vi.fn()} />)
    expect(screen.getByText('Customize Ranking')).toBeInTheDocument()
  })

  it('renders all 4 toggle labels', () => {
    render(<WeightToggles weights={allOn} onWeightsChange={vi.fn()} />)
    expect(screen.getByText('Easy Grades')).toBeInTheDocument()
    expect(screen.getByText('Great Teaching')).toBeInTheDocument()
    expect(screen.getByText('Low Difficulty')).toBeInTheDocument()
    expect(screen.getByText('Good Reviews')).toBeInTheDocument()
  })

  it('all checkboxes are checked when all weights are true', () => {
    render(<WeightToggles weights={allOn} onWeightsChange={vi.fn()} />)
    const checkboxes = screen.getAllByRole('checkbox')
    expect(checkboxes).toHaveLength(4)
    checkboxes.forEach((cb) => {
      expect(cb).toHaveAttribute('data-state', 'checked')
    })
  })

  it('clicking a checkbox calls onWeightsChange with that key toggled to false', () => {
    const onChange = vi.fn()
    render(<WeightToggles weights={allOn} onWeightsChange={onChange} />)
    // Click the "Easy Grades" checkbox (gpa)
    fireEvent.click(screen.getByRole('checkbox', { name: 'Easy Grades' }))
    expect(onChange).toHaveBeenCalledWith({
      gpa: false,
      quality: true,
      difficulty: true,
      sentiment: true,
    })
  })

  it('shows weight distribution "Each factor: 25%" when all 4 enabled', () => {
    render(<WeightToggles weights={allOn} onWeightsChange={vi.fn()} />)
    expect(screen.getByText('Each factor: 25%')).toBeInTheDocument()
  })

  it('shows weight distribution "Each factor: 50%" when 2 enabled', () => {
    const twoOn: ToggleWeights = { gpa: true, quality: true, difficulty: false, sentiment: false }
    render(<WeightToggles weights={twoOn} onWeightsChange={vi.fn()} />)
    expect(screen.getByText('Each factor: 50%')).toBeInTheDocument()
  })

  it('does NOT call onWeightsChange when trying to uncheck the last enabled toggle', () => {
    const oneOn: ToggleWeights = { gpa: true, quality: false, difficulty: false, sentiment: false }
    const onChange = vi.fn()
    render(<WeightToggles weights={oneOn} onWeightsChange={onChange} />)
    // Try to uncheck the only enabled checkbox
    fireEvent.click(screen.getByRole('checkbox', { name: 'Easy Grades' }))
    expect(onChange).not.toHaveBeenCalled()
  })

  it('unchecked labels have muted styling', () => {
    const partial: ToggleWeights = { gpa: true, quality: false, difficulty: true, sentiment: false }
    render(<WeightToggles weights={partial} onWeightsChange={vi.fn()} />)
    const mutedLabel = screen.getByText('Great Teaching')
    expect(mutedLabel).toHaveClass('text-muted-foreground')
    const activeLabel = screen.getByText('Easy Grades')
    expect(activeLabel).not.toHaveClass('text-muted-foreground')
  })
})
