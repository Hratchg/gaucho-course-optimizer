import type { ProfessorRanking } from '@/types/api'

/** Professor with the client-side score for the active weights. */
export interface RankedProfessor extends ProfessorRanking {
  computedScore: number
}

export type PageDef =
  | {
      kind: 'overview'
      courseCode: string | null
      courseTitle: string | null
      professorCount: number
      topProfessorId: number | null
      topProfessorName: string | null
      topProfessorScore: number | null
      avgGpa: number | null
    }
  | { kind: 'settings' }
  | { kind: 'professors'; startRank: number; professors: RankedProfessor[] }
  | { kind: 'blank' }

/** One open spread of the book: what is printed on the left and right pages. */
export interface Spread {
  left: PageDef
  right: PageDef
}

export const PROFESSORS_PER_PAGE = 3

/**
 * Pure layout of a course into book spreads:
 * spread 0 — overview | settings, then ranked professors 3 per page,
 * padded with a blank page when the count is odd.
 */
export function paginateCourse({
  courseCode,
  courseTitle,
  professors,
}: {
  courseCode: string | null
  courseTitle: string | null
  professors: RankedProfessor[]
}): Spread[] {
  const gpas = professors
    .map((p) => p.mean_gpa)
    .filter((g): g is number => g != null)
  const avgGpa = gpas.length
    ? Math.round((gpas.reduce((a, b) => a + b, 0) / gpas.length) * 100) / 100
    : null

  const pages: PageDef[] = [
    {
      kind: 'overview',
      courseCode,
      courseTitle,
      professorCount: professors.length,
      topProfessorId: professors[0]?.id ?? null,
      topProfessorName: professors[0]?.name ?? null,
      topProfessorScore: professors[0]?.computedScore ?? null,
      avgGpa,
    },
    { kind: 'settings' },
  ]

  for (let i = 0; i < professors.length; i += PROFESSORS_PER_PAGE) {
    pages.push({
      kind: 'professors',
      startRank: i + 1,
      professors: professors.slice(i, i + PROFESSORS_PER_PAGE),
    })
  }

  if (pages.length % 2 === 1) pages.push({ kind: 'blank' })

  const spreads: Spread[] = []
  for (let i = 0; i < pages.length; i += 2) {
    spreads.push({ left: pages[i], right: pages[i + 1] })
  }
  return spreads
}
