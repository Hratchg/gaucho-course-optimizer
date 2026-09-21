import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { Canvas } from '@react-three/fiber'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useProfessors } from '@/hooks/useProfessors'
import { useProfessorGrades } from '@/hooks/useProfessorGrades'
import { computeGauchoScore, DEFAULT_TOGGLE_WEIGHTS, type ToggleWeights } from '@/lib/scoring'
import { Button } from '@/components/ui/button'
import Book from './Book'
import { paginateCourse, type RankedProfessor } from './paginate'

const TURN_SETTLE_MS = 650

/**
 * The 3D open-book course view: professors ranked on flippable parchment
 * pages. Purely presentational — same data hooks and scoring as CoursePage.
 */
export default function BookCourseView() {
  const { courseId } = useParams<{ courseId: string }>()
  const numericCourseId = Number(courseId)
  const location = useLocation()
  const courseCode: string | null =
    (location.state as { courseCode?: string } | null)?.courseCode ?? null
  const courseTitle: string | null =
    (location.state as { courseTitle?: string } | null)?.courseTitle ?? null

  const { data: professors, isLoading, error, refetch } = useProfessors(numericCourseId)
  const [weights, setWeights] = useState<ToggleWeights>(DEFAULT_TOGGLE_WEIGHTS)
  const [spreadIndex, setSpreadIndex] = useState(0)
  const [turning, setTurning] = useState(true) // entrance cover-flip
  const settleTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    document.title = `${courseCode ?? 'Course Results'} | CoursePick`
  }, [courseCode])

  // Entrance settle.
  useEffect(() => {
    const t = setTimeout(() => setTurning(false), 900)
    return () => clearTimeout(t)
  }, [])

  const ranked: RankedProfessor[] = useMemo(() => {
    if (!professors) return []
    return professors
      .map((p) => ({
        ...p,
        computedScore: computeGauchoScore(
          p.gpa_factor,
          p.quality_factor,
          p.difficulty_factor,
          p.sentiment_factor,
          weights,
        ),
      }))
      .sort((a, b) => b.computedScore - a.computedScore)
  }, [professors, weights])

  const spreads = useMemo(
    () => paginateCourse({ courseCode, courseTitle, professors: ranked }),
    [courseCode, courseTitle, ranked],
  )

  // Grade history for the top-ranked professor, shown on the overview page.
  // Fetched here because drei Html content has no react-query context.
  const { data: topProfGrades } = useProfessorGrades(ranked[0]?.id ?? 0, numericCourseId)

  const maxSpread = Math.max(spreads.length - 1, 0)
  const clampedIndex = Math.min(spreadIndex, maxSpread)

  const flip = (dir: 1 | -1) => {
    setSpreadIndex((s) => {
      const next = Math.min(Math.max(s + dir, 0), maxSpread)
      if (next !== s) {
        setTurning(true)
        if (settleTimer.current) clearTimeout(settleTimer.current)
        settleTimer.current = setTimeout(() => setTurning(false), TURN_SETTLE_MS)
      }
      return next
    })
  }

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') flip(1)
      if (e.key === 'ArrowLeft') flip(-1)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [maxSpread])

  return (
    <section
      aria-label="Course rankings book"
      className="relative h-[calc(100dvh-3.5rem)] min-h-[560px] w-full overflow-hidden bg-brand-ink"
    >
      {/* Header strip */}
      <div className="pointer-events-none absolute inset-x-0 top-0 z-20 flex items-start justify-between px-6 pt-4">
        <div>
          <h1 className="font-display text-2xl font-black text-white drop-shadow">
            {courseCode ?? 'Course rankings'}
          </h1>
          <p className="font-script text-lg text-brand-gold-soft">from the CoursePick stacks</p>
        </div>
        <Link
          to={`/courses/${numericCourseId}?classic=1`}
          className="focusable pointer-events-auto rounded-full border border-brand-gold/60 px-4 py-1.5 text-sm font-semibold text-brand-gold-soft hover:bg-brand-gold/10"
        >
          Classic view
        </Link>
      </div>

      {/* 3D book */}
      <div className="absolute inset-0">
        <Canvas
          shadows
          camera={{ position: [0, 0.25, 3.4], fov: 42 }}
          dpr={[1, 2]}
          aria-hidden
        >
          <color attach="background" args={['#161320']} />
          <ambientLight intensity={0.55} color="#fff2dd" />
          <directionalLight
            position={[2.4, 3.2, 3.6]}
            intensity={1.7}
            color="#ffe3b8"
            castShadow
            shadow-mapSize={[1024, 1024]}
          />
          {/* Gold rim from behind for the regal glow */}
          <pointLight position={[-2.5, 1.2, -2]} intensity={9} color="#c9a227" />
          {!isLoading && !error && (
            <Book
              spreads={spreads}
              spreadIndex={clampedIndex}
              courseId={numericCourseId}
              weights={weights}
              onWeightsChange={setWeights}
              turning={turning}
              topProfGrades={topProfGrades}
            />
          )}
        </Canvas>
      </div>

      {/* Loading / error overlays */}
      {isLoading && (
        <div className="absolute inset-0 z-10 flex items-center justify-center">
          <p className="font-script text-3xl text-brand-gold-soft">opening the book…</p>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 z-10 flex items-center justify-center" role="alert">
          <div className="rounded-2xl bg-brand-parchment px-8 py-6 text-center shadow-2xl">
            <p className="font-display text-lg font-bold text-brand-ink">
              We could not open this course.
            </p>
            <div className="mt-4 flex justify-center gap-3">
              <Button type="button" variant="outline" onClick={() => refetch()}>
                Try again
              </Button>
              <Button asChild>
                <Link to={`/courses/${numericCourseId}?classic=1`}>Classic view</Link>
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Page controls */}
      {!isLoading && !error && spreads.length > 1 && (
        <div className="absolute inset-x-0 bottom-5 z-20 flex items-center justify-center gap-4">
          <button
            type="button"
            onClick={() => flip(-1)}
            disabled={clampedIndex === 0}
            aria-label="Previous pages"
            className="focusable btn-press rounded-full border border-brand-gold/60 bg-brand-ink/70 p-2.5 text-brand-gold-soft backdrop-blur disabled:opacity-30"
          >
            <ChevronLeft className="h-5 w-5" aria-hidden />
          </button>
          <p className="min-w-24 text-center text-sm text-white/70">
            Spread {clampedIndex + 1} of {spreads.length}
          </p>
          <button
            type="button"
            onClick={() => flip(1)}
            disabled={clampedIndex === maxSpread}
            aria-label="Next pages"
            className="focusable btn-press rounded-full border border-brand-gold/60 bg-brand-ink/70 p-2.5 text-brand-gold-soft backdrop-blur disabled:opacity-30"
          >
            <ChevronRight className="h-5 w-5" aria-hidden />
          </button>
        </div>
      )}
      <p className="absolute bottom-1.5 left-0 right-0 z-20 text-center text-xs text-white/40">
        Use ← → to flip pages
      </p>
    </section>
  )
}
