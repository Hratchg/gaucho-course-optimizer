import { describe, expect, it } from 'vitest'
import * as THREE from 'three'
import {
  CASE_H,
  CASE_W,
  GENERATED_SHELF_Y_NATIVE,
  MAX_LEAN,
  SPINE_VARIANTS,
  generatedShelfLayout,
  materialHasColorMap,
  packShelfBooks,
  proceduralShelfYs,
  spineSpec,
} from './books'

describe('proceduralShelfYs', () => {
  it('matches the five original shelf tops', () => {
    expect(proceduralShelfYs()).toEqual([
      0.28,
      0.28 + (CASE_H - 0.5) / 5,
      0.28 + (2 * (CASE_H - 0.5)) / 5,
      0.28 + (3 * (CASE_H - 0.5)) / 5,
      0.28 + (4 * (CASE_H - 0.5)) / 5,
    ])
  })
})

describe('generatedShelfLayout', () => {
  it('scales the six measured keeper shelves into CASE_H space', () => {
    const layout = generatedShelfLayout(CASE_H)
    expect(layout.shelfYs).toHaveLength(GENERATED_SHELF_Y_NATIVE.length)
    expect(layout.shelfYs[0]).toBeCloseTo(GENERATED_SHELF_Y_NATIVE[0] * CASE_H)
    expect(layout.shelfYs[layout.shelfYs.length - 1]).toBeCloseTo(GENERATED_SHELF_Y_NATIVE[5] * CASE_H)
    expect(layout.maxHeights.every((h) => h >= 0.18)).toBe(true)
    expect(layout.innerW).toBeGreaterThan(1)
    expect(layout.innerW).toBeLessThan(CASE_W)
  })
})

describe('packShelfBooks', () => {
  it('is deterministic for a given seed', () => {
    const opts = {
      seed: 13,
      shelfYs: proceduralShelfYs(),
      innerW: CASE_W - 0.2,
      caseD: 0.45,
    }
    const a = packShelfBooks(opts)
    const b = packShelfBooks(opts)
    expect(a.length).toBeGreaterThan(20)
    expect(a).toEqual(b)
  })

  it('keeps every book on a known shelf and inside the inner width', () => {
    const shelfYs = proceduralShelfYs()
    const innerW = CASE_W - 0.2
    const books = packShelfBooks({ seed: 7919, shelfYs, innerW, caseD: 0.45 })
    for (const book of books) {
      const [x, y] = book.pos
      expect(x).toBeGreaterThan(-innerW / 2)
      expect(x).toBeLessThan(innerW / 2)
      expect(shelfYs.some((shelfY) => y > shelfY && y < shelfY + 0.55)).toBe(true)
      expect(book.color).toMatch(/^#[0-9a-f]{6}$/)
    }
  })

  it('assigns every book a valid spine variant and bounded lean', () => {
    const books = packShelfBooks({
      seed: 99,
      shelfYs: proceduralShelfYs(),
      innerW: CASE_W - 0.2,
      caseD: 0.45,
    })
    for (const book of books) {
      expect(book.variant).toBeGreaterThanOrEqual(0)
      expect(book.variant).toBeLessThan(SPINE_VARIANTS)
      expect(Number.isInteger(book.variant)).toBe(true)
      expect(Math.abs(book.lean)).toBeLessThanOrEqual(MAX_LEAN)
    }
  })

  it('adds flat stacked books on some shelves that stay upright and in bounds', () => {
    const innerW = CASE_W - 0.2
    const books = packShelfBooks({ seed: 5, shelfYs: proceduralShelfYs(), innerW, caseD: 0.45 })
    // Flat books are wider than tall; upright books the reverse.
    const flat = books.filter((b) => b.scale[0] > b.scale[1])
    expect(flat.length).toBeGreaterThan(0)
    for (const b of flat) {
      expect(b.lean).toBe(0)
      expect(b.pos[0] + b.scale[0] / 2).toBeLessThanOrEqual(innerW / 2)
    }
  })

  it('detects whether a material already has a color map', () => {
    expect(materialHasColorMap(new THREE.MeshStandardMaterial({ color: '#9a7b57' }))).toBe(false)
    expect(materialHasColorMap(new THREE.MeshStandardMaterial({ map: new THREE.Texture() }))).toBe(true)
  })

  it('caps generated-case book height so they stay under the next shelf', () => {
    const layout = generatedShelfLayout()
    const books = packShelfBooks({
      seed: 42,
      shelfYs: layout.shelfYs,
      innerW: layout.innerW,
      caseD: layout.caseD,
      maxHeights: layout.maxHeights,
    })
    expect(books.length).toBeGreaterThan(20)
    books.forEach((book, i) => {
      const shelfIndex = layout.shelfYs.findIndex(
        (shelfY, s) =>
          book.pos[1] > shelfY &&
          book.pos[1] < shelfY + layout.maxHeights[s] + 0.05,
      )
      expect(shelfIndex, `book ${i}`).toBeGreaterThanOrEqual(0)
      expect(book.scale[1]).toBeLessThanOrEqual(layout.maxHeights[shelfIndex] + 1e-6)
    })
  })
})

describe('spineSpec', () => {
  it('is deterministic per variant and stays inside the palette', () => {
    for (let v = 0; v < SPINE_VARIANTS; v++) {
      const a = spineSpec(v)
      const b = spineSpec(v)
      expect(a).toEqual(b)
      expect(a.base).toMatch(/^#[0-9a-f]{6}$/)
      expect(a.bands.length).toBeGreaterThanOrEqual(1)
      for (const [cy, bh] of a.bands) {
        expect(cy).toBeGreaterThan(0)
        expect(cy).toBeLessThan(1)
        expect(bh).toBeGreaterThan(0)
        expect(bh).toBeLessThan(0.1)
      }
      for (const r of a.ridges) {
        expect(r).toBeGreaterThan(0.2)
        expect(r).toBeLessThan(0.95)
      }
    }
  })

  it('varies band layout across variants', () => {
    const layouts = new Set(
      Array.from({ length: SPINE_VARIANTS }, (_, v) => JSON.stringify(spineSpec(v))),
    )
    expect(layouts.size).toBeGreaterThan(SPINE_VARIANTS / 2)
  })
})
