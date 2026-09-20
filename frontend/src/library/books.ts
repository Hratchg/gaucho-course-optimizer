import * as THREE from 'three'
import { useMemo } from 'react'

/** Deterministic PRNG so book colors/sizes are stable per bookcase. */
export function mulberry32(seed: number) {
  let a = seed
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

export const BOOK_PALETTE = [
  '#B8433F', '#89547C', '#3E5F8A', '#437A6B', '#B08D3E',
  '#6C5CE7', '#20BFA9', '#C96A4A', '#54577C', '#7E5B3A',
] as const

export const CASE_W = 2.4
export const CASE_H = 3.1
export const CASE_D = 0.45
export const SHELF_COUNT = 5
export const SHELF_T = 0.045

/**
 * Native Tripo keeper (Y 0–1) shelf-top clusters from the unsimplified mesh,
 * excluding the cornice at y≈1. Scaled by CASE_H when the GLB is normalized.
 */
export const GENERATED_SHELF_Y_NATIVE = [0.0477, 0.2063, 0.3748, 0.5084, 0.654, 0.8137] as const
export const GENERATED_NATIVE_W = 0.4704
export const GENERATED_NATIVE_D = 0.2113
export const GENERATED_NATIVE_H = 1

export function materialHasColorMap(material: THREE.Material | THREE.Material[]): boolean {
  const mats = Array.isArray(material) ? material : [material]
  return mats.some((m) => Boolean(m && 'map' in m && (m as THREE.MeshStandardMaterial).map))
}

export interface BookInstance {
  pos: [number, number, number]
  scale: [number, number, number]
  color: string
}

export function proceduralShelfYs(caseH = CASE_H, count = SHELF_COUNT): number[] {
  return Array.from({ length: count }, (_, s) => 0.28 + s * ((caseH - 0.5) / count))
}

export function generatedShelfLayout(caseH = CASE_H) {
  const s = caseH / GENERATED_NATIVE_H
  const shelfYs = GENERATED_SHELF_Y_NATIVE.map((y) => y * s)
  const nextYs = [...shelfYs.slice(1), caseH - 0.06]
  return {
    innerW: GENERATED_NATIVE_W * s - 0.16,
    caseD: GENERATED_NATIVE_D * s,
    shelfYs,
    maxHeights: shelfYs.map((y, i) => Math.max(0.18, nextYs[i] - y - 0.04)),
  }
}

export function packShelfBooks({
  seed,
  shelfYs,
  innerW,
  caseD,
  shelfT = SHELF_T,
  maxHeights,
}: {
  seed: number
  shelfYs: number[]
  innerW: number
  caseD: number
  shelfT?: number
  maxHeights?: number[]
}): BookInstance[] {
  const rand = mulberry32(seed)
  const rows: BookInstance[] = []
  for (let s = 0; s < shelfYs.length; s++) {
    const shelfY = shelfYs[s]
    const maxH = maxHeights?.[s] ?? 0.46
    let x = -innerW / 2 + 0.06
    while (x < innerW / 2 - 0.1) {
      const w = 0.045 + rand() * 0.05
      const rawH = 0.32 + rand() * 0.14
      const h = Math.min(rawH, maxH)
      const d = caseD - 0.14 - rand() * 0.06
      if (rand() > 0.08) {
        rows.push({
          pos: [x + w / 2, shelfY + h / 2 + shelfT / 2, -0.02],
          scale: [w, h, d],
          color: BOOK_PALETTE[Math.floor(rand() * BOOK_PALETTE.length)],
        })
      }
      x += w + 0.006 + (rand() < 0.06 ? 0.09 : 0)
    }
  }
  return rows
}

export function applyBookInstances(mesh: THREE.InstancedMesh | null, books: BookInstance[]) {
  if (!mesh) return
  const m = new THREE.Matrix4()
  const q = new THREE.Quaternion()
  const v = new THREE.Vector3()
  const sc = new THREE.Vector3()
  books.forEach((b, i) => {
    v.set(...b.pos)
    sc.set(...b.scale)
    m.compose(v, q, sc)
    mesh.setMatrixAt(i, m)
    mesh.setColorAt(i, new THREE.Color(b.color))
  })
  mesh.instanceMatrix.needsUpdate = true
  if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true
}

export function useBookInstances(books: BookInstance[]) {
  const bookGeo = useMemo(() => new THREE.BoxGeometry(1, 1, 1), [])
  const bookMat = useMemo(
    () => new THREE.MeshStandardMaterial({ roughness: 0.75, metalness: 0.02 }),
    [],
  )
  const setInstances = (mesh: THREE.InstancedMesh | null) => applyBookInstances(mesh, books)
  return { bookGeo, bookMat, setInstances }
}
