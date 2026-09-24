import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { ChevronDown, ChevronUp, Clock, MapPin, Users } from 'lucide-react'
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

function SectionDetails({ sections }: { sections: ScheduledSection[] }) {
  const [isOpen, setIsOpen] = useState(false)

  if (sections.length === 0) return null

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger
        aria-label={`${isOpen ? 'Hide' : 'Show'} section details`}
        className="focusable rounded-sm mt-2 flex min-h-[44px] items-center gap-1 text-sm text-primary hover:text-primary/80 transition-colors"
      >
        {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        View {sections.length === 1 ? 'Section' : `${sections.length} Sections`}
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="mt-2 space-y-2">
          {sections.map((section) => (
            <div
              key={section.enroll_code}
              className="rounded-md border border-primary/20 bg-primary/5 p-3 text-sm"
            >
              <div className="flex flex-wrap gap-x-4 gap-y-1">
                {section.days && section.begin_time && section.end_time && (
                  <span className="flex items-center gap-1 text-foreground">
                    <Clock className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                    {section.days} {formatTime(section.begin_time)}-{formatTime(section.end_time)}
                  </span>
                )}
                {section.building && section.room && (
                  <span className="flex items-center gap-1 text-foreground">
                    <MapPin className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                    {section.building} {section.room}
                  </span>
                )}
                {section.enrolled != null && section.max_enroll != null && (
                  <span className="flex items-center gap-1 text-foreground">
                    <Users className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                    {section.enrolled}/{section.max_enroll} enrolled
                  </span>
                )}
              </div>
              <div className="mt-1 text-xs text-muted-foreground">
                Enroll Code: {section.enroll_code}
                {section.quarter_name && ` \u2022 ${section.quarter_name}`}
              </div>
            </div>
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
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

export function ProfessorCard({ professor, score, courseId, index = 0 }: ProfessorCardProps) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <Card
      className="mb-3 stagger-in shadow-none ring-1 ring-border"
      style={{ '--stagger-delay': `${index * 40}ms` } as React.CSSProperties}
    >
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-xl font-semibold leading-tight">{professor.name}</h3>
            {professor.is_active_teacher && (
              <Badge className="bg-primary text-primary-foreground hover:bg-primary text-xs px-2 py-0.5 rounded-full whitespace-nowrap">
                Actively Teaching
              </Badge>
            )}
            {professor.teaching_next_quarter && (
              <Badge
                variant="outline"
                className="border-primary text-primary hover:bg-primary/10 text-xs px-2 py-0.5 rounded-full whitespace-nowrap"
              >
                Teaching Next Quarter
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
        {professor.teaching_next_quarter && professor.scheduled_sections.length > 0 && (
          <SectionDetails sections={professor.scheduled_sections} />
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
