import { useParams } from 'react-router-dom'
import { useMemo } from 'react'
import { useProfessors } from '@/hooks/useProfessors'
import { ProfessorCard } from '@/components/ProfessorCard'
import { computeGauchoScore, DEFAULT_WEIGHTS } from '@/lib/scoring'
import type { Weights } from '@/lib/scoring'

export default function CoursePage() {
  const { courseId } = useParams<{ courseId: string }>()
  const numericCourseId = Number(courseId)
  const { data: professors, isLoading, error } = useProfessors(numericCourseId)

  const weights: Weights = DEFAULT_WEIGHTS

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

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12 text-center">
        <p className="font-semibold">Could not load professors. Check your connection and try refreshing.</p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12">
        <p>Loading...</p>
      </div>
    )
  }

  if (rankedProfessors.length === 0) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12 text-center">
        <p className="font-semibold">No professors found for this course</p>
        <p className="text-sm text-muted-foreground">
          Grade and RMP data may not be available yet for this course.
        </p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-6">
      {rankedProfessors.map((prof) => (
        <ProfessorCard
          key={prof.id}
          professor={prof}
          score={prof.computedScore}
          courseId={numericCourseId}
        />
      ))}
    </div>
  )
}
