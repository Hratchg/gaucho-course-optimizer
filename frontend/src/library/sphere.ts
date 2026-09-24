import * as THREE from 'three'
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

/** World position of a sphere book, matching BookSphere's rig, tilt, and spin. */
export function worldBookPosition(
  book: BookInstance,
  yaw: number,
  slide: number,
  scale: number,
): THREE.Vector3 {
  const p = new THREE.Vector3(...book.pos)
  p.applyAxisAngle(new THREE.Vector3(0, 1, 0), yaw)
  p.applyAxisAngle(new THREE.Vector3(1, 0, 0), 0.1)
  p.multiplyScalar(scale)
  p.add(new THREE.Vector3(slide, 0.28, 0))
  return p
}

/** World orientation: tilt, then spin, then the book's outward spine. */
export function worldBookQuaternion(book: BookInstance, yaw: number): THREE.Quaternion {
  const [rx, ry, rz] = book.rotation ?? [0, 0, book.lean]
  const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(0.1, 0, 0))
  q.multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(0, yaw, 0)))
  q.multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)))
  return q
}

/**
 * Index of the front-facing book farthest to the right — the one a pull
 * should lift out of the sphere.
 */
export function pickFrontBook(
  books: BookInstance[],
  yaw: number,
  slide: number,
  scale: number,
): number {
  let best = 0
  let bestX = -Infinity
  books.forEach((book, index) => {
    const p = worldBookPosition(book, yaw, slide, scale)
    if (p.z <= 0 || p.x <= bestX) return
    bestX = p.x
    best = index
  })
  return best
}
