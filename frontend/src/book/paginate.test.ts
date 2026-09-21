import { describe, expect, it } from 'vitest'
import { PROFESSORS_PER_PAGE, paginateCourse, type RankedProfessor } from './paginate'

function prof(overrides: Partial<RankedProfessor> = {}): RankedProfessor {
  return {
    id: 1,
    name: 'Ada Lovelace',
    department: 'CMPSC',
    gaucho_score: 80,
    gpa_factor: 0.8,
    quality_factor: 0.9,
    difficulty_factor: 0.7,
    sentiment_factor: 0.6,
    has_rmp: true,
    rmp_quality: 4.5,
    rmp_difficulty: 2.5,
    rmp_would_take_again: 90,
    rmp_num_ratings: 40,
    mean_gpa: 3.4,
    std_gpa: 0.3,
    avg_sentiment: 0.5,
    match_confidence: 0.95,
    quarters_taught: 6,
    tags: [],
    is_active_teacher: true,
    recent_quarters: [],
    teaching_next_quarter: true,
    scheduled_sections: [],
    computedScore: 84,
    ...overrides,
  }
}

describe('paginateCourse', () => {
  it('always opens with overview | settings even with no professors', () => {
    const spreads = paginateCourse({ courseCode: 'CMPSC 130A', courseTitle: null, professors: [] })
    expect(spreads).toHaveLength(1)
    expect(spreads[0].left.kind).toBe('overview')
    expect(spreads[0].right.kind).toBe('settings')
    if (spreads[0].left.kind === 'overview') {
      expect(spreads[0].left.professorCount).toBe(0)
      expect(spreads[0].left.topProfessorName).toBeNull()
      expect(spreads[0].left.avgGpa).toBeNull()
    }
  })

  it('chunks professors 3 per page with correct start ranks', () => {
    const professors = Array.from({ length: 7 }, (_, i) =>
      prof({ id: i + 1, name: `Prof ${i + 1}`, computedScore: 90 - i }),
    )
    const spreads = paginateCourse({ courseCode: 'MATH 4A', courseTitle: 'Calc', professors })
    const profPages = spreads
      .flatMap((s) => [s.left, s.right])
      .filter((p) => p.kind === 'professors')
    expect(profPages).toHaveLength(3) // 3 + 3 + 1
    expect(profPages[0]).toMatchObject({ startRank: 1 })
    expect(profPages[1]).toMatchObject({ startRank: 1 + PROFESSORS_PER_PAGE })
    expect(profPages[2]).toMatchObject({ startRank: 7 })
    if (profPages[2].kind === 'professors') {
      expect(profPages[2].professors.map((p) => p.name)).toEqual(['Prof 7'])
    }
  })

  it('pads with a blank page so every spread has two pages', () => {
    const professors = Array.from({ length: 3 }, (_, i) => prof({ id: i + 1 }))
    const spreads = paginateCourse({ courseCode: null, courseTitle: null, professors })
    // pages: overview, settings, professors → blank pad → 2 spreads
    expect(spreads).toHaveLength(2)
    expect(spreads[1].right.kind).toBe('blank')
    for (const s of spreads) {
      expect(s.left).toBeDefined()
      expect(s.right).toBeDefined()
    }
  })

  it('summarizes top professor and average GPA on the overview page', () => {
    const professors = [
      prof({ name: 'Best Prof', computedScore: 95, mean_gpa: 3.8 }),
      prof({ id: 2, name: 'Second', computedScore: 70, mean_gpa: 3.0 }),
      prof({ id: 3, name: 'NoGpa', computedScore: 60, mean_gpa: null }),
    ]
    const spreads = paginateCourse({ courseCode: 'PSTAT 120B', courseTitle: 'Prob', professors })
    const overview = spreads[0].left
    expect(overview.kind).toBe('overview')
    if (overview.kind === 'overview') {
      expect(overview.topProfessorName).toBe('Best Prof')
      expect(overview.topProfessorScore).toBe(95)
      expect(overview.avgGpa).toBeCloseTo(3.4)
      expect(overview.professorCount).toBe(3)
    }
  })

  it('is deterministic', () => {
    const professors = Array.from({ length: 5 }, (_, i) => prof({ id: i + 1 }))
    const args = { courseCode: 'X', courseTitle: 'Y', professors }
    expect(paginateCourse(args)).toEqual(paginateCourse(args))
  })
})
