import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import type { ProfessorRanking } from '@/types/api'

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
            <div className="mt-4 text-sm text-muted-foreground">
              Details loading...
            </div>
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  )
}
