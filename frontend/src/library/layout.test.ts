import { describe, expect, it } from 'vitest'
import { BOOKCASES, deptFromCourseCode, slotForDept } from './layout'

describe('deptFromCourseCode', () => {
  it('reads the department prefix from a spaced course code', () => {
    expect(deptFromCourseCode('MATH 4A')).toBe('MATH')
    expect(deptFromCourseCode('CMPSC 130A')).toBe('CMPSC')
  })

  it('uppercases a lowercase prefix', () => {
    expect(deptFromCourseCode('phys 1')).toBe('PHYS')
  })

  it('trims leading space before splitting', () => {
    expect(deptFromCourseCode('  CHEM 1A')).toBe('CHEM')
  })

  it('returns GENERAL when the code is empty', () => {
    expect(deptFromCourseCode('')).toBe('GENERAL')
    expect(deptFromCourseCode('   ')).toBe('GENERAL')
  })
})

describe('slotForDept', () => {
  it('returns the featured bookcase for a known department', () => {
    expect(slotForDept('MATH').dept).toBe('MATH')
    expect(slotForDept('PSY').dept).toBe('PSY')
  })

  it('falls back to the GENERAL case for unknown departments', () => {
    const general = BOOKCASES[BOOKCASES.length - 1]
    expect(general.dept).toBe('GENERAL')
    expect(slotForDept('HIST')).toBe(general)
    expect(slotForDept('WRIT')).toBe(general)
  })

  it('falls back to GENERAL when the case does not match exactly', () => {
    expect(slotForDept('general').dept).toBe('GENERAL')
    expect(slotForDept('')).toBe(BOOKCASES[BOOKCASES.length - 1])
  })
})
