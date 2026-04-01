import { Slider } from '@/components/ui/slider'
import { normalizeWeights } from '@/lib/scoring'
import type { Weights } from '@/lib/scoring'

interface WeightSlidersProps {
  weights: Weights
  onWeightsChange: (weights: Weights) => void
}

const SLIDER_CONFIG = [
  { key: 'gpa' as const, label: 'GPA Weight' },
  { key: 'quality' as const, label: 'Quality Weight' },
  { key: 'difficulty' as const, label: 'Difficulty Weight' },
  { key: 'sentiment' as const, label: 'Sentiment Weight' },
]

export function WeightSliders({ weights, onWeightsChange }: WeightSlidersProps) {
  const normalized = normalizeWeights(weights)

  return (
    <div className="space-y-5">
      <h2 className="text-lg font-semibold">Score Weights</h2>
      {SLIDER_CONFIG.map(({ key, label }) => (
        <div key={key}>
          <div className="mb-2 flex items-center justify-between">
            <label className="text-sm">{label}</label>
            <span className="text-sm text-muted-foreground">
              {normalized[key].toFixed(2)}
            </span>
          </div>
          <Slider
            aria-label={label}
            value={[weights[key]]}
            onValueChange={([value]) =>
              onWeightsChange({ ...weights, [key]: value })
            }
            min={0}
            max={10}
            step={1}
            className="w-full"
          />
        </div>
      ))}
    </div>
  )
}
