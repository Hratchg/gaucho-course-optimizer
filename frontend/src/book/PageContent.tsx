import { Link } from 'react-router-dom'
import { WeightToggles } from '@/components/WeightToggles'
import { GradeChart } from '@/components/GradeChart'
import { useProfessorGrades } from '@/hooks/useProfessorGrades'
import type { ToggleWeights } from '@/lib/scoring'
import type { PageDef, RankedProfessor } from './paginate'

export const PAGE_PX_W = 420
export const PAGE_PX_H = 560

interface PageContentProps {
  page: PageDef
  side: 'left' | 'right'
  courseId: number
  weights: ToggleWeights
  onWeightsChange: (w: ToggleWeights) => void
}

function ScorePill({ score }: { score: number }) {
  return (
    <span className="inline-flex shrink-0 items-center rounded-full bg-brand-gold px-2.5 py-0.5 text-sm font-bold text-brand-ink">
      {score}
    </span>
  )
}

function CondensedProfessor({ prof, rank, courseId }: { prof: RankedProfessor; rank: number; courseId: number }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-brand-gold/30 bg-[#efe5cb] px-3 py-2.5">
      <span className="w-6 shrink-0 text-right font-display text-lg font-bold text-brand-burgundy">{rank}</span>
      <div className="min-w-0 flex-1">
        <p className="truncate font-display text-base font-semibold text-brand-ink">{prof.name}</p>
        <p className="truncate text-xs text-[#5a4f3a]">
          {prof.mean_gpa != null ? `GPA ${prof.mean_gpa.toFixed(2)}` : 'GPA —'}
          {prof.rmp_quality != null ? ` · RMP ${prof.rmp_quality.toFixed(1)}` : ''}
          {prof.teaching_next_quarter ? ' · next qtr' : prof.is_active_teacher ? ' · active' : ''}
        </p>
      </div>
      <ScorePill score={prof.computedScore} />
      <Link
        to={`/courses/${courseId}?classic=1`}
        className="focusable shrink-0 text-xs text-brand-burgundy underline-offset-2 hover:underline"
        aria-label={`Full details for ${prof.name} in classic view`}
      >
        details
      </Link>
    </div>
  )
}

function OverviewGradeChart({ professorId, courseId }: { professorId: number; courseId: number }) {
  const { data: grades } = useProfessorGrades(professorId, courseId)
  if (!grades || grades.length === 0) return null
  return (
    <div className="mt-2 h-40">
      <GradeChart quarters={grades} selectedQuarter="all" />
    </div>
  )
}

/** One parchment page of the open book, rendered as real DOM inside drei Html. */
export default function PageContent({ page, side, courseId, weights, onWeightsChange }: PageContentProps) {
  return (
    <div
      style={{ width: PAGE_PX_W, height: PAGE_PX_H }}
      className={`flex select-none flex-col overflow-hidden bg-transparent px-7 py-6 text-brand-ink ${
        side === 'left' ? 'pr-8' : 'pl-8'
      }`}
    >
      {page.kind === 'overview' && (
        <>
          <p className="font-script text-xl text-brand-burgundy">this quarter&rsquo;s pick</p>
          <h2 className="mt-0.5 font-display text-3xl font-black leading-tight">
            {page.courseCode ?? 'Course'}
          </h2>
          {page.courseTitle && (
            <p className="mt-1 font-display text-base text-[#5a4f3a]">{page.courseTitle}</p>
          )}
          <div className="my-3 h-0.5 w-full bg-brand-gold/70" />
          <dl className="space-y-1.5 text-sm">
            <div className="flex justify-between">
              <dt className="text-[#5a4f3a]">Professors ranked</dt>
              <dd className="font-semibold">{page.professorCount}</dd>
            </div>
            {page.avgGpa != null && (
              <div className="flex justify-between">
                <dt className="text-[#5a4f3a]">Average GPA</dt>
                <dd className="font-semibold">{page.avgGpa.toFixed(2)}</dd>
              </div>
            )}
            {page.topProfessorName && (
              <div className="flex justify-between">
                <dt className="text-[#5a4f3a]">Top pick</dt>
                <dd className="flex items-center gap-2 font-semibold">
                  {page.topProfessorName}
                  {page.topProfessorScore != null && <ScorePill score={page.topProfessorScore} />}
                </dd>
              </div>
            )}
          </dl>
          {page.topProfessorId != null && (
            <OverviewGradeChart professorId={page.topProfessorId} courseId={courseId} />
          )}
          <p className="mt-auto text-xs text-[#8a8064]">
            Flip the pages for the full ranking →
          </p>
        </>
      )}

      {page.kind === 'settings' && (
        <>
          <h2 className="font-display text-2xl font-black">Reader&rsquo;s settings</h2>
          <p className="mb-4 mt-1 text-sm text-[#5a4f3a]">
            Choose what matters to you — the ranking on the next pages updates instantly.
          </p>
          <WeightToggles weights={weights} onWeightsChange={onWeightsChange} />
          <p className="mt-auto text-xs text-[#8a8064]">
            Prefer the classic layout?{' '}
            <Link to={`/courses/${courseId}?classic=1`} className="focusable text-brand-burgundy underline">
              Open classic view
            </Link>
          </p>
        </>
      )}

      {page.kind === 'professors' && (
        <>
          <h2 className="font-display text-xl font-black">
            Professors {page.startRank}–{page.startRank + page.professors.length - 1}
          </h2>
          <div className="mt-3 space-y-2.5">
            {page.professors.map((prof, i) => (
              <CondensedProfessor key={prof.id} prof={prof} rank={page.startRank + i} courseId={courseId} />
            ))}
          </div>
        </>
      )}

      {page.kind === 'blank' && <div aria-hidden className="flex-1" />}
    </div>
  )
}
