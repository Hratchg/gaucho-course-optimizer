/** How long the pulled book travels before the course panel expands. */
export const FLIGHT_MS = 1700

const DEFAULT_START: readonly [number, number, number] = [1.55, 0.12, 0.55]
/** Where the book sits on the right, just before the panel expands. */
const END: readonly [number, number, number] = [2.85, 0.18, 2.35]

/**
 * Point on the arc from the sphere's right edge (`start`) to the right side of the screen.
 * `start` moves with the sphere so the trail stays attached while the globe slides left.
 */
export function flightPoint(
  t: number,
  start: readonly [number, number, number] = DEFAULT_START,
): [number, number, number] {
  const clamped = Math.min(1, Math.max(0, t))
  const control: [number, number, number] = [
    start[0] * 0.42 + END[0] * 0.58,
    Math.max(start[1], END[1]) + 1.05,
    start[2] * 0.4 + END[2] * 0.6,
  ]
  const u = 1 - clamped
  return [
    u * u * start[0] + 2 * u * clamped * control[0] + clamped * clamped * END[0],
    u * u * start[1] + 2 * u * clamped * control[1] + clamped * clamped * END[1],
    u * u * start[2] + 2 * u * clamped * control[2] + clamped * clamped * END[2],
  ]
}

export function smoothstep(t: number): number {
  const clamped = Math.min(1, Math.max(0, t))
  return clamped * clamped * (3 - 2 * clamped)
}
