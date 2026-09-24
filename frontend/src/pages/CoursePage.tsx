import { Link, useLocation, useParams } from 'react-router-dom'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useProfessors } from '@/hooks/useProfessors'
import { ProfessorCard } from '@/components/ProfessorCard'
import { SkeletonCard } from '@/components/SkeletonCard'
import { WeightToggles } from '@/components/WeightToggles'
import { computeGauchoScore, DEFAULT_TOGGLE_WEIGHTS } from '@/lib/scoring'
import type { ToggleWeights } from '@/lib/scoring'
import { CourseSections } from '@/components/CourseSections'
import { useColdStartMessage } from '@/hooks/useElapsedTime'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'

type QuarterFilter = 'all' | 'next' | 'current'

function ActiveTeacherFilter({
  checked,
  onCheckedChange,
}: {
  checked: boolean
  onCheckedChange: (checked: boolean) => void
}) {
  return (
    <div className="flex items-center gap-2">
      <Checkbox
        id="active-filter"
        checked={checked}
        onCheckedChange={(val) => onCheckedChange(val === true)}
      />
      <label
        htmlFor="active-filter"
        className="text-sm cursor-pointer select-none"
      >
        Taught recently only
      </label>
    </div>
  )
}

function QuarterFilterButtons({
  value,
  onChange,
  scheduledQuarter,
}: {
  value: QuarterFilter
  onChange: (v: QuarterFilter) => void
  scheduledQuarter: string
}) {
  const options: { label: string; value: QuarterFilter }[] = [
    { label: 'All', value: 'all' },
    { label: scheduledQuarter, value: 'next' },
    { label: 'Taught recently', value: 'current' },
  ]

  return (
    <div role="group" aria-label="Quarter" className="flex rounded-full bg-muted p-1">
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          className={`focusable min-h-9 flex-1 rounded-full px-3 text-sm transition-colors ${
            value === opt.value
              ? 'bg-card text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => onChange(opt.value)}
          aria-pressed={value === opt.value}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}

export default function CoursePage({
  courseId: courseIdProp,
  compact = false,
}: {
  courseId?: number
  compact?: boolean
} = {}) {
  const { courseId: routeId } = useParams<{ courseId: string }>()
  const location = useLocation()
  const numericCourseId = courseIdProp ?? Number(routeId)
  const nav = location.state as { courseCode?: string; courseTitle?: string | null } | null
  const courseCode = nav?.courseCode?.trim() || ''
  const courseTitle = nav?.courseTitle?.trim() || ''
  const { data: professors, isLoading, error, refetch } = useProfessors(numericCourseId)

  const [weights, setWeights] = useState<ToggleWeights>(DEFAULT_TOGGLE_WEIGHTS)
  const [sheetOpen, setSheetOpen] = useState(false)
  const [showActiveOnly, setShowActiveOnly] = useState(false)
  const [quarterFilter, setQuarterFilter] = useState<QuarterFilter>('all')
  const quarterTouched = useRef(false)
  const showColdStart = useColdStartMessage(isLoading)

  useEffect(() => {
    quarterTouched.current = false
    setQuarterFilter('all')
  }, [numericCourseId])

  useEffect(() => {
    if (quarterTouched.current || !professors) return
    if (professors.some((professor) => professor.teaching_next_quarter)) {
      setQuarterFilter('next')
    }
  }, [professors])

  function changeQuarter(value: QuarterFilter) {
    quarterTouched.current = true
    setQuarterFilter(value)
  }

  useEffect(() => {
    if (compact) return
    document.title = courseCode ? `${courseCode} | CoursePick` : 'Course Results | CoursePick'
  }, [compact, courseCode])

  const rankedProfessors = useMemo(() => {
    if (!professors) return []
    let filtered = [...professors]

    // Apply quarter filter
    if (quarterFilter === 'next') {
      const nextProfs = filtered.filter(p => p.teaching_next_quarter)
      if (nextProfs.length > 0) {
        filtered = nextProfs
      }
    } else if (quarterFilter === 'current') {
      // Current quarter = actively teaching (taught recently)
      const currentProfs = filtered.filter(p => p.is_active_teacher)
      if (currentProfs.length > 0) {
        filtered = currentProfs
      }
    }

    // Apply active teacher filter
    if (showActiveOnly) {
      const activeProfs = filtered.filter(p => p.is_active_teacher)
      // If no professors are active, show all (per edge case decision)
      if (activeProfs.length > 0) {
        filtered = activeProfs
      }
    }

    return filtered
      .map((p) => ({
        ...p,
        computedScore: computeGauchoScore(
          p.gpa_factor, p.quality_factor, p.difficulty_factor, p.sentiment_factor, weights
        ),
      }))
      .sort((a, b) => b.computedScore - a.computedScore)
  }, [professors, weights, showActiveOnly, quarterFilter])

  const hasActiveProfs = useMemo(
    () => professors?.some(p => p.is_active_teacher) ?? false,
    [professors]
  )

  const hasNextQuarterProfs = useMemo(
    () => professors?.some(p => p.teaching_next_quarter) ?? false,
    [professors]
  )

  const scheduledQuarter = useMemo(() => {
    for (const professor of professors ?? []) {
      if (!professor.teaching_next_quarter) continue
      const name = professor.scheduled_sections?.find((section) => section.quarter_name)?.quarter_name
      if (name) return name
    }
    return 'Next quarter'
  }, [professors])

  return (
    <div className={compact ? 'h-full overflow-y-auto px-3 py-3' : 'mx-auto max-w-3xl px-5 py-10'}>
      {!compact && (
        <header className="mb-8">
          <h1 className="font-heading text-3xl font-semibold tracking-tight">
            {courseCode || 'Course results'}
          </h1>
          {courseTitle && <p className="mt-1 text-muted-foreground">{courseTitle}</p>}
          <p className="mt-3 max-w-[62ch] text-sm leading-relaxed text-muted-foreground">
            A 0–100 score from UCSB grades and RateMyProfessors. Missing reviews are left out.{' '}
            <Link to="/methodology" className="text-foreground underline-offset-2 hover:underline">
              How scoring works
            </Link>
          </p>
        </header>
      )}
      <div className="flex gap-6">
        <section className="min-w-0 flex-1" aria-label="Professor rankings">
          {error ? (
            <div className="py-12 text-center" role="alert">
              <p className="font-semibold">
                We could not load professors for this course.
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                Something went wrong on our end. You can try again.
              </p>
              <Button
                type="button"
                variant="outline"
                className="mt-4 min-h-[44px]"
                onClick={() => refetch()}
              >
                Try again
              </Button>
            </div>
          ) : isLoading ? (
            <>
              {showColdStart && (
                <div className="mb-4 rounded-lg border border-border bg-muted px-3 py-2.5 text-sm text-muted-foreground">
                  Waking up the server. This can take 15–30 seconds.
                </div>
              )}
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </>
          ) : rankedProfessors.length === 0 ? (
            <div className="py-12 text-center">
              <p className="font-semibold">No professors found for this course</p>
              <p className="text-sm text-muted-foreground">
                Grade and RMP data may not be available yet for this course.
              </p>
            </div>
          ) : (
            <>
            {quarterFilter === 'next' && !hasNextQuarterProfs && (
              <div className="mb-4 rounded-lg border border-border bg-muted px-3 py-2.5 text-sm text-muted-foreground">
                No professors are scheduled for {scheduledQuarter} yet. Showing all professors.
              </div>
            )}
            {showActiveOnly && !hasActiveProfs && rankedProfessors.length > 0 && (
              <div className="mb-4 rounded-lg border border-border bg-muted px-3 py-2.5 text-sm text-muted-foreground">
                No professors have taught this course recently. Showing all professors.
              </div>
            )}
            {rankedProfessors.map((prof, index) => (
              <ProfessorCard
                key={prof.id}
                professor={prof}
                score={prof.computedScore}
                courseId={numericCourseId}
                index={index}
              />
            ))}
            </>
          )}
          {!isLoading && !error && <CourseSections courseId={numericCourseId} />}
        </section>

        <aside className={compact ? 'hidden' : 'hidden w-64 shrink-0 md:block'}>
          <div className="sticky top-20 space-y-6 rounded-xl border border-border bg-muted/40 p-4">
            <QuarterFilterButtons
              value={quarterFilter}
              onChange={changeQuarter}
              scheduledQuarter={scheduledQuarter}
            />
            <ActiveTeacherFilter
              checked={showActiveOnly}
              onCheckedChange={setShowActiveOnly}
            />
            <WeightToggles weights={weights} onWeightsChange={setWeights} />
          </div>
        </aside>
      </div>

      {compact && (
        <div className="mt-4 space-y-4">
          <QuarterFilterButtons
            value={quarterFilter}
            onChange={changeQuarter}
            scheduledQuarter={scheduledQuarter}
          />
          <ActiveTeacherFilter
            checked={showActiveOnly}
            onCheckedChange={setShowActiveOnly}
          />
          <details className="rounded-xl border border-border bg-muted/40 p-3">
            <summary className="cursor-pointer text-sm font-medium">Customize ranking</summary>
            <div className="mt-3">
              <WeightToggles weights={weights} onWeightsChange={setWeights} />
            </div>
          </details>
        </div>
      )}

      <div className={compact ? 'hidden' : 'mt-4 md:hidden'}>
        <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
          <SheetTrigger asChild>
            <Button variant="outline" className="w-full min-h-[44px]">
              Customize ranking
            </Button>
          </SheetTrigger>
          <SheetContent side="bottom" className="px-6 pb-8">
            <SheetHeader>
              <SheetTitle>Customize ranking</SheetTitle>
            </SheetHeader>
            <div className="mt-4 space-y-6">
              <QuarterFilterButtons
                value={quarterFilter}
                onChange={changeQuarter}
                scheduledQuarter={scheduledQuarter}
              />
              <ActiveTeacherFilter
                checked={showActiveOnly}
                onCheckedChange={setShowActiveOnly}
              />
              <WeightToggles weights={weights} onWeightsChange={setWeights} />
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </div>
  )
}
