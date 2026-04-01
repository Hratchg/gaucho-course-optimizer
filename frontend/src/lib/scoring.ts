export interface Weights {
  gpa: number
  quality: number
  difficulty: number
  sentiment: number
}

export const DEFAULT_WEIGHTS: Weights = { gpa: 4, quality: 3, difficulty: 2, sentiment: 1 }

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

export function computeGauchoScore(
  gpaFactor: number,
  qualityFactor: number,
  difficultyFactor: number,
  sentimentFactor: number,
  weights: Weights
): number {
  const w = normalizeWeights(weights)
  const raw =
    gpaFactor * w.gpa +
    qualityFactor * w.quality +
    difficultyFactor * w.difficulty +
    sentimentFactor * w.sentiment
  return Math.round(raw * 100)
}
