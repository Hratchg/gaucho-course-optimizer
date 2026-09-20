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

  const first = data[0]
  const last = data[data.length - 1]
  const label = `GPA trend from ${first.quarter} (${first.avg_gpa}) to ${last.quarter} (${last.avg_gpa})`

  return (
    <div role="img" aria-label={label}>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data}>
          <XAxis dataKey="quarter" tick={{ fontSize: 12, fontFamily: 'Inter Variable, sans-serif' }} />
          <YAxis domain={[0, 4.0]} tick={{ fontSize: 12, fontFamily: 'Inter Variable, sans-serif' }} />
          <Tooltip />
          <Line type="monotone" dataKey="avg_gpa" stroke="#2563EB" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
