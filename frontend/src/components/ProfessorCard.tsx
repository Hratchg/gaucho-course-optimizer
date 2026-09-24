import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import type { ProfessorRanking, ScheduledSection } from '@/types/api'
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
  index?: number
}

function scoreColorClass(score: number): string {
  if (score >= 70) return 'bg-primary text-primary-foreground hover:bg-primary'
  if (score >= 50) return 'bg-brand-oak text-white hover:bg-brand-oak'
  return 'bg-muted text-muted-foreground hover:bg-muted'
}

function formatTime(time: string | null): string {
  if (!time) return ''
  // Convert "14:00" to "2:00 PM"
  const [h, m] = time.split(':').map(Number)
  const period = h >= 12 ? 'PM' : 'AM'
  const hour12 = h % 12 || 12
  return `${hour12}:${m.toString().padStart(2, '0')} ${period}`
}

function formatDays(days: string | null): string {
  return (days ?? '').replace(/\s+/g, '')
}

function sectionLine(section: ScheduledSection): string {
  const when = section.days && section.begin_time
    ? `${formatDays(section.days)} ${formatTime(section.begin_time)}${section.end_time ? `–${formatTime(section.end_time)}` : ''}`
    : ''
  const where = section.building && section.room ? `${section.building} ${section.room}` : section.building ?? ''
  const seats = section.enrolled != null && section.max_enroll != null
    ? `${section.enrolled} of ${section.max_enroll}`
    : ''
  return [when, where, seats].filter(Boolean).join(', ')
}

function MeetingLines({ sections }: { sections: ScheduledSection[] }) {
  if (sections.length === 0) return null
  const quarter = sections.find((section) => section.quarter_name)?.quarter_name

  return (
    <div className="mt-2">
      {quarter && <p className="text-sm text-muted-foreground">{quarter}</p>}
      <ul className="mt-0.5 space-y-0.5">
        {sections.map((section) => (
          <li key={section.enroll_code} className="text-sm text-foreground">
            {sectionLine(section)}
          </li>
        ))}
      </ul>
    </div>
  )
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
      <CollapsibleTrigger
        aria-label={`${isOpen ? 'Hide' : 'Show'} quarters taught`}
        className="focusable rounded-sm mt-2 flex min-h-[44px] items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        Quarters Taught ({quarters.length})
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="mt-1 flex flex-wrap gap-1">
          {quarters.map((q) => (
            <Badge key={q} variant="outline" className="text-xs border-primary/30">
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
    <Card
      className="mb-3 shadow-none ring-1 ring-border"
    >
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-xl font-semibold leading-tight">{professor.name}</h3>
            {professor.is_active_teacher && (
              <Badge className="bg-primary text-primary-foreground hover:bg-primary text-xs px-2 py-0.5 rounded-full whitespace-nowrap">
                Taught recently
              </Badge>
            )}
            {professor.teaching_next_quarter && (professor.scheduled_sections?.length ?? 0) === 0 && (
              <Badge
                variant="outline"
                className="border-primary text-primary hover:bg-primary/10 text-xs px-2 py-0.5 rounded-full whitespace-nowrap"
              >
                Next quarter
              </Badge>
            )}
            {!professor.has_rmp && (
              <Badge
                variant="outline"
                className="text-xs px-2 py-0.5 rounded-full whitespace-nowrap"
              >
                GPA only
              </Badge>
            )}
          </div>
          <Badge
            className={`${scoreColorClass(score)} text-sm font-bold px-2.5 py-1 rounded-full`}
            aria-label={`Gaucho Score: ${score}`}
          >
            {score}
          </Badge>
        </div>
        {professor.mean_gpa !== null && (
          <p className="mt-1 text-sm">Avg GPA: {professor.mean_gpa.toFixed(2)}</p>
        )}
        {(professor.rmp_quality !== null || professor.rmp_difficulty !== null || professor.rmp_would_take_again !== null) && (
          <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm">
            {professor.rmp_quality !== null && <span>Quality: {professor.rmp_quality.toFixed(1)}</span>}
            {professor.rmp_difficulty !== null && <span>Difficulty: {professor.rmp_difficulty.toFixed(1)}</span>}
            {professor.rmp_would_take_again !== null && (
              <span>Would take again: {professor.rmp_would_take_again.toFixed(0)}%</span>
            )}
          </div>
        )}
        {professor.tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {professor.tags.slice(0, 6).map((tag) => (
              <Badge
                key={tag.name}
                variant="secondary"
                className="text-xs bg-primary/10 text-primary hover:bg-primary/15"
                title={`${tag.name} \u2014 ${tag.count} reviews`}
              >
                {tag.name}
              </Badge>
            ))}
          </div>
        )}
        {(professor.scheduled_sections?.length ?? 0) > 0 && (
          <MeetingLines sections={professor.scheduled_sections} />
        )}
        {professor.recent_quarters.length > 0 && (
          <QuartersList quarters={professor.recent_quarters} />
        )}
        <Collapsible open={isOpen} onOpenChange={setIsOpen}>
          <CollapsibleTrigger
            aria-label={`${isOpen ? 'Hide' : 'Show'} professor details`}
            className="focusable rounded-sm mt-3 flex min-h-[44px] items-center gap-1 text-sm text-primary hover:text-primary/80 transition-colors"
          >
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
