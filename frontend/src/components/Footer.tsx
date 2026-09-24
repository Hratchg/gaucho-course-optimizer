import { Link } from 'react-router-dom'
import { useFreshness } from '@/hooks/useFreshness'

function formatFetchedAt(value: string | null): string | null {
  if (!value) return null
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return null
  return parsed.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'America/Los_Angeles',
  })
}

export function Footer() {
  const { data } = useFreshness()
  const gradeTerm = data?.latest_grade_year
    ? `${data.latest_grade_quarter ?? ''} ${data.latest_grade_year}`.trim()
    : null
  const scheduleDate = formatFetchedAt(data?.schedule_fetched_at ?? null)

  return (
    <footer className="border-t border-border/70 text-foreground">
      <div className="mx-auto flex max-w-2xl flex-col gap-4 px-5 py-8 text-sm md:flex-row md:items-start md:justify-between">
        <p className="max-w-[46ch] leading-relaxed text-muted-foreground">
          Rankings combine official UCSB grade distributions
          {gradeTerm ? ` through ${gradeTerm}` : ''}
          {' '}with RateMyProfessors reviews. Missing reviews are left out of the
          score instead of counted as average.
          {scheduleDate ? ` Schedule last refreshed ${scheduleDate}.` : ''}
        </p>
        <nav aria-label="Footer" className="flex shrink-0 gap-4">
          <Link to="/methodology" className="focusable rounded-sm text-muted-foreground hover:text-foreground">
            Methodology
          </Link>
          <a
            href="https://www.ratemyprofessors.com"
            className="focusable rounded-sm text-muted-foreground hover:text-foreground"
            rel="noreferrer"
          >
            RateMyProfessors
          </a>
        </nav>
      </div>
    </footer>
  )
}
