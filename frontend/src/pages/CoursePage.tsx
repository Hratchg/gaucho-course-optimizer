import { useParams } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import { useProfessors } from '@/hooks/useProfessors'
import { ProfessorCard } from '@/components/ProfessorCard'
import { SkeletonCard } from '@/components/SkeletonCard'
import { WeightToggles } from '@/components/WeightToggles'
import { computeGauchoScore, DEFAULT_TOGGLE_WEIGHTS } from '@/lib/scoring'
import type { ToggleWeights } from '@/lib/scoring'
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
        Show only active teachers
      </label>
    </div>
  )
}

function QuarterFilterButtons({
  value,
  onChange,
}: {
  value: QuarterFilter
  onChange: (v: QuarterFilter) => void
}) {
  const options: { label: string; value: QuarterFilter }[] = [
    { label: 'All', value: 'all' },
    { label: 'Next Quarter', value: 'next' },
    { label: 'Current', value: 'current' },
  ]

  return (
    <div>
      <p className="mb-2 text-sm font-medium">Quarter Filter</p>
      <div className="flex gap-1">
        {options.map((opt) => (
          <Button
            key={opt.value}
            variant={value === opt.value ? 'default' : 'outline'}
            size="sm"
            className="flex-1 text-xs min-h-[36px]"
            onClick={() => onChange(opt.value)}
            aria-pressed={value === opt.value}
          >
            {opt.label}
          </Button>
        ))}
      </div>
    </div>
  )
}

export default function CoursePage() {
  const { courseId } = useParams<{ courseId: string }>()
  const numericCourseId = Number(courseId)
  const { data: professors, isLoading, error } = useProfessors(numericCourseId)

  const [weights, setWeights] = useState<ToggleWeights>(DEFAULT_TOGGLE_WEIGHTS)
  const [sheetOpen, setSheetOpen] = useState(false)
  const [showActiveOnly, setShowActiveOnly] = useState(false)
  const [quarterFilter, setQuarterFilter] = useState<QuarterFilter>('all')
  const showColdStart = useColdStartMessage(isLoading)

  useEffect(() => {
    document.title = 'Course Results | CoursePick'
  }, [])

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

  return (
    <div className="mx-auto max-w-5xl px-4 py-6">
      {/* Mobile: "Adjust weights" button + bottom Sheet */}
      <div className="mb-4 md:hidden">
        <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
          <SheetTrigger asChild>
            <Button variant="outline" className="w-full min-h-[44px]">
              Customize Ranking
            </Button>
          </SheetTrigger>
          <SheetContent side="bottom" className="px-6 pb-8">
            <SheetHeader>
              <SheetTitle>Customize Ranking</SheetTitle>
            </SheetHeader>
            <div className="mt-4 space-y-6">
              <QuarterFilterButtons value={quarterFilter} onChange={setQuarterFilter} />
              <ActiveTeacherFilter
                checked={showActiveOnly}
                onCheckedChange={setShowActiveOnly}
              />
              <WeightToggles weights={weights} onWeightsChange={setWeights} />
            </div>
          </SheetContent>
        </Sheet>
      </div>

      {/* Desktop: two-column layout */}
      <div className="flex gap-6">
        {/* Left sidebar -- desktop only, sticky */}
        <aside className="hidden w-64 shrink-0 md:block">
          <div className="sticky top-20 space-y-6 rounded-lg border border-primary/20 p-4">
            <QuarterFilterButtons value={quarterFilter} onChange={setQuarterFilter} />
            <ActiveTeacherFilter
              checked={showActiveOnly}
              onCheckedChange={setShowActiveOnly}
            />
            <WeightToggles weights={weights} onWeightsChange={setWeights} />
          </div>
        </aside>

        {/* Main content: professor cards */}
        <section className="min-w-0 flex-1" aria-label="Professor rankings">
          {error ? (
            <div className="py-12 text-center">
              <p className="font-semibold">
                Could not load professors. Check your connection and try refreshing.
              </p>
            </div>
          ) : isLoading ? (
            <>
              {showColdStart && (
                <div className="mb-4 rounded-lg border border-primary/30 bg-primary/5 p-3 text-sm text-primary">
                  Waking up the server... free-tier cold start may take 15-30 seconds.
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
              <div className="mb-4 rounded-lg border border-primary/20 bg-primary/5 p-3 text-sm text-primary">
                No professors are scheduled for next quarter yet. Showing all professors.
              </div>
            )}
            {showActiveOnly && !hasActiveProfs && rankedProfessors.length > 0 && (
              <div className="mb-4 rounded-lg border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-800">
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
        </section>
      </div>
    </div>
  )
}
