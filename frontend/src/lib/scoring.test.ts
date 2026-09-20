// @vitest-environment node
import { describe, it, expect } from 'vitest'
import { normalizeWeights, normalizeToggles, computeGauchoScore } from './scoring'
import type { Weights, ToggleWeights } from './scoring'

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

  it('omits missing RateMyProfessors factors instead of treating them as 0.5', () => {
    const score = computeGauchoScore(0.8, null, null, null, equalWeights)
    expect(score).toBe(80)
  })
})

describe('normalizeToggles', () => {
  it('converts all-enabled toggles to 0.25 each', () => {
    const result = normalizeToggles({ gpa: true, quality: true, difficulty: true, sentiment: true })
    expect(result.gpa).toBeCloseTo(0.25)
    expect(result.quality).toBeCloseTo(0.25)
    expect(result.difficulty).toBeCloseTo(0.25)
    expect(result.sentiment).toBeCloseTo(0.25)
  })

  it('converts 2 enabled toggles to 0.5 each, disabled to 0', () => {
    const result = normalizeToggles({ gpa: true, quality: true, difficulty: false, sentiment: false })
    expect(result.gpa).toBeCloseTo(0.5)
    expect(result.quality).toBeCloseTo(0.5)
    expect(result.difficulty).toBe(0)
    expect(result.sentiment).toBe(0)
  })

  it('converts 1 enabled toggle to 1.0, rest to 0', () => {
    const result = normalizeToggles({ gpa: true, quality: false, difficulty: false, sentiment: false })
    expect(result.gpa).toBeCloseTo(1.0)
    expect(result.quality).toBe(0)
    expect(result.difficulty).toBe(0)
    expect(result.sentiment).toBe(0)
  })

  it('with all 4 enabled, normalized weights sum to 1', () => {
    const result = normalizeToggles({ gpa: true, quality: true, difficulty: true, sentiment: true })
    const sum = result.gpa + result.quality + result.difficulty + result.sentiment
    expect(sum).toBeCloseTo(1)
  })
})

describe('computeGauchoScore with ToggleWeights', () => {
  it('computes score with all 4 toggles ON (25% each)', () => {
    const allOn: ToggleWeights = { gpa: true, quality: true, difficulty: true, sentiment: true }
    // (0.8*0.25 + 0.7*0.25 + 0.6*0.25 + 0.5*0.25) * 100 = 0.65 * 100 = 65
    const score = computeGauchoScore(0.8, 0.7, 0.6, 0.5, allOn)
    expect(score).toBe(65)
  })

  it('computes score with 2 toggles ON (50% each)', () => {
    const twoOn: ToggleWeights = { gpa: true, quality: true, difficulty: false, sentiment: false }
    // (0.8*0.5 + 0.7*0.5 + 0.6*0 + 0.5*0) * 100 = 0.75 * 100 = 75
    const score = computeGauchoScore(0.8, 0.7, 0.6, 0.5, twoOn)
    expect(score).toBe(75)
  })

  it('computes score with 1 toggle ON (100% to that factor)', () => {
    const oneOn: ToggleWeights = { gpa: true, quality: false, difficulty: false, sentiment: false }
    // 0.8 * 1.0 * 100 = 80
    const score = computeGauchoScore(0.8, 0.7, 0.6, 0.5, oneOn)
    expect(score).toBe(80)
  })

  it('returns 100 when all factors are 1.0 regardless of toggle config', () => {
    const twoOn: ToggleWeights = { gpa: true, quality: false, difficulty: true, sentiment: false }
    expect(computeGauchoScore(1, 1, 1, 1, twoOn)).toBe(100)
  })

  it('returns 0 when all factors are 0.0 regardless of toggle config', () => {
    const threeOn: ToggleWeights = { gpa: true, quality: true, difficulty: true, sentiment: false }
    expect(computeGauchoScore(0, 0, 0, 0, threeOn)).toBe(0)
  })
})
