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

/** Cloth/leather spines that sit with stone + terracotta chrome. */
export const BOOK_PALETTE = [
  '#8a4630', '#3d4a42', '#2c3544', '#6b4a32', '#4a3d38',
  '#7a5338', '#3a2c28', '#4d5a52', '#5c4030', '#2f3d38',
] as const

export const SPINE_VARIANTS = BOOK_PALETTE.length

export const CASE_W = 2.4
export const CASE_H = 3.1
export const CASE_D = 0.45
export const SHELF_COUNT = 5
export const SHELF_T = 0.045

/** Full-viewport landing shelf — wide enough to fill a 16:9 frame at fov 46. */
export const HERO_W = 7.4
export const HERO_H = 4.35
export const HERO_D = 0.52
export const HERO_SHELVES = 6

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
  /** Near-white warm tint multiplied over the spine texture for in-variant variety. */
  color: string
  /** Index into the spine material variants (0..SPINE_VARIANTS-1). */
  variant: number
  /** Small z-rotation in radians for leaning books; 0 for upright/stacked. */
  lean: number
  /**
   * Full local Euler (XYZ, radians). When set, it replaces `lean`.
   * Used by the sphere so each spine faces outward.
   */
  rotation?: [number, number, number]
}

export const MAX_LEAN = 0.09

/** Warm near-white tint so books of one variant still differ slightly. */
export function tintHex(rand: () => number): string {
  const b = 0.82 + rand() * 0.18
  const to = (v: number) => Math.round(Math.min(1, v) * 255).toString(16).padStart(2, '0')
  return `#${to(b)}${to(b * 0.985)}${to(b * 0.955)}`
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

    // Occasionally reserve the right end of the shelf for a flat stack.
    const hasStack = rand() < 0.35
    const stackLen = hasStack ? 0.3 + rand() * 0.1 : 0
    const xEnd = innerW / 2 - 0.1 - (hasStack ? stackLen + 0.05 : 0)

    let x = -innerW / 2 + 0.06
    while (x < xEnd) {
      const w = 0.045 + rand() * 0.05
      const rawH = 0.32 + rand() * 0.14
      const h = Math.min(rawH, maxH)
      const d = caseD - 0.14 - rand() * 0.06
      if (rand() > 0.08) {
        const lean = rand() < 0.1 ? (rand() - 0.5) * 2 * MAX_LEAN : 0
        rows.push({
          pos: [x + w / 2, shelfY + h / 2 + shelfT / 2, -0.02],
          scale: [w, h, d],
          color: tintHex(rand),
          variant: Math.floor(rand() * SPINE_VARIANTS),
          lean,
        })
      }
      x += w + 0.006 + (rand() < 0.06 ? 0.09 : 0)
    }

    if (hasStack) {
      const count = 2 + Math.floor(rand() * 3)
      const cx = innerW / 2 - 0.08 - stackLen / 2
      let yTop = shelfY + shelfT / 2
      for (let k = 0; k < count; k++) {
        const thick = 0.045 + rand() * 0.025
        if (yTop + thick - (shelfY + shelfT / 2) > maxH) break
        const len = stackLen - rand() * 0.05
        const d = caseD - 0.16 - rand() * 0.05
        rows.push({
          pos: [cx + (rand() - 0.5) * 0.03, yTop + thick / 2, -0.02],
          scale: [len, thick, d],
          color: tintHex(rand),
          variant: Math.floor(rand() * SPINE_VARIANTS),
          lean: 0,
        })
        yTop += thick
      }
    }
  }
  return rows
}

export function applyBookInstances(mesh: THREE.InstancedMesh | null, books: BookInstance[]) {
  if (!mesh) return
  const m = new THREE.Matrix4()
  const q = new THREE.Quaternion()
  const e = new THREE.Euler()
  const v = new THREE.Vector3()
  const sc = new THREE.Vector3()
  books.forEach((b, i) => {
    v.set(...b.pos)
    sc.set(...b.scale)
    const [rx, ry, rz] = b.rotation ?? [0, 0, b.lean]
    e.set(rx, ry, rz)
    q.setFromEuler(e)
    m.compose(v, q, sc)
    mesh.setMatrixAt(i, m)
    mesh.setColorAt(i, new THREE.Color(b.color))
  })
  mesh.instanceMatrix.needsUpdate = true
  if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true
}

/** Deterministic decorative layout for one spine variant. */
export interface SpineSpec {
  base: string
  /** Horizontal gilt bands as [centerY, height] fractions of spine height. */
  bands: [number, number][]
  /** y fractions of thin embossed ridge lines. */
  ridges: number[]
  /** Whether the title panel (darker inset behind the top band) is drawn. */
  titlePanel: boolean
}

