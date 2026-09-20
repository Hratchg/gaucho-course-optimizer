import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import type { GradeQuarter } from '@/types/api'
import { GradeChart } from './GradeChart'

class ResizeObserverMock implements ResizeObserver { observe() {} unobserve() {} disconnect() {} }
globalThis.ResizeObserver = ResizeObserverMock

const multiQuarters: GradeQuarter[] = [
  {
    quarter: 'Fall 2023', avg_gpa: 3.0,
    a_plus: 2, a: 10, a_minus: 5, b_plus: 4, b: 8, b_minus: 3,
    c_plus: 2, c: 3, c_minus: 1, d_plus: 0, d: 1, d_minus: 0, f: 1,
  },
  {
    quarter: 'Winter 2024', avg_gpa: 3.4,
    a_plus: 5, a: 15, a_minus: 8, b_plus: 6, b: 10, b_minus: 4,
    c_plus: 1, c: 2, c_minus: 1, d_plus: 0, d: 0, d_minus: 0, f: 0,
  },
]

const singleQuarter: GradeQuarter[] = [
  {
    quarter: 'Spring 2024', avg_gpa: 3.1,
    a_plus: 3, a: 12, a_minus: 6, b_plus: 5, b: 9, b_minus: 4,
    c_plus: 2, c: 3, c_minus: 1, d_plus: 1, d: 0, d_minus: 0, f: 0,
  },
]

describe('GradeChart', () => {
  it('renders without crashing with selectedQuarter="all"', () => {
    const { container } = render(
      <GradeChart quarters={multiQuarters} selectedQuarter="all" />
    )
    expect(container).toBeInTheDocument()
  })

  it('displays "All Quarters Combined" in the title when selectedQuarter is "all"', () => {
    render(<GradeChart quarters={multiQuarters} selectedQuarter="all" />)
    expect(screen.getByText(/All Quarters Combined/)).toBeInTheDocument()
  })

  it('displays the most recent quarter label in the title when selectedQuarter is "most-recent"', () => {
    render(<GradeChart quarters={multiQuarters} selectedQuarter="most-recent" />)
    expect(screen.getByText(/Winter 2024/)).toBeInTheDocument()
  })

  it('displays the specific quarter label in the title when a specific quarter is selected', () => {
    render(<GradeChart quarters={multiQuarters} selectedQuarter="Fall 2023" />)
    expect(screen.getByText(/Fall 2023/)).toBeInTheDocument()
  })

  it('renders with a single quarter without crashing', () => {
    const { container } = render(
      <GradeChart quarters={singleQuarter} selectedQuarter="most-recent" />
    )
    expect(container).toBeInTheDocument()
    expect(screen.getByText(/Spring 2024/)).toBeInTheDocument()
  })
})
