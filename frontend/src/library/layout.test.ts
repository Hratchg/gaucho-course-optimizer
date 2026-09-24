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
  it('always returns the single hero shelf', () => {
    expect(BOOKCASES).toHaveLength(1)
    expect(slotForDept('MATH')).toBe(BOOKCASES[0])
    expect(slotForDept('HIST')).toBe(BOOKCASES[0])
    expect(slotForDept('')).toBe(BOOKCASES[0])
  })
})