export function spineSpec(variant: number): SpineSpec {
  const rand = mulberry32(0x5eed + variant * 101)
  const base = BOOK_PALETTE[((variant % SPINE_VARIANTS) + SPINE_VARIANTS) % SPINE_VARIANTS]
  const bands: [number, number][] = [[0.1 + rand() * 0.06, 0.035]]
  if (rand() < 0.6) bands.push([bands[0][0] + 0.09, 0.018])
  if (rand() < 0.7) bands.push([0.88 + rand() * 0.04, 0.03])
  const ridgeCount = rand() < 0.5 ? 3 : 4
  const ridges = Array.from({ length: ridgeCount }, (_, i) => 0.3 + (i * 0.5) / ridgeCount + rand() * 0.02)
  return { base, bands, ridges, titlePanel: rand() < 0.5 }
}

const GILT = '#d8b862'
const PAGE_EDGE = '#e9dfc2'

/** Paint one spine variant onto an offscreen canvas. Null when no 2D canvas (tests/SSR). */
export function createSpineTexture(variant: number): THREE.CanvasTexture | null {
  if (typeof document === 'undefined') return null
  const canvas = document.createElement('canvas')
  canvas.width = 128
  canvas.height = 256
  const ctx = canvas.getContext('2d')
  if (!ctx || typeof ctx.createLinearGradient !== 'function') return null
  const spec = spineSpec(variant)
  const rand = mulberry32(0xa77e + variant * 733)
  const W = canvas.width
  const H = canvas.height

  ctx.fillStyle = spec.base
  ctx.fillRect(0, 0, W, H)

  // Rounded-spine shading: darker at left/right edges.
  const shade = ctx.createLinearGradient(0, 0, W, 0)
  shade.addColorStop(0, 'rgba(0,0,0,0.42)')
  shade.addColorStop(0.18, 'rgba(0,0,0,0)')
  shade.addColorStop(0.5, 'rgba(255,255,255,0.09)')
  shade.addColorStop(0.82, 'rgba(0,0,0,0)')
  shade.addColorStop(1, 'rgba(0,0,0,0.42)')
  ctx.fillStyle = shade
  ctx.fillRect(0, 0, W, H)

  // Leather grain speckle.
  for (let i = 0; i < 340; i++) {
    const a = rand() * 0.07
    ctx.fillStyle = rand() < 0.5 ? `rgba(0,0,0,${a})` : `rgba(255,255,255,${a * 0.6})`
    ctx.fillRect(Math.floor(rand() * W), Math.floor(rand() * H), 1 + Math.floor(rand() * 2), 1)
  }

  if (spec.titlePanel) {
    ctx.fillStyle = 'rgba(0,0,0,0.28)'
    ctx.fillRect(W * 0.14, H * 0.05, W * 0.72, H * 0.14)
  }

  // Gilt bands.
  for (const [cy, bh] of spec.bands) {
    const y = (cy - bh / 2) * H
    ctx.fillStyle = GILT
    ctx.fillRect(W * 0.08, y, W * 0.84, bh * H)
    ctx.fillStyle = 'rgba(255,255,255,0.35)'
    ctx.fillRect(W * 0.08, y, W * 0.84, 1)
    ctx.fillStyle = 'rgba(0,0,0,0.3)'
    ctx.fillRect(W * 0.08, y + bh * H - 1, W * 0.84, 1)
  }

  // Embossed ridges (raised hubs).
  for (const ry of spec.ridges) {
    const y = ry * H
    ctx.fillStyle = 'rgba(255,255,255,0.13)'
    ctx.fillRect(0, y - 2, W, 2)
    ctx.fillStyle = 'rgba(0,0,0,0.22)'
    ctx.fillRect(0, y, W, 2)
  }

  const tex = new THREE.CanvasTexture(canvas)
  tex.colorSpace = THREE.SRGBColorSpace
  tex.anisotropy = 4
  return tex
}

/**
 * Six-slot material arrays (one per BoxGeometry face) for each spine variant:
 * cloth sides, page-edge top, textured spine on the aisle-facing +z face.
 * Cached module-wide so every bookcase shares the same 10 variants.
 */
let spineMaterialsCache: THREE.Material[][] | null = null

export function getSpineMaterials(): THREE.Material[][] {
  if (spineMaterialsCache) return spineMaterialsCache
  const pages = new THREE.MeshStandardMaterial({ color: PAGE_EDGE, roughness: 0.92 })
  spineMaterialsCache = Array.from({ length: SPINE_VARIANTS }, (_, variant) => {
    const spec = spineSpec(variant)
    const cloth = new THREE.MeshStandardMaterial({ color: spec.base, roughness: 0.82, metalness: 0.02 })
    const tex = createSpineTexture(variant)
    const spine = tex
      ? new THREE.MeshStandardMaterial({ map: tex, roughness: 0.72, metalness: 0.05 })
      : cloth
    // BoxGeometry face order: +x, -x, +y (top), -y, +z (front/spine), -z.
    return [cloth, cloth, pages, cloth, spine, cloth]
  })
  return spineMaterialsCache
}

export function groupBooksByVariant(books: BookInstance[]): Map<number, BookInstance[]> {
  const groups = new Map<number, BookInstance[]>()
  for (const b of books) {
    const list = groups.get(b.variant)
    if (list) list.push(b)
    else groups.set(b.variant, [b])
  }
  return groups
}

export function useBookGeometry() {
  return useMemo(() => new THREE.BoxGeometry(1, 1, 1), [])
}
