import { describe, expect, it } from 'vitest'
import { SPINE_VARIANTS } from './books'
import { SPHERE_RADIUS, sphereBooks } from './sphere'

describe('sphereBooks', () => {
  it('is deterministic and spaced enough to read as a sphere', () => {
    const a = sphereBooks()
    const b = sphereBooks()
    expect(a.length).toBeGreaterThan(320)
    expect(a.length).toBeLessThan(560)
    expect(a).toEqual(b)
  })

  it('places every book on the sphere with a valid spine', () => {
    const books = sphereBooks(29, SPHERE_RADIUS)
    for (const book of books) {
      const [x, y, z] = book.pos
      expect(Math.hypot(x, y, z)).toBeCloseTo(SPHERE_RADIUS, 2)
      expect(book.variant).toBeGreaterThanOrEqual(0)
      expect(book.variant).toBeLessThan(SPINE_VARIANTS)
      expect(book.rotation?.[1]).toBeTypeOf('number')
    }
  })
})
