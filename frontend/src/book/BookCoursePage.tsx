import { useEffect, useMemo, useState, type CSSProperties } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useProfessors } from '@/hooks/useProfessors'
import { useProfessorGrades } from '@/hooks/useProfessorGrades'
import { computeGauchoScore, DEFAULT_TOGGLE_WEIGHTS, type ToggleWeights } from '@/lib/scoring'
import { WeightToggles } from '@/components/WeightToggles'
import { GradeChart } from '@/components/GradeChart'
import { Button } from '@/components/ui/button'
import { paginateCourse, type RankedProfessor } from './paginate'

function ScorePill({ score }: { score: number }) {
  return (
    <span className="inline-flex items-center rounded-full bg-foreground px-2.5 py-0.5 text-xs font-semibold text-background">
      {score}
    </span>
  )
}

/**
 * The course page as an open book — 2D React, same data and scoring as CoursePage.
 * Left/right pages come from paginateCourse(); arrow keys and buttons flip spreads.
 */
export default function BookCoursePage() {
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

  useEffect(() => {
    document.title = `${courseCode ?? 'Course'} | CoursePick`
  }, [courseCode])

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
  const maxSpread = Math.max(spreads.length - 1, 0)
  const clamped = Math.min(spreadIndex, maxSpread)
  const spread = spreads[clamped]
  const { data: topProfGrades } = useProfessorGrades(ranked[0]?.id ?? 0, numericCourseId)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') setSpreadIndex((s) => Math.min(s + 1, maxSpread))
      if (e.key === 'ArrowLeft') setSpreadIndex((s) => Math.max(s - 1, 0))
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [maxSpread])

  const flip = (dir: 1 | -1) => setSpreadIndex((s) => Math.min(Math.max(s + dir, 0), maxSpread))

  return (
    <section
      aria-label="Course rankings book"
      className="relative min-h-[calc(100dvh-3.5rem)] bg-zinc-100 px-4 py-8 dark:bg-zinc-950"
    >
      <div className="mx-auto flex max-w-5xl items-start justify-between gap-4">
        <div>
          <Link to="/" className="focusable text-sm text-muted-foreground hover:text-foreground">
            ← Shelf
          </Link>
          <h1 className="mt-2 font-heading text-2xl font-semibold tracking-tight text-foreground">
            {courseCode ?? 'Course rankings'}
          </h1>
        </div>
        <Link
          to={`/courses/${numericCourseId}?classic=1`}
          className="focusable rounded-full border border-border px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          Classic view
        </Link>
      </div>

      <div className="mx-auto mt-6 max-w-5xl">
        {isLoading && <p className="py-24 text-center text-muted-foreground">Opening the book…</p>}
        {error && (
          <div className="py-16 text-center" role="alert">
            <p className="font-medium">We could not load this course.</p>
            <div className="mt-4 flex justify-center gap-3">
              <Button type="button" variant="outline" onClick={() => refetch()}>
                Try again
              </Button>
              <Button asChild>
                <Link to={`/courses/${numericCourseId}?classic=1`}>Classic view</Link>
              </Button>
            </div>
          </div>
        )}

        {!isLoading && !error && spread && (
          <div
            className="grid overflow-hidden rounded-sm bg-[#f4efe4] text-[#1f1a18] shadow-[0_24px_60px_-28px_rgba(20,16,12,0.35)] ring-1 ring-black/8 md:grid-cols-2"
            style={
              {
                colorScheme: 'light',
                '--foreground': '#1f1a18',
                '--muted-foreground': '#6b6258',
                '--primary': '#e24b4b',
                '--border': '#ddd4c4',
              } as CSSProperties
            }
          >
            <article className="border-b border-black/8 px-8 py-8 md:border-b-0 md:border-r md:px-10">
              <PageFace
                page={spread.left}
                courseId={numericCourseId}
                weights={weights}
                onWeightsChange={setWeights}
                topProfGrades={topProfGrades}
              />
            </article>
            <article className="px-8 py-8 md:px-10">
              <PageFace
                page={spread.right}
                courseId={numericCourseId}
                weights={weights}
                onWeightsChange={setWeights}
              />
            </article>
          </div>
        )}

        {!isLoading && !error && spreads.length > 1 && (
          <div className="mt-6 flex items-center justify-center gap-4">
            <button
              type="button"
              onClick={() => flip(-1)}
              disabled={clamped === 0}
              aria-label="Previous pages"
              className="focusable rounded-full border border-border p-2 disabled:opacity-30"
            >
              <ChevronLeft className="h-5 w-5" aria-hidden />
            </button>
            <p className="min-w-24 text-center text-sm text-muted-foreground">
              {clamped + 1} / {spreads.length}
            </p>
            <button
              type="button"
              onClick={() => flip(1)}
              disabled={clamped === maxSpread}
              aria-label="Next pages"
              className="focusable rounded-full border border-border p-2 disabled:opacity-30"
            >
              <ChevronRight className="h-5 w-5" aria-hidden />
            </button>
          </div>
        )}
      </div>
    </section>
  )
}

