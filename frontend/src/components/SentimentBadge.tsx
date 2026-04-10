import { Badge } from '@/components/ui/badge'

interface SentimentBadgeProps {
  score: number | null
}

export function SentimentBadge({ score }: SentimentBadgeProps) {
  if (score === null) return null

  let label: string
  let className: string

  if (score >= 0.2) {
    label = 'Positive'
    className = 'bg-green-100 text-green-800 hover:bg-green-100 rounded-full'
  } else if (score <= -0.2) {
    label = 'Negative'
    className = 'bg-red-100 text-red-800 hover:bg-red-100 rounded-full'
  } else {
    label = 'Neutral'
    className = 'bg-blue-100 text-blue-800 hover:bg-blue-100 rounded-full'
  }

  return <Badge variant="secondary" className={className}>{label}</Badge>
}
