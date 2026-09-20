import { afterEach, describe, expect, it, vi } from 'vitest'
import { canRender3D } from './webgl'

const originalInnerWidth = window.innerWidth
const originalMatchMedia = window.matchMedia

function stubMatchMedia(reducedMotion: boolean) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    configurable: true,
    value: (query: string) => ({
      matches: query.includes('prefers-reduced-motion: reduce') ? reducedMotion : false,
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

function stubViewport(width: number) {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  })
}

function stubWebGL(available: boolean) {
  return vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockImplementation(() => {
    return available ? ({} as WebGLRenderingContext) : null
  })
}

describe('canRender3D', () => {
  afterEach(() => {
    stubViewport(originalInnerWidth)
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      configurable: true,
      value: originalMatchMedia,
    })
    vi.restoreAllMocks()
  })

  it('rejects when the user prefers reduced motion', () => {
    stubMatchMedia(true)
    stubViewport(1440)
    stubWebGL(true)

    expect(canRender3D()).toBe(false)
  })

  it('rejects viewports narrower than 768px', () => {
    stubMatchMedia(false)
    stubViewport(375)
    stubWebGL(true)

    expect(canRender3D()).toBe(false)
  })

  it('rejects a 767px viewport on the md breakpoint edge', () => {
    stubMatchMedia(false)
    stubViewport(767)
    stubWebGL(true)

    expect(canRender3D()).toBe(false)
  })

  it('allows a 768px viewport when WebGL is available and motion is OK', () => {
    stubMatchMedia(false)
    stubViewport(768)
    stubWebGL(true)

    expect(canRender3D()).toBe(true)
  })

  it('rejects when WebGL is unavailable', () => {
    stubMatchMedia(false)
    stubViewport(1440)
    stubWebGL(false)

    expect(canRender3D()).toBe(false)
  })
})
