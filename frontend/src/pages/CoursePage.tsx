import { useParams } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import { useProfessors } from '@/hooks/useProfessors'
import { ProfessorCard } from '@/components/ProfessorCard'
import { SkeletonCard } from '@/components/SkeletonCard'
import { WeightSliders } from '@/components/WeightSliders'
import { computeGauchoScore, DEFAULT_WEIGHTS } from '@/lib/scoring'
import type { Weights } from '@/lib/scoring'
import { useColdStartMessage } from '@/hooks/useElapsedTime'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'

export default function CoursePage() {
  const { courseId } = useParams<{ courseId: string }>()
  const numericCourseId = Number(courseId)
  const { data: professors, isLoading, error } = useProfessors(numericCourseId)

  const [weights, setWeights] = useState<Weights>(DEFAULT_WEIGHTS)
  const [sheetOpen, setSheetOpen] = useState(false)
  const showColdStart = useColdStartMessage(isLoading)

  useEffect(() => {
    document.title = 'Course Results | Gaucho Course Optimizer'
  }, [])

  const rankedProfessors = useMemo(() => {
    if (!professors) return []
    return [...professors]
      .map((p) => ({
        ...p,
        computedScore: computeGauchoScore(
          p.gpa_factor, p.quality_factor, p.difficulty_factor, p.sentiment_factor, weights
        ),
      }))
      .sort((a, b) => b.computedScore - a.computedScore)
  }, [professors, weights])

  return (
    <div className="mx-auto max-w-5xl px-4 py-6">
      {/* Mobile: "Adjust weights" button + bottom Sheet */}
      <div className="mb-4 md:hidden">
        <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
          <SheetTrigger asChild>
            <Button variant="outline" className="w-full min-h-[44px]">
              Adjust weights
            </Button>
          </SheetTrigger>
          <SheetContent side="bottom" className="px-6 pb-8">
            <SheetHeader>
              <SheetTitle>Adjust Weights</SheetTitle>
            </SheetHeader>
            <div className="mt-4">
              <WeightSliders weights={weights} onWeightsChange={setWeights} />
            </div>
          </SheetContent>
        </Sheet>
      </div>

      {/* Desktop: two-column layout */}
      <div className="flex gap-6">
        {/* Left sidebar -- desktop only, sticky */}
        <aside className="hidden w-64 shrink-0 md:block">
          <div className="sticky top-20">
            <WeightSliders weights={weights} onWeightsChange={setWeights} />
          </div>
        </aside>

        {/* Main content: professor cards */}
        <main className="min-w-0 flex-1">
          {error ? (
            <div className="py-12 text-center">
              <p className="font-semibold">
                Could not load professors. Check your connection and try refreshing.
              </p>
            </div>
          ) : isLoading ? (
            <>
              {showColdStart && (
                <div className="mb-4 rounded-lg border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-800">
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
            rankedProfessors.map((prof) => (
              <ProfessorCard
                key={prof.id}
                professor={prof}
                score={prof.computedScore}
                courseId={numericCourseId}
              />
            ))
          )}
        </main>
      </div>
    </div>
  )
}
