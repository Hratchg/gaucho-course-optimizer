import { SPINE_VARIANTS, mulberry32, tintHex, type BookInstance } from './books'

/** Radius of the landing sphere, in world units. */
export const SPHERE_RADIUS = 2.05

/**
 * Upright books distributed on latitude rings of a sphere.
 * Each book's +z (spine face) points outward. Deterministic for a seed.
 */
export function sphereBooks(seed = 29, radius = SPHERE_RADIUS): BookInstance[] {
  const rand = mulberry32(seed)
  const rows = 11
  const books: BookInstance[] = []

  for (let r = 0; r < rows; r++) {
    const yy = -0.9 + (r / (rows - 1)) * 1.8
    const clamped = Math.max(-1, Math.min(1, yy))
    const phi = Math.asin(clamped)
    const ring = Math.cos(phi)
    // Gutter is about half a spine, so cream shows without isolating each book.
    const count = Math.max(8, Math.round(ring * 56))
    const off = rand() * Math.PI * 2

    for (let i = 0; i < count; i++) {
      const th = off + (i / count) * Math.PI * 2
      const h = (0.275 + rand() * 0.02) * (0.9 + 0.1 * Math.cos(phi))
      const w = 0.148 + rand() * 0.012
      const lean = (rand() - 0.5) * 0.1
      books.push({
        pos: [Math.sin(th) * ring * radius, yy * radius, Math.cos(th) * ring * radius],
        scale: [w, h, 0.055],
        color: tintHex(rand),
        variant: Math.floor(rand() * SPINE_VARIANTS),
        lean,
        rotation: [0, th, lean * Math.sin(phi)],
      })
    }
  }

  return books
}
