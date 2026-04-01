// @vitest-environment node
import { describe, it, expect } from 'vitest'
import { normalizeWeights, computeGauchoScore } from './scoring'
import type { Weights } from './scoring'

describe('normalizeWeights', () => {
  it('normalizes weights proportionally', () => {
    const result = normalizeWeights({ gpa: 4, quality: 3, difficulty: 2, sentiment: 1 })
    expect(result.gpa).toBeCloseTo(0.4)
    expect(result.quality).toBeCloseTo(0.3)
    expect(result.difficulty).toBeCloseTo(0.2)
    expect(result.sentiment).toBeCloseTo(0.1)
  })

  it('returns equal weights when all inputs are zero', () => {
    const result = normalizeWeights({ gpa: 0, quality: 0, difficulty: 0, sentiment: 0 })
    expect(result.gpa).toBeCloseTo(0.25)
    expect(result.quality).toBeCloseTo(0.25)
    expect(result.difficulty).toBeCloseTo(0.25)
    expect(result.sentiment).toBeCloseTo(0.25)
  })

  it('normalized weights sum to 1', () => {
    const result = normalizeWeights({ gpa: 7, quality: 2, difficulty: 1, sentiment: 0 })
    const sum = result.gpa + result.quality + result.difficulty + result.sentiment
    expect(sum).toBeCloseTo(1)
  })
})

describe('computeGauchoScore', () => {
  const equalWeights: Weights = { gpa: 1, quality: 1, difficulty: 1, sentiment: 1 }

  it('computes weighted average and scales to 0-100', () => {
    // With equal weights, score = round((0.8+0.7+0.6+0.5)/4 * 100) = round(0.65*100) = 65
    const score = computeGauchoScore(0.8, 0.7, 0.6, 0.5, equalWeights)
    expect(score).toBe(65)
  })

  it('returns 100 when all factors are 1', () => {
    const score = computeGauchoScore(1, 1, 1, 1, equalWeights)
    expect(score).toBe(100)
  })

  it('returns 100 regardless of weights when all factors are 1', () => {
    const score = computeGauchoScore(1, 1, 1, 1, { gpa: 10, quality: 5, difficulty: 3, sentiment: 2 })
    expect(score).toBe(100)
  })

  it('returns 0 when all factors are 0', () => {
    const score = computeGauchoScore(0, 0, 0, 0, equalWeights)
    expect(score).toBe(0)
  })

  it('returns 0 regardless of weights when all factors are 0', () => {
    const score = computeGauchoScore(0, 0, 0, 0, { gpa: 4, quality: 3, difficulty: 2, sentiment: 1 })
    expect(score).toBe(0)
  })
})
