import { render } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import type { GradeQuarter } from '@/types/api'
import { GradeChart } from './GradeChart'

class ResizeObserverMock { observe() {} unobserve() {} disconnect() {} }
globalThis.ResizeObserver = ResizeObserverMock as any

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
]

describe('GradeChart', () => {
  it('renders without crashing', () => {
    const { container } = render(<GradeChart quarters={mockQuarters} />)
    expect(container).toBeInTheDocument()
  })

  it('renders a chart container element', () => {
    const { container } = render(<GradeChart quarters={mockQuarters} />)
    expect(container.querySelector('.recharts-wrapper, div')).not.toBeNull()
  })
})
