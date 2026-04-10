import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts'
import type { GradeQuarter } from '@/types/api'

const GRADE_KEYS = [
  'a_plus', 'a', 'a_minus', 'b_plus', 'b', 'b_minus',
  'c_plus', 'c', 'c_minus', 'd_plus', 'd', 'd_minus', 'f',
] as const

const GRADE_LABELS = [
  'A+', 'A', 'A-', 'B+', 'B', 'B-',
  'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F',
]

interface GradeChartProps {
  quarters: GradeQuarter[]
  selectedQuarter: string
}

function getFilteredQuarters(quarters: GradeQuarter[], selectedQuarter: string): GradeQuarter[] {
  if (selectedQuarter === 'all') {
    return quarters
  }
  if (selectedQuarter === 'most-recent') {
    return quarters.length > 0 ? [quarters[quarters.length - 1]] : []
  }
  const match = quarters.find(q => q.quarter === selectedQuarter)
  return match ? [match] : []
}

function getTitle(quarters: GradeQuarter[], selectedQuarter: string): string {
  if (selectedQuarter === 'all') {
    return 'Grade Distribution \u2014 All Quarters Combined'
  }
  if (selectedQuarter === 'most-recent') {
    const label = quarters.length > 0 ? quarters[quarters.length - 1].quarter : 'N/A'
    return `Grade Distribution \u2014 ${label}`
  }
  return `Grade Distribution \u2014 ${selectedQuarter}`
}

export function GradeChart({ quarters, selectedQuarter }: GradeChartProps) {
  const filtered = getFilteredQuarters(quarters, selectedQuarter)

  const data = GRADE_LABELS.map((label, i) => ({
    grade: label,
    count: filtered.reduce((sum, q) => sum + (q[GRADE_KEYS[i]] ?? 0), 0),
  }))

  const title = getTitle(quarters, selectedQuarter)

  return (
    <figure
      role="img"
      aria-label={`Bar chart showing grade distribution: ${title}`}
    >
      <h4 className="mb-2 text-sm font-semibold text-primary">{title}</h4>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
          <XAxis dataKey="grade" tick={{ fontSize: 12, fontFamily: 'Inter Variable, sans-serif' }} />
          <YAxis tick={{ fontSize: 12, fontFamily: 'Inter Variable, sans-serif' }} />
          <Tooltip />
          <Bar dataKey="count" fill="#2563EB" />
        </BarChart>
      </ResponsiveContainer>
    </figure>
  )
}
