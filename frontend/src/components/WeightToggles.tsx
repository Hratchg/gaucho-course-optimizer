import { useState, useCallback } from 'react'
import { Checkbox } from '@/components/ui/checkbox'
import type { ToggleWeights } from '@/lib/scoring'

interface WeightTogglesProps {
  weights: ToggleWeights
  onWeightsChange: (weights: ToggleWeights) => void
}

const TOGGLE_CONFIG = [
  { key: 'gpa' as const, label: 'Easy Grades' },
  { key: 'quality' as const, label: 'Great Teaching' },
  { key: 'difficulty' as const, label: 'Low Difficulty' },
  { key: 'sentiment' as const, label: 'Good Reviews' },
]

export function WeightToggles({ weights, onWeightsChange }: WeightTogglesProps) {
  const [shakeKey, setShakeKey] = useState<string | null>(null)

  const enabledCount = TOGGLE_CONFIG.filter(({ key }) => weights[key]).length

  const handleToggle = useCallback(
    (key: keyof ToggleWeights) => {
      // Prevent unchecking the last enabled toggle
      if (weights[key] && enabledCount === 1) {
        setShakeKey(key)
        setTimeout(() => setShakeKey(null), 400)
        return
      }
      onWeightsChange({ ...weights, [key]: !weights[key] })
    },
    [weights, enabledCount, onWeightsChange]
  )

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Customize Ranking</h2>
      <div className="space-y-3">
        {TOGGLE_CONFIG.map(({ key, label }) => (
          <div
            key={key}
            className={`flex items-center gap-3${shakeKey === key ? ' animate-shake' : ''}`}
          >
            <Checkbox
              id={key}
              checked={weights[key]}
              onCheckedChange={() => handleToggle(key)}
            />
            <label
              htmlFor={key}
              className={`text-sm cursor-pointer select-none${
                weights[key] ? '' : ' text-muted-foreground'
              }`}
            >
              {label}
            </label>
          </div>
        ))}
      </div>
      <p className="text-xs text-muted-foreground">
        Each factor: {Math.round(100 / enabledCount)}%
      </p>
    </div>
  )
}
