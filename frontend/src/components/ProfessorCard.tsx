import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import type { ProfessorRanking } from '@/types/api'
import { GradeChart } from './GradeChart'
import { GpaTrendChart } from './GpaTrendChart'
import { SentimentBadge } from './SentimentBadge'
import { useProfessorGrades } from '@/hooks/useProfessorGrades'
import { useProfessorComments } from '@/hooks/useProfessorComments'

interface ProfessorCardProps {
  professor: ProfessorRanking
  score: number
  courseId: number
}

function scoreBorderClass(score: number): string {
  if (score >= 70) return 'border-l-4 border-l-green-500'
  if (score >= 50) return 'border-l-4 border-l-yellow-500'
  return 'border-l-4 border-l-red-500'
}

function ExpandedCharts({ professorId, courseId }: { professorId: number; courseId: number }) {
  const { data: grades, isLoading } = useProfessorGrades(professorId, courseId)
  if (isLoading) return <p className="text-sm text-muted-foreground">Loading charts...</p>
  if (!grades || grades.length === 0) return <p className="text-sm text-muted-foreground">No grade data available</p>
  return (
    <div className="space-y-4">
      <div>
        <h4 className="mb-2 text-sm font-semibold">Grade Distribution</h4>
        <GradeChart quarters={grades} />
      </div>
      <div>
        <h4 className="mb-2 text-sm font-semibold">GPA Trend</h4>
        <GpaTrendChart quarters={grades} />
      </div>
    </div>
  )
}

function ExpandedComments({ professorId }: { professorId: number }) {
  const { data: comments, isLoading } = useProfessorComments(professorId)
  if (isLoading) return <p className="text-sm text-muted-foreground">Loading comments...</p>
  if (!comments || comments.length === 0) return <p className="text-sm text-muted-foreground">No comments found for this professor.</p>
  return (
    <div>
      <h4 className="mb-2 text-sm font-semibold">Recent Comments</h4>
      <div className="space-y-3">
        {comments.map((comment, i) => (
          <div key={i} className="border-b pb-3 last:border-b-0">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">{comment.created_at ?? 'Unknown date'}</span>
              <SentimentBadge score={comment.sentiment_score} />
            </div>
            <p className="mt-1 text-sm leading-relaxed">{comment.text ?? 'No comment text'}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export function ProfessorCard({ professor, score, courseId }: ProfessorCardProps) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <Card className={`${scoreBorderClass(score)} mb-6`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <h3 className="text-xl font-semibold leading-tight">{professor.name}</h3>
          <span className="text-[28px] font-semibold leading-none">{score}</span>
        </div>
        <p className="mt-1 text-sm">
          Avg GPA: {professor.mean_gpa !== null ? professor.mean_gpa.toFixed(2) : 'N/A'}
        </p>
        <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm">
          <span>Quality: {professor.rmp_quality !== null ? professor.rmp_quality.toFixed(1) : 'N/A'}</span>
          <span>Difficulty: {professor.rmp_difficulty !== null ? professor.rmp_difficulty.toFixed(1) : 'N/A'}</span>
          <span>Would take again: {professor.rmp_would_take_again !== null ? `${professor.rmp_would_take_again.toFixed(0)}%` : 'N/A'}</span>
        </div>
        {professor.keywords.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {professor.keywords.slice(0, 6).map((kw) => (
              <Badge key={kw} variant="secondary" className="text-xs">{kw}</Badge>
            ))}
          </div>
        )}
        <Collapsible open={isOpen} onOpenChange={setIsOpen}>
          <CollapsibleTrigger className="mt-3 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
            {isOpen ? (
              <><ChevronUp className="h-4 w-4" /> Hide details</>
            ) : (
              <><ChevronDown className="h-4 w-4" /> Show details</>
            )}
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="mt-4 space-y-6">
              <ExpandedCharts professorId={professor.id} courseId={courseId} />
              <ExpandedComments professorId={professor.id} />
            </div>
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  )
}
