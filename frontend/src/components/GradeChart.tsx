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
}

export function GradeChart({ quarters }: GradeChartProps) {
  const data = GRADE_LABELS.map((label, i) => ({
    grade: label,
    count: quarters.reduce((sum, q) => sum + (q[GRADE_KEYS[i]] ?? 0), 0),
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
        <XAxis dataKey="grade" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip />
        <Bar dataKey="count" fill="#6366f1" />
      </BarChart>
    </ResponsiveContainer>
  )
}
