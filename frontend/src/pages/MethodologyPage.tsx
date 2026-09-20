import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useFreshness } from '@/hooks/useFreshness'

export default function MethodologyPage() {
  const { data } = useFreshness()

  useEffect(() => {
    document.title = 'Methodology | CoursePick'
  }, [])

  const gradeTerm = data?.latest_grade_year
    ? `${data.latest_grade_quarter ?? ''} ${data.latest_grade_year}`.trim()
    : 'the latest published UCSB term'

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-heading text-[28px] font-bold text-primary">How CoursePick ranks professors</h1>
      <p className="mt-4 text-muted-foreground">
        Gaucho Score is a 0–100 ranking for a professor in a specific UCSB course.
        It only uses the factors we actually have. A missing RateMyProfessors match
        is omitted, not treated as a 3.0 / 0.5 placeholder.
      </p>

      <h2 className="font-heading mt-10 text-xl font-bold">Sources</h2>
      <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed">
        <li>
          Official UCSB grade distributions through {gradeTerm}. These determine
          average GPA and the grade-history charts.
        </li>
        <li>
          RateMyProfessors quality, difficulty, would-take-again, and comments.
          Comments are scored with VADER sentiment and mapped onto tags.
        </li>
        <li>
          UCSB Curriculums API section listings for who is teaching the current
          and next quarter.
        </li>
      </ul>

      <h2 className="font-heading mt-10 text-xl font-bold">Matching</h2>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
        UCSB grade files and RateMyProfessors use different name formats. We only
        publish a match at 85% confidence or higher. Truncated Nexus surnames can
        still match when every fragment is a prefix of the RateMyProfessors name.
      </p>

      <h2 className="font-heading mt-10 text-xl font-bold">Scoring</h2>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
        GPA is scaled by 4.0. Quality is Bayesian-adjusted toward 3.0 when the
        sample is small, then scaled by 5. Difficulty is inverted so easier
        courses score higher. Sentiment maps VADER&apos;s −1…1 range onto 0…1.
        Enabled factors share the weight equally. You can change those weights
        on a course page.
      </p>

      <p className="mt-10 text-sm">
        <Link to="/search" className="text-primary hover:underline">Search a course</Link>
        {' '}to see the ranking applied.
      </p>
    </div>
  )
}
