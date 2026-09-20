import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { useTheme } from './useTheme'

const STORAGE_KEY = 'coursepick-theme'

function createMemoryStorage(): Storage {
  const map = new Map<string, string>()
  return {
    get length() {
      return map.size
    },
    clear() {
      map.clear()
    },
    getItem(key) {
      return map.has(key) ? map.get(key)! : null
    },
    key(index) {
      return [...map.keys()][index] ?? null
    },
    removeItem(key) {
      map.delete(key)
    },
    setItem(key, value) {
      map.set(key, String(value))
    },
  }
}

function stubMatchMedia(prefersDark: boolean) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    configurable: true,
    value: (query: string) => ({
      matches: query.includes('prefers-color-scheme: dark') ? prefersDark : false,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
      onchange: null,
    }),
  })
}

describe('useTheme', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      value: createMemoryStorage(),
    })
    document.documentElement.classList.remove('dark')
    stubMatchMedia(false)
  })

  afterEach(() => {
    document.documentElement.classList.remove('dark')
  })

  it('uses a stored light theme from localStorage', async () => {
    localStorage.setItem(STORAGE_KEY, 'light')
    stubMatchMedia(true)

    const { result } = renderHook(() => useTheme())

    expect(result.current.theme).toBe('light')
    await waitFor(() => {
      expect(document.documentElement.classList.contains('dark')).toBe(false)
    })
  })

  it('uses a stored dark theme from localStorage', async () => {
    localStorage.setItem(STORAGE_KEY, 'dark')
    stubMatchMedia(false)

    const { result } = renderHook(() => useTheme())

    expect(result.current.theme).toBe('dark')
    await waitFor(() => {
      expect(document.documentElement.classList.contains('dark')).toBe(true)
    })
  })

  it('falls back to the dark media query when nothing is stored', async () => {
    stubMatchMedia(true)

    const { result } = renderHook(() => useTheme())

    expect(result.current.theme).toBe('dark')
    await waitFor(() => {
      expect(document.documentElement.classList.contains('dark')).toBe(true)
    })
  })

  it('falls back to light when the media query prefers light', async () => {
    stubMatchMedia(false)

    const { result } = renderHook(() => useTheme())

    expect(result.current.theme).toBe('light')
    await waitFor(() => {
      expect(document.documentElement.classList.contains('dark')).toBe(false)
    })
  })

  it('ignores an invalid stored value and uses the media query', () => {
    localStorage.setItem(STORAGE_KEY, 'purple')
    stubMatchMedia(true)

    const { result } = renderHook(() => useTheme())

    expect(result.current.theme).toBe('dark')
  })

  it('toggle persists the opposite theme and flips the html class', async () => {
    stubMatchMedia(false)
    const { result } = renderHook(() => useTheme())

    expect(result.current.theme).toBe('light')

    act(() => {
      result.current.toggle()
    })

    expect(result.current.theme).toBe('dark')
    await waitFor(() => {
      expect(localStorage.getItem(STORAGE_KEY)).toBe('dark')
      expect(document.documentElement.classList.contains('dark')).toBe(true)
    })

    act(() => {
      result.current.toggle()
    })

    expect(result.current.theme).toBe('light')
    await waitFor(() => {
      expect(localStorage.getItem(STORAGE_KEY)).toBe('light')
      expect(document.documentElement.classList.contains('dark')).toBe(false)
    })
  })
})
