/** Shelf layout: a single hero bookcase that fills the landing viewport. */

export interface BookcaseSlot {
  dept: string
  position: [number, number, number]
  rotationY: number
}

/** One case, centered on the camera. Department is unused for placement. */
export const BOOKCASES: BookcaseSlot[] = [
  { dept: 'HERO', position: [0, 0, 0], rotationY: 0 },
]

/** Derive the department prefix from a course code like "MATH 4A" or "CMPSC 130A". */
export function deptFromCourseCode(code: string): string {
  const prefix = code.trim().split(/\s+/)[0]?.toUpperCase()
  return prefix ? prefix : 'GENERAL'
}

/** Every course pulls from the same hero shelf. */
export function slotForDept(_dept: string): BookcaseSlot {
  return BOOKCASES[0]
}
