export interface Weights {
  gpa: number
  quality: number
  difficulty: number
  sentiment: number
}

export interface ToggleWeights {
  gpa: boolean
  quality: boolean
  difficulty: boolean
  sentiment: boolean
}

export const DEFAULT_WEIGHTS: Weights = { gpa: 4, quality: 3, difficulty: 2, sentiment: 1 }

export const DEFAULT_TOGGLE_WEIGHTS: ToggleWeights = {
  gpa: true,
  quality: true,
  difficulty: true,
  sentiment: true,
}

export function normalizeWeights(weights: Weights): Weights {
  const total = weights.gpa + weights.quality + weights.difficulty + weights.sentiment
  if (total === 0) return { gpa: 0.25, quality: 0.25, difficulty: 0.25, sentiment: 0.25 }
  return {
    gpa: weights.gpa / total,
    quality: weights.quality / total,
    difficulty: weights.difficulty / total,
    sentiment: weights.sentiment / total,
  }
}

export function normalizeToggles(toggles: ToggleWeights): Weights {
  const enabledCount = [toggles.gpa, toggles.quality, toggles.difficulty, toggles.sentiment]
    .filter(Boolean).length
  const share = enabledCount > 0 ? 1 / enabledCount : 0.25
  return {
    gpa: toggles.gpa ? share : 0,
    quality: toggles.quality ? share : 0,
    difficulty: toggles.difficulty ? share : 0,
    sentiment: toggles.sentiment ? share : 0,
  }
}

export function computeGauchoScore(
  gpaFactor: number | null,
  qualityFactor: number | null,
  difficultyFactor: number | null,
  sentimentFactor: number | null,
  weights: Weights | ToggleWeights
): number {
  const w = typeof weights.gpa === 'boolean'
    ? normalizeToggles(weights as ToggleWeights)
    : normalizeWeights(weights as Weights)
  const values = {
    gpa: gpaFactor,
    quality: qualityFactor,
    difficulty: difficultyFactor,
    sentiment: sentimentFactor,
  } as const
  const usable = (Object.keys(values) as Array<keyof typeof values>).filter(
    (key) => values[key] != null && w[key] > 0
  )
  if (usable.length === 0) return 0
  const weightSum = usable.reduce((sum, key) => sum + w[key], 0)
  if (weightSum === 0) return 0
  const raw = usable.reduce((sum, key) => sum + (values[key] as number) * (w[key] / weightSum), 0)
  return Math.round(Math.max(0, Math.min(100, raw * 100)))
}
