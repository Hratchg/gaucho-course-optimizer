import { lazy, Suspense, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, BookOpen, ArrowRight } from 'lucide-react'
import { useCourseSearch } from '@/hooks/useCourseSearch'
import { useTheme } from '@/hooks/useTheme'
import { BOOKCASES, deptFromCourseCode } from './layout'
import type { CameraTarget } from './CameraRig'
import type { CourseResult } from '@/types/api'

const LibraryScene = lazy(() => import('./LibraryScene'))

/**
 * The interactive library landing. Owns search state, maps the highlighted
 * course to a bookcase (camera flight), and pulls the book on selection.
 * "Open the book" navigates to the course page.
 */
export default function LibraryLanding() {
  const [query, setQuery] = useState('')
  const [picked, setPicked] = useState<CourseResult | null>(null)
  const [hovered, setHovered] = useState<CourseResult | null>(null)
  const { data: courses, isLoading } = useCourseSearch(query)
  const { theme } = useTheme()
  const navigate = useNavigate()

  const results = (courses ?? []).slice(0, 6)
  const top = picked ?? hovered ?? results[0] ?? null

  const featured = useMemo(() => new Set(BOOKCASES.map((b) => b.dept)), [])
  const deptOf = (c: CourseResult) => {
    const d = (c.department ?? deptFromCourseCode(c.code)).toUpperCase()
    return featured.has(d) ? d : 'GENERAL'
  }

  const target: CameraTarget = {
    dept: top ? deptOf(top) : null,
    bookFocus: Boolean(picked),
  }

  const openBook = () => {
    if (!picked) return
    navigate(`/courses/${picked.id}`, { state: { courseCode: picked.code } })
  }

  return (
    <section className="relative h-[calc(100dvh-3.5rem)] min-h-[480px] w-full overflow-hidden bg-brand-ink">
      {/* 3D scene */}
      <div className="absolute inset-0">
        <Suspense fallback={<div className="h-full w-full bg-brand-ink" aria-hidden />}>
          <LibraryScene
            target={target}
            pulledCourse={
              picked
                ? { code: picked.code, title: picked.title ?? undefined, dept: deptOf(picked) }
                : null
            }
            night={theme === 'dark'}
          />
        </Suspense>
      </div>

      {/* UI overlay */}
      <div className="relative z-10 flex h-full flex-col items-center pointer-events-none">
        <div className="mt-[10vh] text-center px-4">
          <p className="font-script text-2xl text-brand-gold-soft drop-shadow-md">welcome to the stacks</p>
          <h1 className="mt-1 font-display font-extrabold text-4xl md:text-5xl text-white drop-shadow-lg">
            Every UCSB course.
            <br />
            One library.
          </h1>
        </div>

        {/* Search card — docked top-right */}
        <div
          data-testid="search-dock"
          className="pointer-events-auto absolute left-4 right-4 top-4 sm:left-auto sm:right-6 sm:top-6 sm:w-96"
        >
          <div className="rounded-2xl bg-brand-parchment/95 dark:bg-brand-ink/90 shadow-2xl ring-1 ring-brand-gold/50 dark:ring-brand-gold/40 backdrop-blur">
            <div className="flex items-center gap-3 px-4">
              <Search className="h-5 w-5 shrink-0 text-brand-violet" aria-hidden />
              <input
                type="text"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value)
                  setPicked(null)
                }}
                placeholder='Find a course — try "CMPSC 130A"'
                aria-label="Search courses"
                className="focusable w-full bg-transparent py-4 font-sans text-base text-foreground placeholder:text-muted-foreground outline-none"
              />
            </div>

            {query.trim().length >= 2 && !picked && (
              <ul className="max-h-64 overflow-y-auto border-t border-border" role="listbox" aria-label="Course results">
                {isLoading && (
                  <li className="px-4 py-3 text-sm text-muted-foreground">Searching the stacks…</li>
                )}
                {!isLoading && results.length === 0 && (
                  <li className="px-4 py-3 text-sm text-muted-foreground">
                    Nothing on these shelves. Try a course code like &ldquo;MATH 4A&rdquo;.
                  </li>
                )}
                {results.map((c) => (
                  <li key={c.id} role="option" aria-selected={top?.id === c.id}>
                    <button
                      type="button"
                      onClick={() => setPicked(c)}
                      onMouseEnter={() => setHovered(c)}
                      onMouseLeave={() => setHovered(null)}
                      onFocus={() => setHovered(c)}
                      onBlur={() => setHovered(null)}
                      className={`focusable flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-brand-violet/10 ${
                        top?.id === c.id ? 'bg-brand-violet/5' : ''
                      }`}
                    >
                      <BookOpen className="h-4 w-4 shrink-0 text-brand-coral" aria-hidden />
                      <span className="font-sans font-semibold text-foreground">{c.code}</span>
                      {c.title && (
                        <span className="truncate text-sm text-muted-foreground">{c.title}</span>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Pulled-book action card */}
          {picked && (
            <div className="mt-4 flex items-center justify-between rounded-2xl bg-brand-violet px-5 py-4 shadow-2xl">
              <div className="min-w-0">
                <p className="font-heading font-bold text-white">{picked.code}</p>
                {picked.title && (
                  <p className="truncate text-sm text-white/80">{picked.title}</p>
                )}
              </div>
              <button
                type="button"
                onClick={openBook}
                className="focusable btn-press ml-4 inline-flex shrink-0 items-center gap-2 rounded-full bg-white px-5 py-2.5 font-sans font-semibold text-brand-violet hover:bg-white/90"
              >
                Open the book
                <ArrowRight className="h-4 w-4" aria-hidden />
              </button>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
