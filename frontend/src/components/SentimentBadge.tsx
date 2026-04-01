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
    className = 'bg-green-100 text-green-800 hover:bg-green-100'
  } else if (score <= -0.2) {
    label = 'Negative'
    className = 'bg-red-100 text-red-800 hover:bg-red-100'
  } else {
    label = 'Neutral'
    className = 'bg-orange-100 text-orange-800 hover:bg-orange-100'
  }

  return <Badge variant="secondary" className={className}>{label}</Badge>
}
