import { describe, expect, it } from 'vitest'
import * as THREE from 'three'
import {
  BOOK_PALETTE,
  CASE_H,
  CASE_W,
  GENERATED_SHELF_Y_NATIVE,
  generatedShelfLayout,
  materialHasColorMap,
  packShelfBooks,
  proceduralShelfYs,
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
      expect(BOOK_PALETTE).toContain(book.color)
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
