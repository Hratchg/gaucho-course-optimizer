import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts'
import type { GradeQuarter } from '@/types/api'

interface GpaTrendChartProps {
  quarters: GradeQuarter[]
}

export function GpaTrendChart({ quarters }: GpaTrendChartProps) {
  const data = quarters
    .filter((q) => q.avg_gpa != null)
    .map((q) => ({ quarter: q.quarter, avg_gpa: q.avg_gpa }))

  if (data.length === 0) return <p className="text-sm text-muted-foreground">No GPA trend data available</p>

  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={data}>
        <XAxis dataKey="quarter" tick={{ fontSize: 12 }} />
        <YAxis domain={[0, 4.0]} tick={{ fontSize: 12 }} />
        <Tooltip />
        <Line type="monotone" dataKey="avg_gpa" stroke="#10b981" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}
