import { describe, expect, it } from 'vitest'
import { GENERATED_BOOKCASE_URL } from './generatedAssets'

describe('generatedAssets', () => {
  it('keeps the procedural bookcase on unless VITE_GENERATED_BOOKCASE=1', () => {
    expect(GENERATED_BOOKCASE_URL).toBeNull()
  })
})
