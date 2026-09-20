import { Link } from 'react-router-dom'
import { useFreshness } from '@/hooks/useFreshness'
import BrandWordmark from '@/components/BrandWordmark'

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
    <footer className="bg-[oklch(0.206_0.039_289.4)] text-white">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-8 text-sm md:flex-row md:items-center md:justify-between">
        <div className="flex flex-col gap-3 md:max-w-2xl">
          <BrandWordmark className="text-lg" />
          <p className="text-[oklch(0.781_0.041_294.9)]">
            Rankings combine official UCSB grade distributions
            {gradeTerm ? ` through ${gradeTerm}` : ''}
            {' '}with RateMyProfessors reviews. Missing reviews are left out of the
            score instead of counted as average.
            {scheduleDate ? ` Schedule last refreshed ${scheduleDate}.` : ''}
          </p>
        </div>
        <nav aria-label="Footer" className="flex shrink-0 gap-4">
          <Link to="/methodology" className="focusable rounded-sm text-brand-sun hover:underline">
            Methodology
          </Link>
          <a
            href="https://www.ratemyprofessors.com"
            className="focusable rounded-sm text-brand-sun hover:underline"
            rel="noreferrer"
          >
            RateMyProfessors
          </a>
        </nav>
      </div>
    </footer>
  )
}
