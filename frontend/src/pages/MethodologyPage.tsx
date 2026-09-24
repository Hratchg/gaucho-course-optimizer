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
    <article className="mx-auto max-w-2xl px-5 py-16">
      <h1 className="font-heading text-4xl font-semibold tracking-tight text-foreground">
        How CoursePick ranks professors
      </h1>
      <p className="mt-4 max-w-[62ch] text-base leading-relaxed text-muted-foreground">
        Gaucho Score is a 0–100 ranking for a professor in a specific UCSB course.
        It only uses the factors we actually have. A missing RateMyProfessors match
        is omitted, not treated as a 3.0 / 0.5 placeholder.
      </p>

      <section className="mt-12">
        <h2 className="font-heading text-xl font-semibold tracking-tight">Sources</h2>
        <ul className="mt-4 space-y-4 text-sm leading-relaxed">
          <li>
            <p className="font-medium text-foreground">UCSB grade distributions</p>
            <p className="mt-1 text-muted-foreground">
              Official grades through {gradeTerm}. These set average GPA and the grade-history charts.
            </p>
          </li>
          <li>
            <p className="font-medium text-foreground">RateMyProfessors</p>
            <p className="mt-1 text-muted-foreground">
              Quality, difficulty, would-take-again, and comments. Comments are scored with VADER sentiment and mapped onto tags.
            </p>
          </li>
          <li>
            <p className="font-medium text-foreground">UCSB Curriculums API</p>
            <p className="mt-1 text-muted-foreground">
              Section listings for who is teaching the current and next quarter.
            </p>
          </li>
        </ul>
      </section>

      <section className="mt-12">
        <h2 className="font-heading text-xl font-semibold tracking-tight">Matching</h2>
        <p className="mt-4 max-w-[62ch] text-sm leading-relaxed text-muted-foreground">
          UCSB grade files and RateMyProfessors use different name formats. We only
          publish a match at 85% confidence or higher. Truncated Nexus surnames can
          still match when every fragment is a prefix of the RateMyProfessors name.
        </p>
      </section>

      <section className="mt-12">
        <h2 className="font-heading text-xl font-semibold tracking-tight">Scoring</h2>
        <p className="mt-4 max-w-[62ch] text-sm leading-relaxed text-muted-foreground">
          GPA is scaled by 4.0. Quality is Bayesian-adjusted toward 3.0 when the
          sample is small, then scaled by 5. Difficulty is inverted so easier
          courses score higher. Sentiment maps VADER&apos;s −1…1 range onto 0…1.
          Enabled factors share the weight equally. You can change those weights
          on a course page.
        </p>
      </section>

      <p className="mt-14 text-sm">
        <Link to="/" className="text-primary hover:underline">
          Search a course
        </Link>
        {' '}to see the ranking.
      </p>
    </article>
  )
}
