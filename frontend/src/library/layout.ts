/** Shelf layout: department → bookcase slot in the 3D library. */

export interface BookcaseSlot {
  /** Department label shown on the brass plaque. */
  dept: string
  /** World-space position of the bookcase center. */
  position: [number, number, number]
  /** Y-axis rotation in radians. */
  rotationY: number
}

const AISLE_Z = -1.2
const SPACING = 3.4

/**
 * Featured departments get their own case, arranged in a shallow arc.
 * Everything else lands on the GENERAL case (rightmost).
 */
export const BOOKCASES: BookcaseSlot[] = [
  { dept: 'MATH', position: [-2 * SPACING, 0, AISLE_Z - 0.6], rotationY: 0.18 },
  { dept: 'CHEM', position: [-SPACING, 0, AISLE_Z - 0.2], rotationY: 0.09 },
  { dept: 'PHYS', position: [0, 0, AISLE_Z], rotationY: 0 },
  { dept: 'CMPSC', position: [SPACING, 0, AISLE_Z - 0.2], rotationY: -0.09 },
  { dept: 'PSY', position: [2 * SPACING, 0, AISLE_Z - 0.6], rotationY: -0.18 },
  { dept: 'GENERAL', position: [3 * SPACING, 0, AISLE_Z - 1.2], rotationY: -0.28 },
]

/** Derive the department prefix from a course code like "MATH 4A" or "CMPSC 130A". */
export function deptFromCourseCode(code: string): string {
  return code.trim().split(/\s+/)[0]?.toUpperCase() ?? 'GENERAL'
}

export function slotForDept(dept: string): BookcaseSlot {
  return BOOKCASES.find((b) => b.dept === dept) ?? BOOKCASES[BOOKCASES.length - 1]
}
