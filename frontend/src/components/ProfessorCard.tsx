import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import type { ProfessorRanking } from '@/types/api'
import { GradeChart } from './GradeChart'
import { GpaTrendChart } from './GpaTrendChart'
import { SentimentBadge } from './SentimentBadge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useProfessorGrades } from '@/hooks/useProfessorGrades'
import { useProfessorComments } from '@/hooks/useProfessorComments'

interface ProfessorCardProps {
  professor: ProfessorRanking
  score: number
  courseId: number
}

function scoreColorClass(score: number): string {
  if (score >= 70) return 'bg-green-600 text-white hover:bg-green-600'
  if (score >= 50) return 'bg-yellow-600 text-white hover:bg-yellow-600'
  return 'bg-red-600 text-white hover:bg-red-600'
}

function ExpandedCharts({ professorId, courseId }: { professorId: number; courseId: number }) {
  const { data: grades, isLoading } = useProfessorGrades(professorId, courseId)
  const [selectedQuarter, setSelectedQuarter] = useState<string>('most-recent')

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading charts...</p>
  if (!grades || grades.length === 0) return <p className="text-sm text-muted-foreground">No grade data available</p>

  const quarterOptions = [...grades].reverse().map(q => q.quarter)

  return (
    <div className="space-y-4">
      <div>
        <div className="mb-2 flex items-center justify-between">
          <Select value={selectedQuarter} onValueChange={setSelectedQuarter}>
            <SelectTrigger className="w-[200px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="most-recent">Most Recent</SelectItem>
              <SelectItem value="all">All Quarters Combined</SelectItem>
              {quarterOptions.map(q => (
                <SelectItem key={q} value={q}>{q}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <GradeChart quarters={grades} selectedQuarter={selectedQuarter} />
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

function QuartersList({ quarters }: { quarters: string[] }) {
  const [isOpen, setIsOpen] = useState(false)
  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger className="mt-2 flex min-h-[44px] items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        Quarters Taught ({quarters.length})
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="mt-1 flex flex-wrap gap-1">
          {quarters.map((q) => (
            <Badge key={q} variant="outline" className="text-xs">
              {q}
            </Badge>
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}

export function ProfessorCard({ professor, score, courseId }: ProfessorCardProps) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <Card className="mb-6">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <h3 className="text-xl font-semibold leading-tight">{professor.name}</h3>
            {professor.is_active_teacher && (
              <Badge className="bg-primary text-primary-foreground hover:bg-primary text-xs px-2 py-0.5 rounded-full whitespace-nowrap">
                Actively Teaching
              </Badge>
            )}
          </div>
          <Badge className={`${scoreColorClass(score)} text-sm font-bold px-2.5 py-1 rounded-full`}>{score}</Badge>
        </div>
        <p className="mt-1 text-sm">
          Avg GPA: {professor.mean_gpa !== null ? professor.mean_gpa.toFixed(2) : 'N/A'}
        </p>
        <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm">
          <span>Quality: {professor.rmp_quality !== null ? professor.rmp_quality.toFixed(1) : 'N/A'}</span>
          <span>Difficulty: {professor.rmp_difficulty !== null ? professor.rmp_difficulty.toFixed(1) : 'N/A'}</span>
          <span>Would take again: {professor.rmp_would_take_again !== null ? `${professor.rmp_would_take_again.toFixed(0)}%` : 'N/A'}</span>
        </div>
        {professor.tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {professor.tags.slice(0, 6).map((tag) => (
              <Badge
                key={tag.name}
                variant="secondary"
                className="text-xs"
                title={`${tag.name} \u2014 ${tag.count} reviews`}
              >
                {tag.name}
              </Badge>
            ))}
          </div>
        )}
        {professor.recent_quarters.length > 0 && (
          <QuartersList quarters={professor.recent_quarters} />
        )}
        <Collapsible open={isOpen} onOpenChange={setIsOpen}>
          <CollapsibleTrigger className="mt-3 flex min-h-[44px] items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
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
