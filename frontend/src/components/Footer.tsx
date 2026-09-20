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
    <footer className="border-t border-primary/10 bg-background">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-6 text-sm text-muted-foreground md:flex-row md:items-center md:justify-between">
        <p>
          Rankings combine official UCSB grade distributions
          {gradeTerm ? ` through ${gradeTerm}` : ''}
          {' '}with RateMyProfessors reviews. Missing reviews are left out of the
          score instead of counted as average.
          {scheduleDate ? ` Schedule last refreshed ${scheduleDate}.` : ''}
        </p>
        <nav aria-label="Footer" className="flex shrink-0 gap-4">
          <Link to="/methodology" className="focusable rounded-sm text-primary hover:underline">
            Methodology
          </Link>
          <a
            href="https://www.ratemyprofessors.com"
            className="focusable rounded-sm text-primary hover:underline"
            rel="noreferrer"
          >
            RateMyProfessors
          </a>
        </nav>
      </div>
    </footer>
  )
}