function PageFace({
  page,
  courseId,
  weights,
  onWeightsChange,
  topProfGrades,
}: {
  page: ReturnType<typeof paginateCourse>[number]['left']
  courseId: number
  weights: ToggleWeights
  onWeightsChange: (w: ToggleWeights) => void
  topProfGrades?: import('@/types/api').GradeQuarter[]
}) {
  if (page.kind === 'overview') {
    return (
      <div className="flex min-h-[28rem] flex-col">
        <p className="text-xs uppercase tracking-[0.16em] text-black/45">Course</p>
        <h2 className="mt-1 font-heading text-3xl font-semibold tracking-tight">
          {page.courseCode ?? 'Course'}
        </h2>
        {page.courseTitle && <p className="mt-1 text-sm text-black/55">{page.courseTitle}</p>}
        <dl className="mt-6 space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-black/50">Professors</dt>
            <dd className="font-medium">{page.professorCount}</dd>
          </div>
          {page.avgGpa != null && (
            <div className="flex justify-between">
              <dt className="text-black/50">Average GPA</dt>
              <dd className="font-medium">{page.avgGpa.toFixed(2)}</dd>
            </div>
          )}
          {page.topProfessorName && (
            <div className="flex justify-between gap-3">
              <dt className="text-black/50">Top pick</dt>
              <dd className="flex items-center gap-2 font-medium">
                {page.topProfessorName}
                {page.topProfessorScore != null && <ScorePill score={page.topProfessorScore} />}
              </dd>
            </div>
          )}
        </dl>
        {topProfGrades && topProfGrades.length > 0 && (
          <div className="mt-4 h-40">
            <GradeChart quarters={topProfGrades} selectedQuarter="all" />
          </div>
        )}
        <p className="mt-auto pt-6 text-xs text-black/40">Next pages: ranking →</p>
      </div>
    )
  }

  if (page.kind === 'settings') {
    return (
      <div className="flex min-h-[28rem] flex-col">
        <h2 className="font-heading text-xl font-semibold">What matters to you</h2>
        <p className="mb-5 mt-1 text-sm text-black/55">
          Rankings update as you change these.
        </p>
        <WeightToggles weights={weights} onWeightsChange={onWeightsChange} />
        <p className="mt-auto pt-6 text-xs text-black/40">
          Prefer a list?{' '}
          <a href={`/courses/${courseId}?classic=1`} className="underline underline-offset-2">
            Classic view
          </a>
        </p>
      </div>
    )
  }

  if (page.kind === 'professors') {
    return (
      <div>
        <h2 className="font-heading text-lg font-semibold">
          {page.startRank}–{page.startRank + page.professors.length - 1}
        </h2>
        <ul className="mt-4 space-y-2">
          {page.professors.map((prof, i) => (
            <li
              key={prof.id}
              className="flex items-center gap-3 border-b border-black/8 py-3 last:border-0"
            >
              <span className="w-6 text-right text-sm text-black/40">{page.startRank + i}</span>
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{prof.name}</p>
                <p className="text-xs text-black/45">
                  {prof.mean_gpa != null ? `GPA ${prof.mean_gpa.toFixed(2)}` : 'GPA —'}
                  {prof.teaching_next_quarter ? ' · next quarter' : ''}
                </p>
              </div>
              <ScorePill score={prof.computedScore} />
            </li>
          ))}
        </ul>
      </div>
    )
  }

  return <div aria-hidden className="min-h-[28rem]" />
}
