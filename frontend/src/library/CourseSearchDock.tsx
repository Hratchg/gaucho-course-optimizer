import { useEffect, useState } from 'react'
import { BookOpen, Search } from 'lucide-react'
import { useCourseSearch } from '@/hooks/useCourseSearch'
import type { CourseResult } from '@/types/api'

interface CourseSearchDockProps {
  onPick: (course: CourseResult) => void
  placeholder?: string
  caption?: string
}

/** Shared home search pill — results sit above the input. */
export default function CourseSearchDock({
  onPick,
  placeholder = 'Search a course',
  caption,
}: CourseSearchDockProps) {
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const { data: courses, isLoading } = useCourseSearch(query)

  const results = (courses ?? []).slice(0, 6)
  const showList = query.trim().length >= 2

  useEffect(() => {
    setActiveIndex(0)
  }, [query, courses])

  const pick = (course: CourseResult) => {
    setQuery('')
    setActiveIndex(0)
    onPick(course)
  }

  const onKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showList) {
      if (event.key === 'Escape' && query) {
        event.preventDefault()
        event.stopPropagation()
        setQuery('')
      }
      return
    }

    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActiveIndex((index) => Math.min(index + 1, Math.max(results.length - 1, 0)))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIndex((index) => Math.max(index - 1, 0))
    } else if (event.key === 'Enter') {
      event.preventDefault()
      const course = results[activeIndex]
      if (course) pick(course)
    } else if (event.key === 'Escape') {
      event.preventDefault()
      event.stopPropagation()
      setQuery('')
      setActiveIndex(0)
    }
  }

  return (
    <div
      data-testid="search-dock"
      className="pointer-events-auto absolute bottom-6 left-1/2 z-30 w-[min(28rem,calc(100%-2rem))] -translate-x-1/2"
    >
      {caption && !showList && (
        <p className="mb-2 text-center text-sm text-foreground/80">
          {caption}
        </p>
      )}

      {showList && (
        <ul
          className="mb-2 max-h-64 overflow-y-auto rounded-xl border border-border/70 bg-card/95 shadow-[0_12px_32px_-20px_oklch(0.22_0.02_50_/_0.28)] backdrop-blur-xl"
          role="listbox"
          aria-label="Course results"
        >
          {isLoading && (
            <li className="px-4 py-3 text-sm text-muted-foreground">Searching…</li>
          )}
          {!isLoading && results.length === 0 && (
            <li className="px-4 py-3 text-sm text-muted-foreground">
              No matches. Try a code like &ldquo;MATH 4A&rdquo;.
            </li>
          )}
          {results.map((c, index) => (
            <li key={c.id} role="option" aria-selected={activeIndex === index}>
              <button
                type="button"
                onClick={() => pick(c)}
                onMouseEnter={() => setActiveIndex(index)}
                className={`focusable flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-primary/5 ${
                  activeIndex === index ? 'bg-primary/10' : ''
                }`}
              >
                <BookOpen className="h-4 w-4 shrink-0 text-primary" aria-hidden />
                <span className="font-medium text-foreground">{c.code}</span>
                {c.title && <span className="truncate text-sm text-muted-foreground">{c.title}</span>}
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="flex items-center gap-3 rounded-full border border-border/70 bg-card/95 px-4 shadow-[0_12px_32px_-20px_oklch(0.22_0.02_50_/_0.28)] backdrop-blur-xl">
        <Search className="h-4 w-4 shrink-0 text-primary/80" aria-hidden />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={placeholder}
          aria-label="Search courses"
          className="focusable w-full bg-transparent py-3 text-sm text-foreground placeholder:text-muted-foreground outline-none"
        />
      </div>
    </div>
  )
}
