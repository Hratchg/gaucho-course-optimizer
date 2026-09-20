import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import type { GradeQuarter } from '@/types/api'
import { GpaTrendChart } from './GpaTrendChart'

class ResizeObserverMock implements ResizeObserver { observe() {} unobserve() {} disconnect() {} }
globalThis.ResizeObserver = ResizeObserverMock

const mockQuarters: GradeQuarter[] = [
  {
    quarter: 'F22',
    avg_gpa: 3.2,
    a_plus: 5, a: 20, a_minus: 10,
    b_plus: 8, b: 15, b_minus: 6,
    c_plus: 3, c: 4, c_minus: 2,
    d_plus: 1, d: 1, d_minus: 0,
    f: 1,
  },
  {
    quarter: 'W23',
    avg_gpa: 3.4,
    a_plus: 8, a: 25, a_minus: 12,
    b_plus: 6, b: 10, b_minus: 4,
    c_plus: 2, c: 2, c_minus: 1,
    d_plus: 0, d: 0, d_minus: 0,
    f: 0,
  },
]

const nullGpaQuarters: GradeQuarter[] = [
  {
    quarter: 'F22',
    avg_gpa: null,
    a_plus: 5, a: 20, a_minus: 10,
    b_plus: 8, b: 15, b_minus: 6,
    c_plus: 3, c: 4, c_minus: 2,
    d_plus: 1, d: 1, d_minus: 0,
    f: 1,
  },
]

describe('GpaTrendChart', () => {
  it('renders without crashing', () => {
    const { container } = render(<GpaTrendChart quarters={mockQuarters} />)
    expect(container).toBeInTheDocument()
  })

  it('shows empty message when all quarters have null GPA', () => {
    render(<GpaTrendChart quarters={nullGpaQuarters} />)
    expect(screen.getByText('No GPA trend data available')).toBeInTheDocument()
  })
})
