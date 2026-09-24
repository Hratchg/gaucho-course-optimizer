import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { useCourseSections } from '@/hooks/useCourseSections'
import type { ScheduledSection } from '@/types/api'

function formatTime(begin: string | null, end: string | null): string {
  if (!begin) return ''
  const fmt = (t: string) => {
    const [h, m] = t.split(':').map(Number)
    const suffix = h >= 12 ? 'PM' : 'AM'
    const hour = h > 12 ? h - 12 : h === 0 ? 12 : h
    return `${hour}:${m.toString().padStart(2, '0')} ${suffix}`
  }
  return end ? `${fmt(begin)}–${fmt(end)}` : fmt(begin)
}

function SectionRow({ section }: { section: ScheduledSection }) {
  const enrollment = section.enrolled != null && section.max_enroll != null
    ? `${section.enrolled}/${section.max_enroll}`
    : null

  return (
    <tr className="border-b border-border/50 last:border-0">
      <td className="py-2 pr-3 text-sm">{section.instructor_name_raw}</td>
      <td className="py-2 pr-3 text-sm whitespace-nowrap">{section.days?.trim()}</td>
      <td className="py-2 pr-3 text-sm whitespace-nowrap">{formatTime(section.begin_time, section.end_time)}</td>
      <td className="py-2 pr-3 text-sm whitespace-nowrap">
        {section.building && section.room ? `${section.building} ${section.room}` : section.building || ''}
      </td>
      {enrollment && <td className="py-2 text-sm whitespace-nowrap">{enrollment}</td>}
    </tr>
  )
}

export function CourseSections({ courseId }: { courseId: number }) {
  const { data: sections, isLoading } = useCourseSections(courseId)
  const [isOpen, setIsOpen] = useState(false)

  if (isLoading || !sections || sections.length === 0) return null

  // Group by quarter
  const grouped = new Map<string, ScheduledSection[]>()
  for (const s of sections) {
    const key = s.quarter_name || s.quarter_code
    if (!grouped.has(key)) grouped.set(key, [])
    grouped.get(key)!.push(s)
  }

  const hasEnrollment = sections.some(s => s.enrolled != null && s.max_enroll != null)

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className="mb-6 rounded-lg border border-primary/20 bg-card">
      <CollapsibleTrigger className="flex w-full items-center justify-between p-4 text-left hover:bg-accent/50 transition-colors rounded-lg">
        <div className="flex items-center gap-2">
          <h2 className="text-base font-semibold">Scheduled Sections</h2>
          <span className="text-xs text-muted-foreground">({sections.length})</span>
        </div>
        {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="px-4 pb-4">
          {[...grouped.entries()].map(([quarter, quarterSections]) => (
            <div key={quarter} className="mb-4 last:mb-0">
              <h3 className="mb-2 text-sm font-medium text-primary">{quarter}</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border text-left">
                      <th className="pb-1.5 pr-3 text-xs font-medium text-muted-foreground">Instructor</th>
                      <th className="pb-1.5 pr-3 text-xs font-medium text-muted-foreground">Days</th>
                      <th className="pb-1.5 pr-3 text-xs font-medium text-muted-foreground">Time</th>
                      <th className="pb-1.5 pr-3 text-xs font-medium text-muted-foreground">Location</th>
                      {hasEnrollment && <th className="pb-1.5 text-xs font-medium text-muted-foreground">Enrolled</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {quarterSections.map((s) => (
                      <SectionRow key={s.enroll_code} section={s} />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}
