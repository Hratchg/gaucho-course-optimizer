import { describe, expect, it } from 'vitest'
import { flightPoint, smoothstep } from './flight'

describe('flightPoint', () => {
  it('travels to the right and stays in front of the sphere', () => {
    const start = flightPoint(0)
    const end = flightPoint(1)
    expect(end[0]).toBeGreaterThan(start[0] + 0.8)
    expect(end[2]).toBeGreaterThan(start[2])
    expect(flightPoint(0.5)[1]).toBeGreaterThan(start[1])
  })
})

describe('smoothstep', () => {
  it('eases between 0 and 1', () => {
    expect(smoothstep(0)).toBe(0)
    expect(smoothstep(1)).toBe(1)
    expect(smoothstep(0.5)).toBeCloseTo(0.5)
    expect(smoothstep(-1)).toBe(0)
    expect(smoothstep(2)).toBe(1)
  })
})
