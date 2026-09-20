/** Feature detection for the 3D library landing. */
export function canRender3D(): boolean {
  if (typeof window === 'undefined') return false
  // Respect reduced motion — the library is inherently motion-heavy.
  if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return false
  // Small screens get the classic landing (perf + layout).
  if (window.innerWidth < 768) return false
  try {
    const canvas = document.createElement('canvas')
    return Boolean(
      canvas.getContext('webgl2') ?? canvas.getContext('webgl'),
    )
  } catch {
    return false
  }
}
