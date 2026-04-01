import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useColdStartMessage } from './useElapsedTime'

describe('useColdStartMessage', () => {
  beforeEach(() => { vi.useFakeTimers() })
  afterEach(() => { vi.useRealTimers() })

  it('returns false initially when loading', () => {
    const { result } = renderHook(() => useColdStartMessage(true))
    expect(result.current).toBe(false)
  })

  it('returns true after 3 seconds of loading', () => {
    const { result } = renderHook(() => useColdStartMessage(true))
    act(() => { vi.advanceTimersByTime(3000) })
    expect(result.current).toBe(true)
  })

  it('returns false when not loading', () => {
    const { result } = renderHook(() => useColdStartMessage(false))
    expect(result.current).toBe(false)
  })

  it('resets to false when loading stops', () => {
    const { result, rerender } = renderHook(
      ({ isLoading }) => useColdStartMessage(isLoading),
      { initialProps: { isLoading: true } }
    )
    act(() => { vi.advanceTimersByTime(3000) })
    expect(result.current).toBe(true)
    rerender({ isLoading: false })
    expect(result.current).toBe(false)
  })

  it('does not trigger if loading stops before 3 seconds', () => {
    const { result, rerender } = renderHook(
      ({ isLoading }) => useColdStartMessage(isLoading),
      { initialProps: { isLoading: true } }
    )
    act(() => { vi.advanceTimersByTime(2000) })
    expect(result.current).toBe(false)
    rerender({ isLoading: false })
    act(() => { vi.advanceTimersByTime(2000) })
    expect(result.current).toBe(false)
  })
})
