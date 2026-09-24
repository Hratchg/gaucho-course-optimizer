/** Course id from `/courses/:id`, or null on the shelf. */
export function courseIdFromPath(pathname: string): number | null {
  const match = pathname.match(/^\/courses\/(\d+)\/?$/)
  return match ? Number(match[1]) : null
}
