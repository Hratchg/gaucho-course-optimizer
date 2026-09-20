/** Shelf layout: department → bookcase slot in the 3D library. */

export interface BookcaseSlot {
  /** Department label shown on the brass plaque. */
  dept: string
  /** World-space position of the bookcase center. */
  position: [number, number, number]
  /** Y-axis rotation in radians. */
  rotationY: number
}

const AISLE_Z = -1.05
const SPACING = 2.62

/**
 * Featured departments get their own case, arranged in a shallow arc
 * centered on the camera so the GENERAL case stays in the resting shot.
 */
export const BOOKCASES: BookcaseSlot[] = [
  { dept: 'MATH', position: [-2.5 * SPACING, 0, AISLE_Z - 0.28], rotationY: 0.10 },
  { dept: 'CHEM', position: [-1.5 * SPACING, 0, AISLE_Z - 0.10], rotationY: 0.05 },
  { dept: 'PHYS', position: [-0.5 * SPACING, 0, AISLE_Z], rotationY: 0.015 },
  { dept: 'CMPSC', position: [0.5 * SPACING, 0, AISLE_Z], rotationY: -0.015 },
  { dept: 'PSY', position: [1.5 * SPACING, 0, AISLE_Z - 0.10], rotationY: -0.05 },
  { dept: 'GENERAL', position: [2.5 * SPACING, 0, AISLE_Z - 0.28], rotationY: -0.10 },
]

/** Derive the department prefix from a course code like "MATH 4A" or "CMPSC 130A". */
export function deptFromCourseCode(code: string): string {
  const prefix = code.trim().split(/\s+/)[0]?.toUpperCase()
  return prefix ? prefix : 'GENERAL'
}

export function slotForDept(dept: string): BookcaseSlot {
  return BOOKCASES.find((b) => b.dept === dept) ?? BOOKCASES[BOOKCASES.length - 1]
}
